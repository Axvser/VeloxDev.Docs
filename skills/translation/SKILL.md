# Translation — Cross-Language Document Translation & Adaptation

> **Sub-skill.** Load only when the user asks to translate Wiki content to another language.
> **Default path phase: Phase 4 (final alignment)**
> **Prerequisite:** Phases 2 (api-docs) and 3 (se-analysis) completed with bilingual drafts

Translates and adapts Wiki content across languages while preserving code examples, KaTeX formulas, Mermaid/PlantUML diagrams, and links.

## When to Load

- "Translate to Chinese"
- "Create Japanese version"
- "Add bilingual support"
- "Translate documentation to another language"

## Core Principles

- **Protect technical content** — Code examples, KaTeX formulas, Mermaid diagrams, links stay **unchanged**
- **Translate only text** — Titles, descriptions, comments and other natural language content
- **Mirror directory structure** — `content/en/Xxx` → `content/zh/Xxx` (for Chinese)
- **Verify references** — Internal links must point to the corresponding language path

## Translation Scope

| Content Type | Handling |
|---|---|
| Headings, paragraphs, descriptions | Translate |
| Code blocks, inline code | **Leave unchanged** |
| KaTeX formulas `$...$` `$$...$$` | **Leave unchanged** |
| Mermaid/PlantUML code blocks | Translate label text in `participant`/`title`/`text`, preserve structure |
| Image alt text | Translate |
| Links `[text](url)` | Translate `text`, preserve `url` |
| Table content | Translate cell text |
| Footnotes | Translate |

## Role in the Default Path

In the default path, Phases 2 and 3 already produce **bilingual output**. Phase 4's responsibilities are:

1. **Check consistency** — Compare `en/` and `zh/` page structure and content completeness
2. **Fill gaps** — If a page exists only in English, supply the Chinese translation
3. **Align terminology** — Ensure key terms use consistent translations across all Chinese docs
4. **Verify navigation** — Ensure `tree.json` correctly reflects the bilingual structure

## Translation Style Guide

```
← Source (en)       →  Target (zh)
--------------------------------
Service             →  服务
Repository          →  仓储
Middleware          →  中间件
Dependency Injection → 依赖注入
Interface           →  接口
Implementation      →  实现
```
