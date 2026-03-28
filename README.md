# hot-repo

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Daily GitHub Trending scraping, archiving, and multi-channel notifications in a small Python 3.12 project.

## Features

- Fetch the top GitHub Trending repositories for `daily`, `weekly`, or `monthly`.
- Filter by programming language and limit the number of results.
- Archive each run to `archives/YYYY-MM-DD.md`.
- Send notifications through Telegram, Email, Bark, DingTalk, Feishu, or a generic webhook.
- Run locally from a CLI or on a daily GitHub Actions schedule.

## Quick Start

### Local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.main -c config.yaml --no-notify
```

### GitHub Actions

1. Add repository variables for `TRENDING_LANGUAGE`, `TRENDING_SINCE`, and `TRENDING_TOP_N` if you want to override the defaults.
2. Add repository secrets for any notification channel you want to enable, such as `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_SERVER`, `SMTP_PASSWORD`, or `WEBHOOK_URL`.
3. Run the `Daily Trending` workflow manually from `workflow_dispatch`, or wait for the daily schedule at `09:00 UTC`.

## CLI

```bash
python -m src.main [options]
```

| Option | Description |
| --- | --- |
| `-c, --config` | Load settings from a YAML file. |
| `-l, --language` | Override the configured trending language. |
| `-n, --top-n` | Override how many repositories to fetch. |
| `--since` | Override the trending window: `daily`, `weekly`, or `monthly`. |
| `--no-notify` | Skip all notification channels for the current run. |

## Configuration

`src.main` loads configuration from a YAML file when `--config` is provided. Otherwise it reads these environment variables:

- `TRENDING_LANGUAGE`
- `TRENDING_SINCE`
- `TRENDING_TOP_N`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_TO`
- `SMTP_USE_TLS`
- `BARK_URL`
- `DINGTALK_WEBHOOK`
- `FEISHU_WEBHOOK`
- `WEBHOOK_URL`

The example configuration file documents every supported option.

## Project Structure

```text
.
├── .github/workflows/daily-trending.yml
├── archives/
├── config.example.yaml
├── LICENSE
├── README.md
├── README_CN.md
├── requirements.txt
└── src/
    ├── __init__.py
    ├── main.py
    ├── notifier.py
    └── scraper.py
```

## Notification Channels

| Channel | Config keys | Notes |
| --- | --- | --- |
| Telegram | `telegram.enabled`, `telegram.bot_token`, `telegram.chat_id` | Best for direct chat delivery. |
| Email | `email.enabled`, `email.smtp_server`, `email.smtp_port`, `email.username`, `email.password`, `email.to`, `email.use_tls` | SMTP-based delivery. |
| Bark | `bark.enabled`, `bark.url` | Push notifications for Bark clients. |
| DingTalk | `dingtalk.enabled`, `dingtalk.webhook_url` | Uses a custom robot webhook. |
| Feishu | `feishu.enabled`, `feishu.webhook_url` | Uses a custom bot webhook. |
| Webhook | `webhook.enabled`, `webhook.url` | Generic HTTP integration. |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
