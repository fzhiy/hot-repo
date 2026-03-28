from __future__ import annotations

import argparse
import inspect
import logging
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .notifier import dispatch
from .scraper import fetch_trending, format_markdown, format_text

LOGGER = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG: dict[str, Any] = {
    "language": "",
    "since": "daily",
    "top_n": 10,
    "telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": "",
    },
    "email": {
        "enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "to": "",
        "use_tls": True,
    },
    "bark": {
        "enabled": False,
        "url": "",
    },
    "dingtalk": {
        "enabled": False,
        "webhook_url": "",
    },
    "feishu": {
        "enabled": False,
        "webhook_url": "",
    },
    "webhook": {
        "enabled": False,
        "url": "",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _load_yaml_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    config_path = Path(path).expanduser()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Configuration file must contain a YAML mapping: {config_path}")
    return _deep_merge(DEFAULT_CONFIG, payload)


def _load_env_config() -> dict[str, Any]:
    language = os.getenv("TRENDING_LANGUAGE", DEFAULT_CONFIG["language"])
    since = os.getenv("TRENDING_SINCE", DEFAULT_CONFIG["since"])
    top_n = int(os.getenv("TRENDING_TOP_N", str(DEFAULT_CONFIG["top_n"])))

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = int(os.getenv("SMTP_PORT", str(DEFAULT_CONFIG["email"]["smtp_port"])))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    email_to = os.getenv("EMAIL_TO", "")
    smtp_use_tls = _parse_bool(
        os.getenv("SMTP_USE_TLS"),
        default=DEFAULT_CONFIG["email"]["use_tls"],
    )

    bark_url = os.getenv("BARK_URL", "")
    dingtalk_webhook = os.getenv("DINGTALK_WEBHOOK", "")
    feishu_webhook = os.getenv("FEISHU_WEBHOOK", "")
    webhook_url = os.getenv("WEBHOOK_URL", "")

    return {
        "language": language,
        "since": since,
        "top_n": top_n,
        "telegram": {
            "enabled": bool(telegram_bot_token and telegram_chat_id),
            "bot_token": telegram_bot_token,
            "chat_id": telegram_chat_id,
        },
        "email": {
            "enabled": bool(smtp_server and email_to),
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": smtp_username,
            "password": smtp_password,
            "to": email_to,
            "use_tls": smtp_use_tls,
        },
        "bark": {
            "enabled": bool(bark_url),
            "url": bark_url,
        },
        "dingtalk": {
            "enabled": bool(dingtalk_webhook),
            "webhook_url": dingtalk_webhook,
        },
        "feishu": {
            "enabled": bool(feishu_webhook),
            "webhook_url": feishu_webhook,
        },
        "webhook": {
            "enabled": bool(webhook_url),
            "url": webhook_url,
        },
    }


def _invoke_compatible(func: Any, **candidates: Any) -> Any:
    signature = inspect.signature(func)
    parameters = signature.parameters

    if any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    ):
        return func(**candidates)

    accepted = {
        key: value
        for key, value in candidates.items()
        if key in parameters
    }
    return func(**accepted)


def _notification_title(config: dict[str, Any], generated_at: datetime) -> str:
    parts = [f"GitHub Trending {generated_at.date().isoformat()}", config["since"]]
    if config.get("language"):
        parts.append(str(config["language"]))
    return " | ".join(parts)


def _notifications_enabled(config: dict[str, Any]) -> bool:
    for channel in ("telegram", "email", "bark", "dingtalk", "feishu", "webhook"):
        if config.get(channel, {}).get("enabled"):
            return True
    return False


def load_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    if path:
        return _load_yaml_config(path)
    return _load_env_config()


def save_archive(markdown: str, date_str: str) -> Path:
    archive_dir = REPO_ROOT / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{date_str}.md"
    archive_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    LOGGER.info("Archived markdown to %s", archive_path)
    return archive_path


def run(config: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc)

    repositories = _invoke_compatible(
        fetch_trending,
        language=config.get("language"),
        since=config.get("since"),
        top_n=config.get("top_n"),
    )
    markdown = _invoke_compatible(
        format_markdown,
        repositories=repositories,
        repos=repositories,
        items=repositories,
        language=config.get("language"),
        since=config.get("since"),
        top_n=config.get("top_n"),
        generated_at=generated_at,
    )
    text = _invoke_compatible(
        format_text,
        repositories=repositories,
        repos=repositories,
        items=repositories,
        language=config.get("language"),
        since=config.get("since"),
        top_n=config.get("top_n"),
        generated_at=generated_at,
    )

    archive_path = save_archive(markdown, generated_at.date().isoformat())
    print(text)

    if config.get("_notify", True) and _notifications_enabled(config):
        _invoke_compatible(
            dispatch,
            config=config,
            markdown=markdown,
            text=text,
            message=text,
            body=markdown,
            title=_notification_title(config, generated_at),
        )
        LOGGER.info("Notifications dispatched.")
    else:
        LOGGER.info("Notifications skipped.")

    return {
        "repositories": repositories,
        "markdown": markdown,
        "text": text,
        "archive_path": archive_path,
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Fetch, archive, and optionally notify GitHub Trending results.",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a YAML configuration file.",
    )
    parser.add_argument(
        "-l",
        "--language",
        help="Filter the GitHub Trending page by programming language.",
    )
    parser.add_argument(
        "-n",
        "--top-n",
        type=int,
        help="Number of repositories to fetch.",
    )
    parser.add_argument(
        "--since",
        choices=("daily", "weekly", "monthly"),
        help="Trending time window.",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Skip all notification channels for this run.",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.language is not None:
        config["language"] = args.language
    if args.top_n is not None:
        if args.top_n <= 0:
            raise ValueError("--top-n must be greater than 0")
        config["top_n"] = args.top_n
    if args.since is not None:
        config["since"] = args.since
    if args.no_notify:
        config["_notify"] = False

    run(config)


if __name__ == "__main__":
    main()
