# PKB - Personal Knowledge Base

A personal Claude Code plugin marketplace for LLM-powered knowledge management, based on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## Install

```bash
/plugin marketplace add dengd1937/pkb
/plugin install pkb@pkb
```

## Usage

### Ingest a source
> Ingest this article: https://example.com/article

### Ingest a WeChat article
> Ingest this WeChat article: https://mp.weixin.qq.com/s/...

Requires Python 3.10+ with dependencies installed:
```bash
pip install -r skills/wechat2md/requirements.txt
```

### Query the knowledge base
> What do I know about X?

### Lint the knowledge base
> Lint my knowledge base

### Scrape a tweet or X Article to Markdown
> 保存这条推特：https://x.com/user/status/123
>
> 把这条推文转 Markdown 到 ./tweets/foo.md

## Structure

```
pkb/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   ├── llm-wiki/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── wechat2md/
│   │   ├── SKILL.md
│   │   ├── main.py
│   │   ├── mcp_server.py
│   │   ├── requirements.txt
│   │   └── wechat_to_md/
│   └── x2md/
│       ├── SKILL.md
│       └── scripts/
├── CLAUDE.md
├── package.json
└── README.md
```

- `llm-wiki` creates `raw/` directories in your project at runtime. Each source is saved as a Chinese close-reading archive (精读档案) with full metadata for traceability.
- `wechat2md` converts WeChat (mp.weixin.qq.com) articles to Markdown — see its SKILL.md for the Python dependencies.
- `x2md` scrapes X/Twitter URLs (tweets, Articles, threads) to Markdown via headless Chromium — assumes `~/.scrapling-venv` is set up; see its SKILL.md.
