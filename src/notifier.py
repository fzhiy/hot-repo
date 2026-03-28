"""Send notifications via multiple channels."""

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

logger = logging.getLogger(__name__)


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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        if use_tls:
            server.starttls()
        server.login(username, password)
        server.sendmail(username, to_addrs, msg.as_string())
    logger.info("Email sent to %s", to_addrs)


def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    logger.info("Telegram message sent to chat %s", chat_id)


def send_bark(bark_url: str, title: str, body: str) -> None:
    """Send push notification via Bark (iOS)."""
    url = f"{bark_url.rstrip('/')}/{title}/{body}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    logger.info("Bark notification sent")


def send_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()
    logger.info("Webhook notification sent to %s", webhook_url)


def send_dingtalk(webhook_url: str, title: str, text: str) -> None:
    """Send notification via DingTalk robot webhook."""
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text},
    }
    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()
    logger.info("DingTalk notification sent")


def send_feishu(webhook_url: str, title: str, text: str) -> None:
    """Send notification via Feishu/Lark robot webhook."""
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}},
            "elements": [{"tag": "markdown", "content": text}],
        },
    }
    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()
    logger.info("Feishu notification sent")


def markdown_to_html(md_text: str) -> str:
    """Convert markdown table to simple HTML for email."""
    lines = md_text.split("\n")
    html_parts = ['<div style="font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto;">']

    for line in lines:
        if line.startswith("# "):
            html_parts.append(f'<h2 style="color: #24292e;">{line[2:]}</h2>')
        elif line.startswith("> "):
            html_parts.append(f'<blockquote style="color: #6a737d; border-left: 3px solid #dfe2e5; padding-left: 12px;">{line[2:]}</blockquote>')
        elif line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            row = "".join(f"<td style='padding: 6px 12px; border: 1px solid #dfe2e5;'>{c}</td>" for c in cells)
            html_parts.append(f"<tr>{row}</tr>")
        elif line.startswith("|") and "---" in line:
            continue

    html = "\n".join(html_parts)
    # Wrap table rows
    html = html.replace("<tr>", "<table style='border-collapse: collapse; width: 100%;'><tr>", 1)
    html += "</table></div>"
    return html


def dispatch(config: dict, title: str, markdown_body: str, text_body: str) -> list[str]:
    """Dispatch notifications to all configured channels.

    Returns list of errors (empty if all succeeded).
    """
    errors = []

    # Email
    email_cfg = config.get("email")
    if email_cfg and email_cfg.get("enabled"):
        try:
            send_email(
                smtp_server=email_cfg["smtp_server"],
                smtp_port=email_cfg.get("smtp_port", 587),
                username=email_cfg["username"],
                password=email_cfg["password"],
                to_addrs=email_cfg["to"],
                subject=title,
                body_html=markdown_to_html(markdown_body),
                body_text=text_body,
                use_tls=email_cfg.get("use_tls", True),
            )
        except Exception as e:
            errors.append(f"email: {e}")
            logger.error("Email failed: %s", e)

    # Telegram
    tg_cfg = config.get("telegram")
    if tg_cfg and tg_cfg.get("enabled"):
        try:
            send_telegram(tg_cfg["bot_token"], tg_cfg["chat_id"], text_body)
        except Exception as e:
            errors.append(f"telegram: {e}")
            logger.error("Telegram failed: %s", e)

    # Bark
    bark_cfg = config.get("bark")
    if bark_cfg and bark_cfg.get("enabled"):
        try:
            send_bark(bark_cfg["url"], title, text_body[:200])
        except Exception as e:
            errors.append(f"bark: {e}")
            logger.error("Bark failed: %s", e)

    # DingTalk
    ding_cfg = config.get("dingtalk")
    if ding_cfg and ding_cfg.get("enabled"):
        try:
            send_dingtalk(ding_cfg["webhook_url"], title, markdown_body)
        except Exception as e:
            errors.append(f"dingtalk: {e}")
            logger.error("DingTalk failed: %s", e)

    # Feishu
    feishu_cfg = config.get("feishu")
    if feishu_cfg and feishu_cfg.get("enabled"):
        try:
            send_feishu(feishu_cfg["webhook_url"], title, markdown_body)
        except Exception as e:
            errors.append(f"feishu: {e}")
            logger.error("Feishu failed: %s", e)

    # Generic Webhook
    webhook_cfg = config.get("webhook")
    if webhook_cfg and webhook_cfg.get("enabled"):
        try:
            send_webhook(webhook_cfg["url"], {"title": title, "body": markdown_body})
        except Exception as e:
            errors.append(f"webhook: {e}")
            logger.error("Webhook failed: %s", e)

    return errors
