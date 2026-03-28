from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Any
from urllib.parse import quote

import requests


logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    to_addrs: list[str],
    subject: str,
    body_html: str,
    body_text: str,
    use_tls: bool = True,
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = username
    message["To"] = ", ".join(to_addrs)
    message.attach(MIMEText(body_text, "plain", "utf-8"))
    message.attach(MIMEText(body_html, "html", "utf-8"))

    logger.info("Sending email notification to %s", to_addrs)
    with smtplib.SMTP(smtp_server, smtp_port, timeout=REQUEST_TIMEOUT) as smtp:
        if use_tls:
            smtp.starttls()
        if username or password:
            smtp.login(username, password)
        smtp.sendmail(username, to_addrs, message.as_string())


def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    logger.info("Sending Telegram notification to chat %s", chat_id)
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def send_bark(bark_url: str, title: str, body: str) -> None:
    base_url = bark_url.rstrip("/")
    url = f"{base_url}/{quote(title)}/{quote(body)}"

    logger.info("Sending Bark notification")
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def send_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    logger.info("Sending webhook notification to %s", webhook_url)
    response = requests.post(webhook_url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def send_dingtalk(webhook_url: str, title: str, text: str) -> None:
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text,
        },
    }

    logger.info("Sending DingTalk notification")
    response = requests.post(webhook_url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def send_feishu(webhook_url: str, title: str, text: str) -> None:
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                }
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": text,
                }
            ],
        },
    }

    logger.info("Sending Feishu notification")
    response = requests.post(webhook_url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def markdown_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_parts: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if _is_table_header(lines, index):
            html_parts.append(_render_table(lines, index))
            index = _table_end_index(lines, index)
            continue

        html_parts.append(f"<p>{escape(stripped)}</p>")
        index += 1

    return "\n".join(html_parts)


def _is_table_header(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False

    header = lines[index].strip()
    separator = lines[index + 1].strip()
    return "|" in header and _is_table_separator(separator)


def _is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False

    tokens = [segment.strip() for segment in line.strip("|").split("|")]
    return bool(tokens) and all(token and set(token) <= {"-", ":"} for token in tokens)


def _table_end_index(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines) and "|" in lines[index].strip():
        index += 1
    return index


def _split_markdown_row(line: str) -> list[str]:
    return [escape(cell.strip()) for cell in line.strip().strip("|").split("|")]


def _render_table(lines: list[str], start: int) -> str:
    rows: list[str] = ["<table>", "<thead>"]
    headers = _split_markdown_row(lines[start])
    rows.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in headers) + "</tr>")
    rows.extend(["</thead>", "<tbody>"])

    index = start + 2
    while index < len(lines):
        row_line = lines[index].strip()
        if not row_line or "|" not in row_line:
            break
        cells = _split_markdown_row(lines[index])
        rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        index += 1

    rows.extend(["</tbody>", "</table>"])
    return "\n".join(rows)


def dispatch(
    config: dict[str, Any],
    title: str,
    markdown_body: str,
    text_body: str,
) -> list[str]:
    errors: list[str] = []
    body_html = markdown_to_html(markdown_body)

    channels: list[tuple[str, Any]] = [
        ("telegram", lambda channel: send_telegram(channel["bot_token"], channel["chat_id"], markdown_body)),
        (
            "email",
            lambda channel: send_email(
                channel["smtp_server"],
                int(channel["smtp_port"]),
                channel["username"],
                channel["password"],
                list(channel["to_addrs"]),
                title,
                body_html,
                text_body,
                bool(channel.get("use_tls", True)),
            ),
        ),
        ("bark", lambda channel: send_bark(channel["bark_url"], title, text_body)),
        (
            "webhook",
            lambda channel: send_webhook(
                channel["webhook_url"],
                {"title": title, "markdown": markdown_body, "text": text_body},
            ),
        ),
        ("dingtalk", lambda channel: send_dingtalk(channel["webhook_url"], title, markdown_body)),
        ("feishu", lambda channel: send_feishu(channel["webhook_url"], title, markdown_body)),
    ]

    for channel_name, sender in channels:
        channel_config = config.get(channel_name, {})
        if not channel_config.get("enabled", False):
            continue

        try:
            sender(channel_config)
            logger.info("Notification sent via %s", channel_name)
        except Exception as exc:
            message = f"{channel_name}: {exc}"
            errors.append(message)
            logger.error("Notification failed via %s: %s", channel_name, exc)

    return errors
