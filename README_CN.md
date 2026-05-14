# PKB - 个人知识库

基于 [Karpathy 的 LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式构建的个人 Claude Code 插件，用于 LLM 驱动的知识管理。

## 功能

- **采集 (Ingest)** — 抓取来源（URL、文章、粘贴文本）并存入持久的 `raw/` 目录
- **编译 (Compile)** — LLM 将原始素材合成为结构化的 `wiki/` 文章
- **查询 (Query)** — 从已有知识中搜索并回答问题
- **检查 (Lint)** — 自动修复失效链接、补全索引条目、检测质量问题
- **微信** — 通过 CLI 将微信公众号文章转换为 Markdown

## 安装

```bash
/plugin marketplace add dengd1937/pkb
/plugin install pkb@pkb
```

## 使用

### 采集来源

```
Ingest this article: https://example.com/article
```

### 采集微信公众号文章

```
Ingest this WeChat article: https://mp.weixin.qq.com/s/...
```

需要 Python 3.10+：

```bash
pip install -r skills/wechat2md/requirements.txt
```

### 查询知识库

```
What do I know about X?
```

### 检查知识库

```
Lint my wiki
```

## 架构

```
your-project/
├── raw/                    # 不可变的原始素材（按主题组织）
│   └── <topic>/
│       └── YYYY-MM-DD-slug.md
└── wiki/                   # LLM 维护的知识库
    ├── index.md            # 全局文章索引
    ├── log.md              # 追加式操作日志
    └── <topic>/
        └── article.md
```

三种操作驱动知识库运转：

| 操作 | 作用 |
|------|------|
| **采集** | 抓取来源 → 存入 `raw/` → 编译进 `wiki/` |
| **查询** | 搜索 wiki 文章 → 综合回答 → 可选归档 |
| **检查** | 修复失效链接、校验索引、检测质量问题 |

## Skills

### llm-wiki

核心知识库 skill。管理 `raw/` → `wiki/` 流水线，支持级联更新和交叉引用。

### wechat2md

微信公众号文章转换器。使用 [Camoufox](https://github.com/nicholasgasior/camoufox)（反检测浏览器）抓取文章，转换为干净的 Markdown，支持：

- 元数据提取（标题、作者、发布时间）
- 代码块处理与语言检测
- 音视频引用提取
- 可选的本地图片下载

来源：[bzd6661/wechat-article-for-ai](https://github.com/bzd6661/wechat-article-for-ai)

## 项目结构

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

## 许可证

[MIT](LICENSE)
