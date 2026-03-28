# hot-repo

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

这是一个基于 Python 3.12 的轻量项目，用于每日抓取 GitHub Trending、归档结果，并通过多种渠道发送通知。

## 功能特性

- 抓取 `daily`、`weekly` 或 `monthly` 的 GitHub Trending 仓库列表。
- 支持按编程语言筛选，并限制返回数量。
- 每次运行都会归档到 `archives/YYYY-MM-DD.md`。
- 支持 Telegram、Email、Bark、DingTalk、Feishu 和通用 Webhook 通知。
- 既可以通过本地 CLI 运行，也可以通过 GitHub Actions 按日定时执行。

## 快速开始

### 本地运行

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.main -c config.yaml --no-notify
```

### GitHub Actions

1. 如果需要覆盖默认抓取参数，请在仓库中配置 `TRENDING_LANGUAGE`、`TRENDING_SINCE` 和 `TRENDING_TOP_N` 这几个 repository variables。
2. 为需要启用的通知渠道配置 repository secrets，例如 `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`、`SMTP_SERVER`、`SMTP_PASSWORD` 或 `WEBHOOK_URL`。
3. 可以通过 `workflow_dispatch` 手动触发 `Daily Trending` workflow，或者等待每天 `09:00 UTC` 的定时运行。

## CLI

```bash
python -m src.main [options]
```

| 选项 | 说明 |
| --- | --- |
| `-c, --config` | 从 YAML 文件加载配置。 |
| `-l, --language` | 覆盖当前配置中的编程语言筛选。 |
| `-n, --top-n` | 覆盖当前配置中的抓取数量。 |
| `--since` | 覆盖 Trending 时间范围，可选 `daily`、`weekly`、`monthly`。 |
| `--no-notify` | 本次运行跳过所有通知渠道。 |

## 配置说明

当提供 `--config` 时，`src.main` 会优先从 YAML 文件读取配置；否则会从以下环境变量读取：

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

`config.example.yaml` 对所有支持的配置项都做了示例说明。

## 项目结构

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

## 通知渠道

| 渠道 | 配置项 | 说明 |
| --- | --- | --- |
| Telegram | `telegram.enabled`, `telegram.bot_token`, `telegram.chat_id` | 适合直接推送到聊天窗口。 |
| Email | `email.enabled`, `email.smtp_server`, `email.smtp_port`, `email.username`, `email.password`, `email.to`, `email.use_tls` | 基于 SMTP 发送。 |
| Bark | `bark.enabled`, `bark.url` | 适合 Bark 客户端推送。 |
| DingTalk | `dingtalk.enabled`, `dingtalk.webhook_url` | 使用自定义机器人 Webhook。 |
| Feishu | `feishu.enabled`, `feishu.webhook_url` | 使用自定义机器人 Webhook。 |
| Webhook | `webhook.enabled`, `webhook.url` | 适合通用 HTTP 集成。 |

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
