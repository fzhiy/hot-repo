"""GitHub Trending Top 10 daily scraper and notifier."""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .scraper import fetch_trending, format_markdown, format_text
from .notifier import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVES_DIR = PROJECT_ROOT / "archives"


def load_config(path: str | None = None) -> dict:
    """Load config from YAML file or environment variables."""
    if path and Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}

    # Fall back to environment variables
    config = {
        "language": os.getenv("TRENDING_LANGUAGE", ""),
        "since": os.getenv("TRENDING_SINCE", "daily"),
        "top_n": int(os.getenv("TRENDING_TOP_N", "10")),
    }

    # Telegram from env
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        config["telegram"] = {
            "enabled": True,
            "bot_token": tg_token,
            "chat_id": tg_chat,
        }

    # Email from env
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USERNAME")
    if smtp_server and smtp_user:
        config["email"] = {
            "enabled": True,
            "smtp_server": smtp_server,
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": smtp_user,
            "password": os.getenv("SMTP_PASSWORD", ""),
            "to": os.getenv("EMAIL_TO", smtp_user).split(","),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }

    # Bark from env
    bark_url = os.getenv("BARK_URL")
    if bark_url:
        config["bark"] = {"enabled": True, "url": bark_url}

    # DingTalk from env
    ding_url = os.getenv("DINGTALK_WEBHOOK")
    if ding_url:
        config["dingtalk"] = {"enabled": True, "webhook_url": ding_url}

    # Feishu from env
    feishu_url = os.getenv("FEISHU_WEBHOOK")
    if feishu_url:
        config["feishu"] = {"enabled": True, "webhook_url": feishu_url}

    # Generic webhook from env
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        config["webhook"] = {"enabled": True, "url": webhook_url}

    return config


def save_archive(markdown: str, date_str: str) -> Path:
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
    filepath = ARCHIVES_DIR / f"{date_str}.md"
    filepath.write_text(markdown, encoding="utf-8")
    logger.info("Archive saved: %s", filepath)
    return filepath


def run(config: dict) -> None:
    language = config.get("language", "")
    since = config.get("since", "daily")
    top_n = config.get("top_n", 10)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Fetching GitHub trending (language=%s, since=%s, top=%d)", language or "all", since, top_n)

    repos = fetch_trending(language=language, since=since, top_n=top_n)
    if not repos:
        logger.warning("No trending repos found")
        return

    logger.info("Found %d trending repos", len(repos))

    md = format_markdown(repos, date_str, language)
    text = format_text(repos, date_str, language)

    # Save archive
    save_archive(md, date_str)

    # Print to stdout
    print(text)

    # Send notifications
    title = f"GitHub Trending Top {len(repos)} - {date_str}"
    errors = dispatch(config, title, md, text)
    if errors:
        logger.warning("Some notifications failed: %s", errors)
    else:
        logger.info("All notifications sent successfully")


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending Top 10 Daily Notifier")
    parser.add_argument("-c", "--config", help="Path to config YAML file")
    parser.add_argument("-l", "--language", help="Filter by language (e.g. python)")
    parser.add_argument("-n", "--top-n", type=int, help="Number of repos (default: 10)")
    parser.add_argument("--since", choices=["daily", "weekly", "monthly"], help="Time range")
    parser.add_argument("--no-notify", action="store_true", help="Skip notifications, only print and archive")
    args = parser.parse_args()

    config = load_config(args.config)

    # CLI overrides
    if args.language is not None:
        config["language"] = args.language
    if args.top_n is not None:
        config["top_n"] = args.top_n
    if args.since is not None:
        config["since"] = args.since
    if args.no_notify:
        # Disable all notification channels
        for key in ("email", "telegram", "bark", "dingtalk", "feishu", "webhook"):
            if key in config:
                config[key]["enabled"] = False

    run(config)


if __name__ == "__main__":
    main()
