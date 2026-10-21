# 信源说明

直接配置 **44 个信源**，雷达与新闻聚合的上游来源不计入该数量。RSS 地址与社区转订均为公开入口，无需新增密钥。

## 覆盖与阅读方式

- 官方博客侧重模型、产品、技术与应用案例；媒体补充行业事件与国内报道；个人通讯提供深度分析。
- Anthropic 与 Mistral 的条目来自社区维护的转订，不把转订地址称为官方 RSS。
- Google News 是新闻聚合入口，保留条目提供的媒体名称；链接可能先打开聚合页。
- 论文附件保留全部符合时间范围的新链接，跨分类重复链接仅出现一次；主日报提供前 25 篇折叠预览及完整清单入口。
- 相同链接的雷达导读优先保留。不同媒体报道同一事件仍可能分别出现，当前不做语义去重。

## 信源清单

| 来源 | 栏目 | 性质 | AI 主题过滤 |
| --- | --- | --- | --- |
| [AI News Radar](https://news.learnprompt.pro/data) | 雷达精选 | 上游分层聚合 | 专门主题源 |
| [OpenAI News](https://openai.com/news/rss.xml) | 官方资讯 | 官方一手源 | 专门主题源 |
| [Google AI](https://blog.google/technology/ai/rss/) | 官方资讯 | 官方一手源 | 专门主题源 |
| [Hugging Face Blog](https://huggingface.co/blog/feed.xml) | 官方资讯 | 官方一手源 | 专门主题源 |
| [OpenAI Codex](https://github.com/openai/codex/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Claude Code](https://github.com/anthropics/claude-code/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Ollama](https://github.com/ollama/ollama/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [DeepMind](https://deepmind.google/blog/rss.xml) | 官方资讯 | 官方一手源 | 专门主题源 |
| [Google Research](https://research.google/blog/rss/) | 论文与技术 | 官方一手源 | 专门主题源 |
| [Microsoft Research](https://www.microsoft.com/en-us/research/feed/) | 论文与技术 | 官方一手源 | 专门主题源 |
| [NVIDIA Developer](https://developer.nvidia.com/blog/feed/) | 融资与算力 | 官方一手源 | 标题与分类标签 |
| [AWS ML](https://aws.amazon.com/blogs/machine-learning/feed/) | 产品与工具 | 官方一手源 | 专门主题源 |
| [GitHub AI](https://github.blog/ai-and-ml/feed/) | 产品与工具 | 官方一手源 | 专门主题源 |
| [Anthropic News（社区转订）](https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml) | 官方资讯 | 社区维护转订（链接指向官方原文） | 专门主题源 |
| [Anthropic Engineering（社区转订）](https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml) | 论文与技术 | 社区维护转订（链接指向官方原文） | 专门主题源 |
| [Anthropic Research（社区转订）](https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml) | 论文与技术 | 社区维护转订（链接指向官方原文） | 专门主题源 |
| [Mistral News（社区转订）](https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_mistral.xml) | 官方资讯 | 社区维护转订（链接指向官方原文） | 专门主题源 |
| [量子位](https://www.qbitai.com/feed) | 国内动态 | 媒体报道 | 专门主题源 |
| [IT之家 · AI](https://www.ithome.com/rss/) | 国内动态 | 媒体报道 | 标题与分类标签 |
| [InfoQ 中文 · AI](https://www.infoq.cn/feed) | 国内动态 | 媒体报道 | 标题与分类标签 |
| [TechCrunch AI](https://techcrunch.com/category/artificial-intelligence/feed/) | 行业与综合 | 媒体报道 | 专门主题源 |
| [The Verge AI](https://www.theverge.com/rss/ai-artificial-intelligence/index.xml) | 行业与综合 | 媒体报道 | 专门主题源 |
| [WIRED AI](https://www.wired.com/feed/tag/ai/latest/rss) | 行业与综合 | 媒体报道 | 专门主题源 |
| [InfoQ AI](https://feed.infoq.com/ai-ml-data-eng/) | 行业与综合 | 媒体报道 | 专门主题源 |
| [Simon Willison](https://simonwillison.net/atom/everything/) | 深度阅读 | 个人或社区分析 | 标题与分类标签 |
| [Latent Space](https://www.latent.space/feed) | 深度阅读 | 个人或社区分析 | 专门主题源 |
| [Interconnects](https://www.interconnects.ai/feed) | 深度阅读 | 个人或社区分析 | 专门主题源 |
| [MIT AI](https://news.mit.edu/rss/topic/artificial-intelligence2) | 论文与技术 | 高校研究动态 | 专门主题源 |
| [arXiv AI](https://rss.arxiv.org/rss/cs.AI) | 论文预印本 | 研究预印本（未经同行评审） | 专门主题源 |
| [arXiv CL](https://rss.arxiv.org/rss/cs.CL) | 论文预印本 | 研究预印本（未经同行评审） | 专门主题源 |
| [arXiv CV](https://rss.arxiv.org/rss/cs.CV) | 论文预印本 | 研究预印本（未经同行评审） | 专门主题源 |
| [arXiv ML](https://rss.arxiv.org/rss/cs.LG) | 论文预印本 | 研究预印本（未经同行评审） | 专门主题源 |
| [vLLM](https://github.com/vllm-project/vllm/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [SGLang](https://github.com/sgl-project/sglang/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Transformers](https://github.com/huggingface/transformers/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Diffusers](https://github.com/huggingface/diffusers/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [LangGraph](https://github.com/langchain-ai/langgraph/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Open WebUI](https://github.com/open-webui/open-webui/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [Dify](https://github.com/langgenius/dify/releases.atom) | 工具更新 | 官方一手源 | 专门主题源 |
| [国内模型动态 · 新闻聚合](https://news.google.com/rss/search?q=(DeepSeek+OR+Qwen+OR+%E6%99%BA%E8%B0%B1+OR+%E8%B1%86%E5%8C%85+OR+Kimi+OR+MiniMax)+when:2d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans) | 国内动态 | 新闻聚合（需核对原文） | 标题与分类标签 |
| [AI 政策与安全 · 新闻聚合](https://news.google.com/rss/search?q=(%22artificial+intelligence%22+OR+%22AI%22)+(regulation+OR+policy+OR+copyright+OR+safety)+when:2d&hl=en-US&gl=US&ceid=US:en) | 政策与安全 | 新闻聚合（需核对原文） | 标题与分类标签 |
| [AI 融资与芯片 · 新闻聚合](https://news.google.com/rss/search?q=(%22artificial+intelligence%22+OR+%22AI%22)+(funding+OR+acquisition+OR+chip)+when:2d&hl=en-US&gl=US&ceid=US:en) | 融资与算力 | 新闻聚合（需核对原文） | 标题与分类标签 |

## 可用性与限制

2026-10-21 联网检查时，44/44 个配置入口可获取并解析。这个结果只反映检查时的连通与格式，不代表每个信源当天都有更新；日报逐次记录可用状态、获取条目数、过滤情况与实际新增数。

- 公开 RSS 往往只返回最近 10～100 篇；超过这个窗口、公开订阅未收录的文章，或每天一次检查之间出现又移出窗口的内容，可能漏采。
- 雷达与新闻聚合有各自的上游筛选；聚合查询有数量上限，不能等同于全网信息。
- 公众号、微信私域、需要登录的 X 内容、付费文章全文与没有公开订阅的站点，不在直接抓取范围。国内模型通过媒体与关键词聚合补充，不能保证覆盖厂商全部公告。
- Qwen 旧博客订阅的最新条目停留在 2025 年，因此未作为持续更新的直接信源；机器之心旧 `/rss` 入口、部分其他站点的候选地址未通过本次检查，未加入配置。
- 少数社区转订只提供日期，以其带时区的时间戳为准，不能视为精确到分钟的官方发布时间。
- 综合媒体按标题与分类标签筛选 AI，可能有漏检或误检。所有来源仅保留真实时间、原始标题、链接及来源提供的短摘要，不自动翻译或生成分析。
- arXiv 是预印本平台，论文可能尚未经过同行评审；完整列表见当日 `.papers.md` 附件，主日报只预览前 25 篇。
- 来源暂时失败会明确显示；部分成功仍生成日报，全部失败则保留原状态等待重试。

## 检查信源

```sh
python3 daily.py --check-sources
```

该命令输出每个入口的抓取结果、总条目数、主题过滤后的数量与最新条目时间，不写入归档。任一入口失败返回非零退出码；没有近期更新与网络失败是不同的情况。
