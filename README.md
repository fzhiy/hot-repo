# Hot Repo

Daily GitHub Trending Top 10 scraper with multi-channel push notifications.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Daily Trending](https://github.com/fzhiy/hot-repo/actions/workflows/daily-trending.yml/badge.svg)](https://github.com/fzhiy/hot-repo/actions/workflows/daily-trending.yml)

[中文](README_CN.md) | **English**

## Features

- Scrapes GitHub Trending page daily (Top 10 by default)
- Filter by programming language and time range
- Multi-channel notifications: **Telegram**, **Email**, **Bark**, **DingTalk**, **Feishu**, **Webhook**
- Archives trending data as daily markdown files
- GitHub Actions cron for fully automated daily runs
- Config via YAML file or environment variables

## Quick Start

### Local

```bash
# Install dependencies
pip install -r requirements.txt

# Run (prints to stdout, saves to archives/)
python -m src.main

# Filter by language
python -m src.main -l python

# Top 20 weekly
python -m src.main -n 20 --since weekly
```

### GitHub Actions (Automated Daily)

1. Fork this repo
2. Add secrets in **Settings > Secrets and variables > Actions**:

| Secret | Channel |
|--------|---------|
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Telegram |
| `SMTP_SERVER` + `SMTP_USERNAME` + `SMTP_PASSWORD` + `EMAIL_TO` | Email |
| `BARK_URL` | Bark (iOS) |
| `DINGTALK_WEBHOOK` | DingTalk |
| `FEISHU_WEBHOOK` | Feishu/Lark |
| `WEBHOOK_URL` | Generic Webhook |

3. The workflow runs daily at **09:00 UTC (17:00 Beijing Time)**
4. Trigger manually: **Actions > Daily GitHub Trending > Run workflow**

## Configuration

### Option A: YAML file

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your credentials
python -m src.main -c config.yaml
```

### Option B: Environment variables

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python -m src.main
```

See `config.example.yaml` for all available options.

## CLI Options

```
python -m src.main [-h] [-c CONFIG] [-l LANGUAGE] [-n TOP_N]
                   [--since {daily,weekly,monthly}] [--no-notify]

Options:
  -c, --config    Path to config YAML file
  -l, --language  Filter by language (e.g. python, go, rust)
  -n, --top-n     Number of repos (default: 10)
  --since         Time range: daily, weekly, monthly
  --no-notify     Skip notifications, only print and archive
```

## Output Example

```
GitHub Trending Top 10 - 2026-03-28
Language: All Languages | Since: daily
==================================================

#1 owner/awesome-project
   12,345 stars | 500 stars today
   Language: Python
   An awesome project that does amazing things
   https://github.com/owner/awesome-project

#2 ...
```

Archives are saved to `archives/YYYY-MM-DD.md`.

## Project Structure

```
hot_repo/
├── .github/workflows/
│   └── daily-trending.yml        # GitHub Actions cron
├── src/
│   ├── scraper.py                # GitHub Trending page scraper
│   ├── notifier.py               # Multi-channel notification sender
│   └── main.py                   # Entry point and config loader
├── archives/                     # Daily trending markdown archives
├── config.example.yaml           # Config template
├── requirements.txt
└── README.md
```

## Notification Channels

| Channel | Config Key | How to Set Up |
|---------|-----------|---------------|
| Telegram | `telegram` | Create bot via [@BotFather](https://t.me/BotFather), get chat ID |
| Email | `email` | Use SMTP with app password (e.g. Gmail app password) |
| Bark | `bark` | Install [Bark app](https://apps.apple.com/app/bark/id1403753865), get push URL |
| DingTalk | `dingtalk` | Create robot in group, get webhook URL |
| Feishu | `feishu` | Create bot in group, get webhook URL |
| Webhook | `webhook` | Any endpoint accepting POST JSON |

## License

[MIT](LICENSE) -- fzhiy
