from __future__ import annotations

from email import message_from_string
from unittest.mock import MagicMock, patch

from src.notifier import dispatch, markdown_to_html


def test_dispatch_with_all_channels_disabled_returns_no_errors() -> None:
    config = {
        "telegram": {"enabled": False},
        "email": {"enabled": False},
        "bark": {"enabled": False},
        "webhook": {"enabled": False},
        "dingtalk": {"enabled": False},
        "feishu": {"enabled": False},
    }

    errors = dispatch(config, "Daily Report", "| A | B |", "plain text")

    assert errors == []


def test_normalize_notify_config_bridges_keys() -> None:
    from src.main import _normalize_notify_config

    config = {
        "email": {"enabled": True, "to": "a@b.com,c@d.com"},
        "bark": {"enabled": True, "url": "https://bark.example.com/key"},
    }
    normalized = _normalize_notify_config(config)

    assert normalized["email"]["to_addrs"] == ["a@b.com", "c@d.com"]
    assert normalized["bark"]["bark_url"] == "https://bark.example.com/key"


def test_normalize_notify_config_filters_empty_to() -> None:
    from src.main import _normalize_notify_config

    config = {"email": {"enabled": True, "to": ""}}
    normalized = _normalize_notify_config(config)

    assert normalized["email"]["to_addrs"] == []


@patch("src.notifier.requests.post")
def test_dispatch_with_telegram_enabled(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    config = {
        "telegram": {
            "enabled": True,
            "bot_token": "bot-token",
            "chat_id": "chat-123",
        }
    }

    errors = dispatch(config, "Daily Report", "*hello*", "hello")

    assert errors == []
    mock_post.assert_called_once_with(
        "https://api.telegram.org/botbot-token/sendMessage",
        json={
            "chat_id": "chat-123",
            "text": "*hello*",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )


@patch("src.notifier.smtplib.SMTP")
def test_dispatch_with_email_enabled(mock_smtp: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    config = {
        "email": {
            "enabled": True,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "user@example.com",
            "password": "secret",
            "to_addrs": ["to@example.com"],
            "use_tls": True,
        }
    }

    errors = dispatch(
        config,
        "Daily Report",
        "| name | stars |\n| --- | --- |\n| repo | 10 |",
        "repo: 10",
    )

    assert errors == []
    mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
    smtp_instance.starttls.assert_called_once_with()
    smtp_instance.login.assert_called_once_with("user@example.com", "secret")
    smtp_instance.sendmail.assert_called_once()
    sendmail_args = smtp_instance.sendmail.call_args.args
    assert sendmail_args[0] == "user@example.com"
    assert sendmail_args[1] == ["to@example.com"]
    assert "Subject: Daily Report" in sendmail_args[2]
    message = message_from_string(sendmail_args[2])
    html_part = message.get_payload()[1]
    assert html_part.get_content_type() == "text/html"
    assert "<table>" in html_part.get_payload(decode=True).decode("utf-8")


def test_dispatch_handles_exceptions_gracefully() -> None:
    config = {
        "telegram": {
            "enabled": True,
            "bot_token": "bot-token",
            "chat_id": "chat-123",
        },
        "webhook": {
            "enabled": True,
            "webhook_url": "https://example.com/hook",
        },
    }

    with (
        patch("src.notifier.send_telegram", side_effect=RuntimeError("telegram failed")),
        patch("src.notifier.send_webhook") as mock_webhook,
    ):
        errors = dispatch(config, "Daily Report", "markdown", "text")

    assert errors == ["telegram: telegram failed"]
    mock_webhook.assert_called_once_with(
        "https://example.com/hook",
        {"title": "Daily Report", "markdown": "markdown", "text": "text"},
    )


def test_markdown_to_html_renders_tables() -> None:
    html = markdown_to_html("| name | stars |\n| --- | --- |\n| repo | 10 |")

    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "<th>name</th>" in html
    assert "<td>repo</td>" in html
