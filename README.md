# AI 每日观察

[![AI Daily](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml/badge.svg)](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml)

每天北京时间 **10:00**，从 **44 个直接信源**收集 AI 官方动态、国内外资讯、开发工具、研究论文、政策与融资信息，积累可追溯的阅读资料。

**[阅读最新日报](LATEST.md)** · **[浏览历史归档](ARCHIVE.md)** · **[查看运行记录](https://github.com/maximum2974/ai-daily/actions/workflows/daily.yml)**

## 收录内容

合并 **AI Radar 技能**使用的公开精选与完整时间线，不再截断到 20 条；同时独立采集官方、媒体、研究与工具信源。优先保留雷达提供的中文标题、上游导读、来源分层及原文链接，参考讨论单列。

- 数据入口：`https://news.learnprompt.pro/data/daily-brief.json`。
- 精选与 `latest-24h.json` 分别检查新鲜度（48 / 36 小时），合并可用数据；部分入口失败会明确标记覆盖可能不完整。
- 主站网络异常时使用技能指定的 LearnPrompt/ai-news-radar 官方 GitHub 原始数据备用地址。
- 中文标题、导读和可选点评由上游提供，本仓库不调用大模型、不编造缺失字段。
- 实现依据：[AI Radar 技能来源项目](https://github.com/LearnPrompt/ai-news-radar)。`SKILL.md` 是给 AI 助手的操作说明；Actions 执行的是本仓库将其流程实现后的 Python 脚本。

- 官方与技术博客：OpenAI、Google AI、DeepMind、Google Research、Microsoft Research、Hugging Face、NVIDIA Developer、AWS ML、GitHub AI。
- Anthropic 新闻、工程与研究，及 Mistral 新闻：使用社区维护的 RSS 转订，明确标记转订身份，条目链接指向官方原文。
- 国内动态：量子位、IT之家、InfoQ 中文，以及 DeepSeek、Qwen、智谱、豆包、Kimi、MiniMax 等关键词的新闻聚合。
- 海外媒体与深度阅读：TechCrunch、The Verge、WIRED、InfoQ、MIT、Simon Willison、Latent Space、Interconnects。
- 论文：arXiv `cs.AI`、`cs.CL`、`cs.CV`、`cs.LG`；完整收录符合时间范围的新链接到论文附件，主日报折叠预览前 25 篇，标记未经同行评审。
- 开发工具版本：Codex、Claude Code、Ollama、Gemini CLI、vLLM、SGLang、Transformers、Diffusers、LangGraph、Open WebUI、ComfyUI、Dify；过滤 alpha、beta、rc 等预发布版本。
- 政策、安全、融资与芯片：独立新闻聚合查询补充长尾信息，保留媒体名称与聚合入口，阅读时核对原文。
- 每条保留来源时间和原文链接，不复制文章全文；雷达导读明确标记为上游提供。
- 日报提供栏目导航与条数；雷达条目优先中文标题，RSS 条目保留来源语言，摘要仅截取来源提供的文字。无需大模型 API Key，也不调用收费 AI 服务。

完整清单、来源性质与已知覆盖限制见 **[信源说明](SOURCES.md)**。

## 运行方式

GitHub Actions 在 UTC 02:00（北京时间 10:00）触发；02:37 再检查一次，当天已有日报就直接跳过。
GitHub 定时调度可能延迟或漏跑，因此不保证严格准点或永不断档；也可以进入 Actions → AI Daily → Run workflow 手动执行。

抓取最近 48 小时的信息，并依据链接去除历史已收录条目；去除常见追踪参数与链接片段，但保留文章标识参数。综合媒体依据标题与分类标签过滤 AI 主题。没有新内容也会如实保存当天的来源检查记录。
部分来源失败会明确标记；全部来源失败则任务报错、不提交，留待补跑。
每个日期最多生成一份日报，补跑不会覆盖已有日报及手写笔记。

日报归档在 `daily/YYYY/MM/YYYY-MM-DD.md`；`LATEST.md` 是最近一次生成的副本；`ARCHIVE.md` 提供历史索引。
完整论文附件为同目录的 `YYYY-MM-DD.papers.md`；最新副本与历史日报分别使用对应的相对链接。
可以在历史日报的「我的阅读笔记」中添加自己的理解。

## 修改信息源与本地运行

编辑 `sources.json` 即可添加或删除 RSS/Atom 源；无需安装第三方 Python 包，使用 Python 3.10+。

```sh
python3 -m unittest -v
python3 daily.py --check-sources  # 仅联网检查，不写入日报；任一来源失败时退出码为 1
python3 daily.py
```

每个 RSS/Atom 源必须提供带时区的条目时间。支持 gzip 压缩和 RSS 的 `dc:date` 日期字段；单个响应解压后最大 8 MB。`ai_only: true` 对综合媒体启用 AI 主题过滤；`tier` / `tier_rank` 记录来源性质与排序。雷达源的 `max_items: null` 表示不限制每个数据文件的条数，`max_references` 限制每个文件的热议参考数量。

## 提交与贡献记录

本仓库的日报提交由自动化生成，作者使用仓库所有者的 GitHub 隐私邮箱，提交到默认分支 `main`。
GitHub 贡献记录取决于邮箱关联、分支及仓库条件，显示可能有延迟；自动归档不代表手写代码或人工阅读。
参见 [GitHub 贡献统计规则](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)。

工作流只使用此仓库的内置 `GITHUB_TOKEN` 写入日报，不需要个人访问令牌。Fork 后默认不会以原作者身份运行；复用时请修改工作流的仓库条件及提交身份。
若公开仓库长时间无活动，GitHub 可能自动停用定时任务；届时在 Actions 页面重新启用。
