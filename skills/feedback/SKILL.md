---
name: feedback
description: "Use when the user wants to report a bug, request a feature, or give feedback about the PKB plugin. Triggers: 'report a bug', 'file an issue', 'give feedback', 'request a feature', '反馈', '报 bug', '建议', '提个 issue', or any user frustration about a skill not working correctly."
---

# PKB Feedback

File issues to [dengd1937/pkb](https://github.com/dengd1937/pkb) directly from Claude Code. Supports bug reports and feature requests with structured environment info for reproducibility.

## Prerequisites

- `gh` (GitHub CLI) must be installed and authenticated. If not available, tell the user to install it: https://cli.github.com/

## Flow

### 1. Determine type

Ask the user if this is a:
- **Bug report** — something isn't working as expected
- **Feature request** — a suggestion for new functionality or improvement

If the user's message already makes this clear, skip asking.

### 2. Collect information

Ask for:
- **Title** — brief summary of the issue. Draft one based on the user's description and confirm with them.
- **Description**:
  - Bug: what happened, what was expected, steps to reproduce
  - Feature: desired behavior, use case, why it would help
- **Which skill** — llm-wiki, wechat2md, x2md, feedback, or "general" (for plugin-level issues)

### 3. Collect environment (automatic)

Run these commands and include the output in the issue body:
- `gh version` — GitHub CLI version
- `uname -a` (or `sw_vers` on macOS) — OS info
- Read the `version` field from the nearest `marketplace.json` (plugin version)

### 4. Draft and confirm

Compose the issue body using this structure:

```markdown
## {Bug Report | Feature Request}

### Description

{user's description}

### Skill

{skill name or "general"}

### Environment

- PKB version: {version from marketplace.json}
- OS: {uname output}
- gh CLI: {gh version output}
```

**Show the full draft to the user** (title + body) and ask for confirmation before creating the issue.

### 5. Create issue

```
gh issue create --repo dengd1937/pkb --title "{title}" --body "{body}" --label "{bug|enhancement}"
```

If the label does not exist yet in the repo, create it first:
```
gh label create bug --repo dengd1937/pkb --color "d73a4a" --description "Something isn't working"
gh label create enhancement --repo dengd1937/pkb --color "a2eeef" --description "New feature or request"
```

Report the created issue URL back to the user.

## Error handling

- `gh` not installed → tell user to install from https://cli.github.com/
- `gh` not authenticated → suggest running `gh auth login`
- Label creation fails → retry the issue creation without the label flag
- Issue creation fails → show the draft body so the user can file manually at https://github.com/dengd1937/pkb/issues/new
