# Task Plan: hot-repo-v1

## Goal
构建 GitHub Trending Top 10 每日抓取和多渠道推送工具。

## Current Phase
- dispatching

## Plan Overview
将项目拆分为 3 个独立并行的工作单元：scraper 模块、notifier 模块、基础设施（CI + 文档 + 配置）。scraper 和 notifier 无依赖关系可完全并行。main.py 入口文件整合两个模块，由 Planner 在 Worker 完成后集成。

## Scope
- In: 抓取、通知、CLI、CI、文档、测试
- Out: Web UI、数据库、分析可视化

## Action Items
- [ ] 1. Create src/scraper.py: fetch_trending(), format_markdown(), format_text()
- [ ] 2. Create src/notifier.py: 6 个渠道发送函数 + dispatch() 统一分发
- [ ] 3. Create src/main.py: CLI 入口，配置加载（YAML + env），编排 scraper + notifier
- [ ] 4. Create tests/test_scraper.py: 用离线 HTML fixture 测试解析逻辑
- [ ] 5. Create tests/test_notifier.py: mock 外部 API 测试通知分发
- [ ] 6. Create .github/workflows/daily-trending.yml: cron 定时 + 手动触发 + 归档 commit
- [ ] 7. Create config.example.yaml: 全部配置项模板
- [ ] 8. Create .gitignore, LICENSE, requirements.txt: 项目基础文件
- [ ] 9. Create README.md (英文) + README_CN.md (中文): 双语文档
- [ ] 10. Integration test: 端到端运行验证

## Dependencies
- Items 1, 2 无依赖，可并行
- Item 3 依赖 Items 1, 2
- Items 4, 5 分别依赖 Items 1, 2
- Items 6, 7, 8, 9 无依赖，可与 1, 2 并行
- Item 10 依赖所有 Items 完成

## Parallelization
- **Worker 1**: Items 1, 4 (scraper + tests)
- **Worker 2**: Items 2, 5 (notifier + tests)
- **Worker 3**: Items 3, 6, 7, 8, 9 (main entry + CI + config + docs)
- **Planner**: Item 10 (integration verification)

## Validation Strategy
- [ ] pytest tests/ 全部通过
- [ ] python -m src.main --no-notify 成功输出
- [ ] archives/ 生成 .md 归档
- [ ] grep -r '/home/' 无硬编码路径

## Risks
- GitHub Trending HTML 结构变动 → 定期维护 CSS selector
- GitHub 限流 → User-Agent header + 合理超时

## Phases
- [x] Discovery
- [x] Design
- [ ] Implementation
- [ ] Verification
- [ ] Delivery
