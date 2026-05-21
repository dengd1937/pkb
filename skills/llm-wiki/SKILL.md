---
name: llm-wiki
description: "Use when building or maintaining a personal LLM-powered knowledge base. Triggers: ingesting sources into raw/, querying knowledge, linting quality, 'add to wiki', 'what do I know about', or any mention of 'LLM wiki' or 'Karpathy wiki'."
---

# Karpathy LLM Wiki

Build and maintain a personal knowledge base using LLMs. You manage one directory: `raw/` — per-source Chinese close-reading archives (精读档案), organized by topic. Each source is preserved as a faithful, figure-rich treatment capturing key text, images, tables, formulas, and data.

Core ideas from Karpathy:
- "The LLM writes and maintains the wiki; the human reads and asks questions."
- "The wiki is a persistent, compounding artifact."

## Architecture

Single layer, under the user's project root:

**raw/** — Per-source Chinese close-reading archives. Each file is a comprehensive treatment of one source — preserving key passages, figures, tables, and data in full. Organized by topic subdirectories (e.g., `raw/machine-learning/`). Contains one special file:
- `raw/index.md` — Lightweight directory listing. One row per raw file, grouped by topic.

**notes/** — Saved synthesized answers (optional, user-initiated only). Flat directory, no subdirectories. Each note is a cross-source synthesis that the user chose to persist. See `references/note-template.md` for format.

**SKILL.md** (this file) — Schema layer. Defines structure and workflow rules.

Templates live in `references/` relative to this file. Read them when you need the exact format for raw files.

### Initialization

Triggers only on the first Ingest. Check whether `raw/` exists. Create only what is missing; never overwrite existing files:

- `raw/` directory (with `.gitkeep`)
- `raw/index.md` — heading `# Knowledge Base Index`, empty body

If Query or Lint cannot find the raw/ structure, tell the user: "Run an ingest first to initialize the knowledge base." Do not auto-create.

---

## Ingest

Fetch a source into raw/ and update index.md. One step only.

### Fetch (raw/)

1. Get the source content using whatever web or file tools your environment provides. If nothing can reach the source, ask the user to paste it directly.

2. Pick a topic directory. Check existing `raw/` subdirectories first; reuse one if the topic is close enough. Create a new subdirectory only for genuinely distinct topics.

3. Save as `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`.
   - Slug from source title, kebab-case, max 60 characters.
   - Published date unknown → omit the date prefix from the file name (e.g., `descriptive-slug.md`). The metadata Published field still appears; set it to `Unknown`.
   - If a file with the same name already exists, append a numeric suffix (e.g., `descriptive-slug-2.md`).
   - Include full metadata header for traceability (Source, Full text, Collected, Published, author, etc.). **Never omit or truncate metadata.**

4. The raw file is a **per-source Chinese close-reading archive (精读档案)**. Preserve the essence — key text, figures, tables, formulas, code, and data. Be thorough, not selective. If a fetched page looks like only an abstract / teaser / paywalled preview (e.g., an arXiv `/abs/` page), you must obtain the real body before saving — do not save a partial.

   - **Blogs / articles / docs**: follow the **Blog / Article Close Reading** rules below. See `references/blog-template.md`.
   - **Academic papers (arXiv, OpenReview, ACL Anthology, conference PDFs)**: follow the **Academic Paper Close Reading** rules below. See `references/paper-template.md`.
   - **Other sources**: See `references/raw-template.md` as fallback.
   - **Single social-media posts / threads (X, etc.)**: out of scope — use the dedicated `x2md` skill.

#### Academic Paper Close Reading

For papers, the raw file is a thorough **Chinese close reading (精读)** — section-by-section walkthrough preserving key text, formulas, figures, and data. Reproducibility is anchored by the stable metadata URLs.

- **Metadata**: Always include `Source` (canonical citable URL), `Full text` (URL actually read), `Collected`, `Published`, authors, affiliations, arXiv ID, venue. Full traceability — these fields are the provenance chain back to the original.
- **arXiv full-text chain** (try in order, record which worked as `Full text`):
  1. `https://arxiv.org/html/<id>` — official HTML, only exists for papers submitted from ~2023-12 onward.
  2. `https://ar5iv.labs.arxiv.org/html/<id>` — ar5iv mirror; the workhorse for older papers.
  3. PDF — last-resort fallback.
- **Abstract**: faithful Chinese translation.
- **Body**: section-by-section close reading in Chinese. Cover down to subsections. Preserve:
  - Key arguments and reasoning chains in full, not just conclusions.
  - Technical terms in English (chain-of-thought, GSM8K, emergent ability).
  - Key formulas (LaTeX) and key numbers verbatim.
  - Experimental setup details, ablation results, robustness analysis.
  - Important passages quoted directly when the original phrasing matters.
- **Figures**: download ALL content figures into `raw/<topic>/assets/<slug>/` and reference them locally, each with a Chinese caption. Charts rendered as inline SVG/HTML (not downloadable images) → transcribe their data into a Markdown table instead. Do not skip figures — they are part of the reading.
- **Tables**: convert ALL result tables to Markdown tables, with real numbers transcribed verbatim (never invent or estimate values).
- **References**: list the works the body actually leans on, point to the `Full text` URL for the complete bibliography.
- **Strip as format noise**: duplicated title/author/email block, figure-axis numeric runs, mirror footer chrome, submission boilerplate (NeurIPS Checklist, Version Control, Reproducibility / Ethics Statement, Acknowledgements).
- **Do not add external interpretation** (意义 / 影响 / cross-source commentary). This is a faithful reading of ONE source.

#### Blog / Article Close Reading

For blogs/articles/docs, the raw file is a faithful **full Chinese translation of the entire post** — every section, paragraph, list, and table preserved; nothing condensed or dropped.

- **Metadata**: Always include `Source`, `Full text`, `Collected`, `Published`, author, publication. Full traceability.
- **Fetch the real full body, not a summarizer's output**. Pull the raw HTML directly (e.g. `curl -sL`), isolate the article content container, strip site chrome (nav, sidebar, footer, comment widgets, share buttons), and convert to Markdown. Do **not** use a summarizing web-fetch tool as the source — it silently truncates and paraphrases.
- **Translate the full text into Chinese**, faithfully and completely. Keep original section structure and ordering. Keep technical terms / proper nouns in their original form (e.g. chain-of-thought, ReAct, HNSW). Translate figure captions into Chinese.
- **Keep code, prompts, configs, JSON, BibTeX, and command snippets verbatim** in the original language inside fenced code blocks — translating an artifact corrupts it.
- **Images**: download EVERY content image into `raw/<topic>/assets/<slug>/` and reference them locally inline at their original position, each with a translated caption. Convert HTML tables to Markdown tables.
- **References / citation blocks**: keep as-is (do not translate bibliographic entries).
- **Do not add interpretation** (意义 / 影响 / 个人评价). Faithful reading only.

See `references/raw-template.md` (fallback) / `references/blog-template.md` (blogs) / `references/paper-template.md` (papers) for the exact format.

### Post-Ingest

Update `raw/index.md`: add entry for the new file. When adding a new topic section, include a one-line description. See `references/index-template.md` for format.

---

## Query

Search the raw/ archives and answer questions. Examples of triggers:
- "What do I know about X?"
- "Summarize everything related to Y"
- "Compare A and B based on my knowledge base"

### Steps

1. Read `raw/index.md` to locate relevant files.
2. Read those raw files and synthesize an answer.
3. Prefer raw/ content over your own training knowledge. Cite sources with markdown links: `[Title](raw/topic/file.md)` (project-root-relative paths for in-conversation citations).
4. Output the answer in the conversation. Do not write files unless the user explicitly asks to save the answer (see Save below).

### Save

When the user explicitly asks to save, persist, or keep the answer:

1. Create `notes/` if it does not exist (with `.gitkeep`).
2. Save as `notes/descriptive-slug.md`. Slug from the query topic, kebab-case, max 60 characters.
3. The note must include a `Raw` field linking back to every raw/ file it draws from — this is the provenance chain. Use relative paths (e.g., `../raw/topic/file.md`).
4. Output the file path to the user.

---

## Lint

Quality checks on raw/ archives. Two categories with different authority levels.

### Deterministic Checks (auto-fix)

Fix these automatically:

**Index consistency** — compare `raw/index.md` against actual raw/ files (excluding index.md):
- File exists but missing from index → add entry with `(no summary)` placeholder.
- Index entry points to nonexistent file → mark as `[MISSING]`. Do not delete; let the user decide.

**Asset links** — for every image/file link in raw/ files:
- Target does not exist → report to the user.

**Notes Raw references** — for every `Raw` link in notes/ files:
- Target raw/ file does not exist → report to the user.

### Heuristic Checks (report only)

These rely on your judgment. Report findings without auto-fixing:

- Metadata fields missing or incomplete (Source, Full text, Collected, Published, author)
- Images still pointing to external URLs instead of local `assets/` paths
- Tables with placeholder or estimated values instead of real data
- Code blocks containing Chinese — likely translated when they should be verbatim original
- Sections that are overly thin — likely incomplete close readings
- Topic directories that could be merged

### Post-Lint

Report findings to the user. No log file — output a summary in the conversation.

---

## Conventions

- Standard markdown with relative links throughout.
- raw/ supports one level of topic subdirectories only. No deeper nesting.
- Today's date for Collected dates. Published dates come from the source (use `Unknown` when unavailable).
- Inside raw/ files, all markdown links use paths relative to the current file. In conversation output, use project-root-relative paths (e.g., `raw/topic/file.md`).
- Ingest updates `raw/index.md`. Lint may update `raw/index.md` (auto-fix only). Queries write files only when the user explicitly asks to save.
