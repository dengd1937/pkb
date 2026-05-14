---
name: x2md
description: "Use when the user wants to save a specific X/Twitter URL (single tweet, X Article, or a thread starter) as a clean Markdown file in pkb's raw/ layout. Triggers: '保存这条推特', '把这条推文转 Markdown', '抓推特链接', '保存 X 长文', 'x2md', a tweet URL pasted alone, or any mention of '推文转 Markdown'."
---

# x2md — X/Twitter to Markdown

抓取一条 X/Twitter 链接（单条推文、X Articles 长文、可选整条 thread），转成符合 pkb `raw-template` 格式的 Markdown，**默认直接落到 `./raw/<topic>/` 目录**，让 `llm-wiki` 后续可以直接 ingest。基于 headless Chromium，**不需要登录 cookies**。

## Architecture

- 输入：单个 URL（`x.com` / `twitter.com` / `fxtwitter.com` 任一域名都接受）
- 抓取：scrapling/patchright headless Chromium 直接访问 `/<user>/status/<id>` 页面
- 检测：先尝试按 X Article 解析（`og:type=article` + 文章结构），失败则按普通推文解析
- **输出**：默认 `./raw/<topic>/<YYYY-MM-DD>-<slug>.md`，自带 pkb 标准 metadata header（Source / Collected / Published）。可用 `--output` 覆盖路径，`--stdout` 改打印
- 图片：默认跳过；可选下载到本地 `assets/` 子目录；可选上传 Cloudflare R2

脚本路径：`scripts/tweet_scrape.py`（相对本 SKILL.md）

---

## Prerequisites

首次使用前需准备 Python 环境（一次性，全局共享）：

```bash
python3 -m venv ~/.scrapling-venv
~/.scrapling-venv/bin/pip install "scrapling[all]" boto3
~/.scrapling-venv/bin/python3 -c "from scrapling.fetchers import StealthyFetcher; StealthyFetcher.setup()"
```

R2 图床（仅 `--images r2` 模式需要）通过环境变量配置：

```bash
export R2_BUCKET=<bucket>
export R2_ACCESS_KEY=<access-key-id>
export R2_SECRET_KEY=<secret-access-key>
export R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
export R2_PUBLIC_URL=https://<your-public-domain>
export R2_PREFIX=tweets        # 可选，默认 tweets
```

如果首次触发且检测到 venv 不存在，先把上述命令告知用户并停止；不要试图替他装。

---

## Invocation

```bash
~/.scrapling-venv/bin/python3 <skill_dir>/scripts/tweet_scrape.py <URL> [options]
```

参数：

| Flag | 默认 | 含义 |
|---|---|---|
| `<URL>` | — | 必填，推文/长文 URL |
| `--raw-dir DIR` | `./raw` | pkb `raw/` 根目录 |
| `--topic NAME` | `tweets` | `raw/` 下的主题子目录 |
| `--output PATH` / `-o PATH` | 自动 | 显式覆盖输出路径 |
| `--stdout` | off | 不写盘，直接打印 |
| `--thread` | off | 抓整条自回复 thread（仅普通推文有效，长文模式忽略） |
| `--images skip\|local\|r2` | `skip` | 图片处理策略 |

不指定 `--output` 也不带 `--stdout` 时，文件名规则：

| 类型 | 文件名 |
|---|---|
| 单条推文 | `<YYYY-MM-DD>-<user>-<status_id>.md` |
| Thread | `<YYYY-MM-DD>-<user>-thread-<lead_id>.md` |
| X Article 长文 | `<YYYY-MM-DD>-<title-slug>-<status_id>.md` |

---

## Workflow

1. **解析 URL**：从用户消息里抠出推文链接，验证格式
2. **选 topic**：默认 `tweets`；若用户内容明显属于 ML/编程/设计等，建议 Claude 在执行前先扫一眼现有 `raw/` 子目录复用主题，或问用户一句
3. **询问图片策略**：默认 `skip`；如果用户提到图片/插图，问要 `local` 还是 `r2`
4. **询问 thread**：用户没明说就只抓单条；用户说 "整个 thread" / "全文" 才加 `--thread`
5. **执行脚本**：用 Bash 工具调用上面的命令，把 stderr 也展示给用户（包含 `[detect]`、`[fetch]`、`[saved]` 等进度行）
6. **报告结果**：告知最终保存路径、字符数、检测到的类型
7. **可选 ingest**：如果当前工作目录存在 `wiki/` 目录（pkb 项目），询问用户要不要触发 `llm-wiki` 的 Ingest 流程把这个 raw 文件编译进 wiki

---

## Output Format (pkb raw-template 兼容)

### 单条推文

```markdown
# Tweet by @<user> — YYYY-MM-DD

> Source: <URL>
> Collected: <today YYYY-MM-DD>
> Published: <YYYY-MM-DD>

<推文正文>

> 📎 Quoted: <被引用的推文，若有>

---

![image](assets/<id>/<id>_1.jpg)
```

### X Article 长文

```markdown
# <文章标题>

> Source: <URL>
> Collected: <today>
> Published: <YYYY-MM-DD>

作者：@<user>

---

# H1...
## H2...
段落...
- 列表项
```

### Thread

```markdown
# Thread by @<user> — YYYY-MM-DD (N tweets)

> Source: <lead URL>
> Collected: <today>
> Published: <YYYY-MM-DD>

## 1/N — <ISO datetime>
<正文>
🔗 <URL>

## 2/N — ...
```

---

## Notes

- 默认路径基于 **当前工作目录**：用户应在 pkb 项目根下运行，否则会在 cwd 创建一个新的 `./raw/` 目录
- 首次启动 Chromium 较慢（5-15 秒），属正常
- 推文页面 DOM 偶尔变动，遇到抽不到正文时脚本会自动 fallback 到 `og:description`（截断版）
- 长文检测靠 `og:type=article`；如果 X 改了实现，可能误判，需要更新脚本里的 `extract_article`
- Thread 重建只看对话页渲染出的 article 元素，跨页的长 thread 不一定全
- 脚本不写任何 Twitter 用户态数据，纯只读访问
