# Spec: hot-repo — GitHub Trending Top 10 每日推送

## Goal
自动抓取 GitHub Trending Top 10 仓库，通过多渠道推送通知，并归档历史数据。

## Background
开发者需要每天了解 GitHub 上的热门项目，但手动查看 Trending 页面低效。本项目自动化这一流程，支持定时抓取和主动推送。同时作为 multi-agent-dev-framework 的首个实践项目。

## Requirements

### Functional
1. 抓取 https://github.com/trending 页面，解析 Top N 仓库信息（名称、描述、语言、星数、今日新增）
2. 支持按编程语言筛选（python, go, rust, etc.）
3. 支持时间范围选择（daily, weekly, monthly）
4. 支持多渠道推送通知：Telegram, Email, Bark, 钉钉, 飞书, 通用 Webhook
5. 每日归档抓取结果为 Markdown 文件
6. GitHub Actions 定时任务自动运行
7. 支持手动触发运行
8. 支持命令行参数覆盖配置

### Non-Functional
- 抓取超时不超过 30 秒
- 通知发送失败不应阻塞其他渠道
- 配置支持 YAML 文件和环境变量两种方式
- 不依赖非标准库以外的重型框架

## Scope

### In Scope
- GitHub Trending 页面抓取和解析
- 6 个推送渠道的通知发送
- GitHub Actions CI/CD 定时运行
- 每日 Markdown 归档
- 命令行工具
- 双语文档（README.md 英文 + README_CN.md 中文）

### Out of Scope
- Web UI / Dashboard
- 用户登录和认证
- 数据库存储
- Trending 数据分析和可视化
- 多语言同时抓取

## Technical Decisions
- Language: Python 3.12
- Dependencies: requests, beautifulsoup4, pyyaml
- Target environment: GitHub Actions (ubuntu-latest) + 本地运行
- 配置格式: YAML
- 归档格式: Markdown

## Acceptance Criteria
- [ ] `python -m src.main --no-notify` 成功抓取并打印 Top 10
- [ ] `python -m src.main -l python` 按语言筛选正常工作
- [ ] archives/ 目录下生成当日 Markdown 归档文件
- [ ] 配置 Telegram 凭据后推送成功
- [ ] GitHub Actions workflow 可手动触发运行
- [ ] README.md (英文) 和 README_CN.md (中文) 完整可读
- [ ] 所有代码无硬编码路径或凭据

## File Structure (Proposed)
```
hot_repo/
├── .github/workflows/
│   └── daily-trending.yml
├── src/
│   ├── __init__.py
│   ├── scraper.py
│   ├── notifier.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_notifier.py
├── archives/
├── config.example.yaml
├── requirements.txt
├── .gitignore
├── LICENSE
├── README.md
└── README_CN.md
```

## Open Questions
- 无（需求已明确）
