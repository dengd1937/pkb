---
name: wechat2md
description: "Use when the user wants to ingest a WeChat Official Account (微信公众号) article. Triggers: URL from mp.weixin.qq.com, 'WeChat article', '微信公众号', 'convert WeChat', or any ingest request involving a WeChat URL."
---

# WeChat Article to Markdown

Convert WeChat Official Account articles into clean Markdown, then feed into the llm-wiki knowledge base.

## Prerequisites

Before first use, install Python dependencies (Python 3.10+ required):

```bash
pip install -r skills/wechat2md/requirements.txt
```

Camoufox browser (~100 MB) is auto-downloaded on first run.

## When This Skill Activates

When the user provides a `mp.weixin.qq.com` URL and asks to ingest/collect/save it, this skill handles the Fetch step. The Compile step is delegated to llm-wiki.

## Workflow

### Step 1: Run CLI

From the project root, run:

```bash
python skills/wechat2md/main.py "WECHAT_URL" -o /tmp/wechat-output --no-frontmatter --no-images --force -v
```

Flags:
- `-o /tmp/wechat-output` — use a temp directory to avoid polluting the project
- `--no-frontmatter` — output blockquote-style metadata (closer to raw-template.md format)
- `--no-images` — keep remote image URLs (simpler for raw/ storage)
- `--force` — overwrite if output exists
- `-v` — verbose logging for debugging

Output structure:
```
/tmp/wechat-output/
  <article-title>/
    <article-title>.md    # Markdown with blockquote metadata
```

If the user wants images downloaded locally, omit `--no-images` and use `-o raw/<topic>` directly. The images will be saved in `raw/<topic>/<article-title>/images/`.

### Step 2: Transform to raw-template.md Format

The CLI with `--no-frontmatter` outputs:
```
# {Title}

> Author: {Author}
> Date: {YYYY-MM-DD HH:MM:SS}
> Source: {URL}
---
{body}
```

Transform this to match raw-template.md:
1. Keep `# {Title}` as-is.
2. Replace the metadata block with:
   ```
   > Source: {original URL}
   > Collected: {today YYYY-MM-DD}
   > Published: {date portion from Date field, YYYY-MM-DD format; or Unknown}
   ```
3. Remove the `---` separator between metadata and body.
4. Keep the body content unchanged.

### Step 3: Save to raw/

Save the transformed file following llm-wiki conventions:

- Path: `raw/<topic>/YYYY-MM-DD-<slug>.md`
- Topic: check existing `raw/` subdirectories first; reuse one if the topic is close enough. Create a new subdirectory only for genuinely distinct topics.
- Slug: from the article title, kebab-case, max 60 characters.
- If a file with the same name already exists, append a numeric suffix (e.g., `slug-2.md`).

If the CLI created an intermediate output directory (e.g., `/tmp/wechat-output/<title>/`), delete it after saving the raw file.

### Step 4: Hand Off to llm-wiki

Once the raw file is saved, proceed with llm-wiki's Compile step:
1. Read the raw file.
2. Determine placement: merge into existing article or create new article (follow llm-wiki Compile rules).
3. Run cascade updates on related articles.
4. Update `wiki/index.md` and `wiki/log.md` per llm-wiki conventions.

## Error Handling

- **CAPTCHA**: Tell the user: "WeChat triggered a verification page. Please run this command manually in your terminal to solve the CAPTCHA, then paste the resulting Markdown here:" and provide the command with `--no-headless` flag.
- **Network failure**: Retry once. If it fails again, ask the user to provide the content another way (paste text, screenshot, etc.).
- **Empty content / parse error**: The article may be behind a paywall or removed. Ask the user to paste the text directly.
- **Invalid URL**: Only `https://mp.weixin.qq.com/s/...` URLs are supported. For other URLs, fall back to llm-wiki's standard Fetch mechanism.

## CLI Reference

| Flag | Description |
|------|-------------|
| `"URL"` | WeChat article URL |
| `-f FILE` | Batch: text file with URLs (one per line) |
| `-o DIR` | Output directory (default: ./output) |
| `-c N` | Image download concurrency (default: 5) |
| `--no-images` | Skip image download, keep remote URLs |
| `--no-headless` | Show browser (for solving CAPTCHAs) |
| `--force` | Overwrite existing output |
| `--no-frontmatter` | Blockquote metadata instead of YAML |
| `-v` | Verbose/debug logging |
