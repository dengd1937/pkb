# PKB - Personal Knowledge Base

A personal Claude Code plugin marketplace for LLM-powered knowledge management, based on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## Install

```bash
/plugin marketplace add sdeng079/pkb
/plugin install pkb@pkb
```

## Usage

### Ingest a source
> Ingest this article: https://example.com/article

### Query the wiki
> What do I know about X?

### Lint the wiki
> Lint my wiki

## Structure

```
pkb/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   └── llm-wiki/
│       ├── SKILL.md
│       └── references/
├── CLAUDE.md
├── package.json
└── README.md
```

The skill creates `raw/` and `wiki/` directories in your project at runtime.
