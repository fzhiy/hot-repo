# Hot Repo

GitHub Trending Top 10 每日定时抓取 + 多渠道推送通知。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Daily Trending](https://github.com/fzhiy/hot-repo/actions/workflows/daily-trending.yml/badge.svg)](https://github.com/fzhiy/hot-repo/actions/workflows/daily-trending.yml)

**中文** | [English](README.md)

## 功能

- 每天自动抓取 GitHub Trending 页面（默认 Top 10）
- 支持按编程语言和时间范围筛选
- 多渠道推送：**Telegram**、**Email**、**Bark**、**钉钉**、**飞书**、**Webhook**
- 每日趋势数据归档为 Markdown 文件
- GitHub Actions 定时任务，全自动运行
- 支持 YAML 配置文件或环境变量

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（输出到终端，同时保存到 archives/）
python -m src.main

# 按语言筛选
python -m src.main -l python

# Top 20 周榜
python -m src.main -n 20 --since weekly
```

### GitHub Actions（每日自动运行）

1. Fork 本仓库
2. 在 **Settings > Secrets and variables > Actions** 中添加密钥：

| Secret | 推送渠道 |
|--------|---------|
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Telegram |
| `SMTP_SERVER` + `SMTP_USERNAME` + `SMTP_PASSWORD` + `EMAIL_TO` | 邮件 |
| `BARK_URL` | Bark (iOS) |
| `DINGTALK_WEBHOOK` | 钉钉 |
| `FEISHU_WEBHOOK` | 飞书 |
| `WEBHOOK_URL` | 通用 Webhook |

3. 工作流每天 **UTC 09:00（北京时间 17:00）** 自动运行
4. 手动触发：**Actions > Daily GitHub Trending > Run workflow**

## 配置方式

### 方式 A：YAML 配置文件

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的凭据
python -m src.main -c config.yaml
```

### 方式 B：环境变量

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python -m src.main
```

完整配置选项参考 `config.example.yaml`。

## 命令行参数

```
python -m src.main [-h] [-c CONFIG] [-l LANGUAGE] [-n TOP_N]
                   [--since {daily,weekly,monthly}] [--no-notify]

参数：
  -c, --config    配置文件路径（YAML）
  -l, --language  按语言筛选（如 python, go, rust）
  -n, --top-n     获取数量（默认 10）
  --since         时间范围：daily（日）、weekly（周）、monthly（月）
  --no-notify     跳过推送，仅输出到终端和归档
```

## 输出示例

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

归档文件保存在 `archives/YYYY-MM-DD.md`。

## 项目结构

```
hot_repo/
├── .github/workflows/
│   └── daily-trending.yml        # GitHub Actions 定时任务
├── src/
│   ├── scraper.py                # GitHub Trending 页面抓取
│   ├── notifier.py               # 多渠道通知发送
│   └── main.py                   # 入口和配置加载
├── archives/                     # 每日趋势 Markdown 归档
├── config.example.yaml           # 配置模板
├── requirements.txt
└── README.md
```

## 推送渠道

| 渠道 | 配置键 | 设置方法 |
|------|--------|---------|
| Telegram | `telegram` | 通过 [@BotFather](https://t.me/BotFather) 创建机器人，获取 chat ID |
| 邮件 | `email` | 使用 SMTP + 应用专用密码（如 Gmail 应用密码） |
| Bark | `bark` | 安装 [Bark App](https://apps.apple.com/app/bark/id1403753865)，获取推送 URL |
| 钉钉 | `dingtalk` | 在群组中创建自定义机器人，获取 Webhook URL |
| 飞书 | `feishu` | 在群组中创建机器人，获取 Webhook URL |
| Webhook | `webhook` | 任何接受 POST JSON 的端点 |

## 许可证

[MIT](LICENSE) -- fzhiy
