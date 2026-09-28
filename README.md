# AI 每日观察

[![AI Daily](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml/badge.svg)](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml)

每天北京时间 **10:00**，自动收集 AI 官方资讯与开发工具更新，积累可追溯的阅读资料。

**[阅读最新日报](LATEST.md)** · **[浏览历史归档](ARCHIVE.md)** · **[查看运行记录](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml)**

## 收录内容

优先读取 **AI Radar 技能**使用的公开数据，每次最多 20 条雷达精选，提供中文标题、上游导读、来源分层及原文链接。参考讨论单列，官方 RSS 与工具更新作为补充。

- 数据入口：`https://news.learnprompt.pro/data/daily-brief.json`。
- 精选超过 48 小时未更新时降级到 `latest-24h.json`；该文件超过 36 小时则不当作今日资讯，明确记录不可用并使用 RSS。
- 主站网络异常时使用技能指定的 LearnPrompt/ai-news-radar 官方 GitHub 原始数据备用地址。
- 中文标题、导读和可选点评由上游提供，本仓库不调用大模型、不编造缺失字段。
- 实现依据：[AI Radar 技能来源项目](https://github.com/LearnPrompt/ai-news-radar)。`SKILL.md` 是给 AI 助手的操作说明；Actions 执行的是本仓库将其流程实现后的 Python 脚本。

- 官方资讯：OpenAI News、Google AI、Hugging Face Blog。
- 开发工具版本：OpenAI Codex、Claude Code、Ollama；按标题过滤 alpha、beta、rc 等预发布版本。
- 每条保留来源时间和原文链接，不复制文章全文；雷达导读明确标记为上游提供。
- 日报栏目使用中文；雷达条目优先中文标题，RSS 条目保留来源语言。无需大模型 API Key，也不调用收费 AI 服务。

## 运行方式

GitHub Actions 在 UTC 02:00（北京时间 10:00）触发；02:37 再检查一次，当天已有日报就直接跳过。
GitHub 定时调度可能延迟或漏跑，因此不保证严格准点或永不断档；也可以进入 Actions → AI Daily → Run workflow 手动执行。

抓取最近 48 小时的信息，并依据链接去除历史已收录条目。没有新内容也会如实保存当天的来源检查记录。
部分来源失败会明确标记；全部来源失败则任务报错、不提交，留待补跑。
每个日期最多生成一份日报，补跑不会覆盖已有日报及手写笔记。

日报归档在 `daily/YYYY/MM/YYYY-MM-DD.md`；`LATEST.md` 是最近一次生成的副本；`ARCHIVE.md` 提供历史索引。
可以在历史日报的「我的阅读笔记」中添加自己的理解。

## 修改信息源与本地运行

编辑 `sources.json` 即可添加或删除 RSS/Atom 源；无需安装第三方 Python 包，使用 Python 3.10+。

```sh
python3 -m unittest -v
python3 daily.py
```

## 提交与贡献记录

本仓库的日报提交由自动化生成，作者使用仓库所有者的 GitHub 隐私邮箱，提交到默认分支 `main`。
GitHub 贡献记录取决于邮箱关联、分支及仓库条件，显示可能有延迟；自动归档不代表手写代码或人工阅读。
参见 [GitHub 贡献统计规则](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)。

工作流只使用此仓库的内置 `GITHUB_TOKEN` 写入日报，不需要个人访问令牌。Fork 后默认不会以原作者身份运行；复用时请修改工作流的仓库条件及提交身份。
若公开仓库长时间无活动，GitHub 可能自动停用定时任务；届时在 Actions 页面重新启用。
