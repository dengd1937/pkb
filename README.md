# PKB - Personal Knowledge Base

A personal Claude Code plugin marketplace for LLM-powered knowledge management, based on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## Features

- **Ingest** — Fetch sources (URLs, articles, pasted text) into a persistent `raw/` directory
- **Compile** — LLM synthesizes raw material into structured `wiki/` articles
- **Query** — Search and answer questions from your accumulated knowledge
- **Lint** — Auto-fix broken links, missing index entries, and detect quality issues
- **WeChat** — Convert WeChat Official Account articles to Markdown via CLI

## Install

```bash
/plugin marketplace add dengd1937/pkb
/plugin install pkb@pkb
```

## Usage

### Ingest a source

```
Ingest this article: https://example.com/article
```

### Ingest a WeChat article

```
Ingest this WeChat article: https://mp.weixin.qq.com/s/...
```

Requires Python 3.10+:

```bash
pip install -r skills/wechat2md/requirements.txt
```

### Query the wiki

```
What do I know about X?
```

### Lint the wiki

```
Lint my wiki
```

## Architecture

```
your-project/
├── raw/                    # Immutable source material (topic-organized)
│   └── <topic>/
│       └── YYYY-MM-DD-slug.md
└── wiki/                   # LLM-maintained knowledge base
    ├── index.md            # Global article index
    ├── log.md              # Append-only operation log
    └── <topic>/
        └── article.md
```

Three operations drive the knowledge base:

| Operation | What it does |
|-----------|-------------|
| **Ingest** | Fetch source → save to `raw/` → compile into `wiki/` |
| **Query** | Search wiki articles → synthesize answer → optionally archive |
| **Lint** | Fix broken links, validate index, detect quality issues |

## Skills

### llm-wiki

Core knowledge base skill. Manages the `raw/` → `wiki/` pipeline with cascade updates and cross-referencing.

### wechat2md

WeChat Official Account article converter. Uses [Camoufox](https://github.com/nicholasgasior/camoufox) (anti-detection browser) to fetch articles, then converts to clean Markdown with:

- Metadata extraction (title, author, publish time)
- Code block handling with language detection
- Audio/video reference extraction
- Optional local image download

Source: [bzd6661/wechat-article-for-ai](https://github.com/bzd6661/wechat-article-for-ai)

## Project Structure

```
pkb/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   ├── llm-wiki/
│   │   ├── SKILL.md
│   │   └── references/
│   └── wechat2md/
│       ├── SKILL.md
│       ├── main.py
│       ├── mcp_server.py
│       ├── requirements.txt
│       └── wechat_to_md/
├── CLAUDE.md
├── LICENSE
├── package.json
└── README.md
```

## License

[MIT](LICENSE)
