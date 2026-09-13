---
name: cloud-glyph-wiki-create
description: Analyze project source code and produce beautiful, well-structured Wiki documentation
---

## Responsibility

Strictly follow the workflow defined in this SKILL to produce Wiki documentation that meets specifications

## Variable Conventions

> CloudGlyph_Git:[https://github.com/Axvser/CloudGlyph][ReadOnly][Template Repository] - Cloud Glyph repository address

> CloudGlyph_Child_Git:[request] - Local Wiki repository root. This Wiki repository is an independent repo created from the Cloud Glyph:[Template Repository]. It is not counted in Wiki analysis or writing.

> Project_Root:[request] - Root directory of the project to be documented

> MainSKILL_Path:[CloudGlyph_Child_Git/skills/SKILL.md] - Path to the current skill

> Wiki_Root:[CloudGlyph_Child_Git/src/CloudGlyph/Assets/Docs/content/{languages}/] - Root directory for output documentation, dynamically divided by language.

> LanguageMap_List:[CloudGlyph_Child_Git/src/CloudGlyph/Assets/Docs/config/languages.json] - Range of languages supported by the Wiki

> LanguageTargets_List:[request] - Range of languages the user wants the Wiki to support

## Analysis Paradigm

⚙ **Wiki content is organized around「Features」, not the Project's directory structure.** The directory structure is an implementation detail that may evolve with architecture or team conventions — it must not be mapped directly onto the Wiki structure.

⚙ Definition of a Feature: a cohesive set of capabilities a project exposes, usually corresponding to a usage scenario that can be independently described, used, and verified. A single feature may span multiple directories/projects, and a single directory may host several features — feature is the deciding unit, directories are only lookup hints.

⚙ Feature/API discovery order and paths (priority from high to low):

1. **Entry-point understanding** — read the project's README, entry files, build scripts, etc., to form a candidate feature list
2. **Demo / Example first** — scan Examples/, samples/, demo, etc., and fully read all source files; Demos are the primary evidence source for features and APIs
3. **Test-driven** — for a feature lacking Demo, fully read the corresponding test files and extract feature boundaries and typical usage from test cases
4. **Source fallback** — only when the above are all absent, infer features from the source directory structure and interface signatures; such inferences MUST be explicitly marked as *inferred*

⚙ The order above applies to all project sizes: single-project, multi-project, and large frameworks/monorepos alike; for large projects it is especially forbidden to guess features from directory names alone.

⚙ Analysis artifact: a「Feature Inventory」listing per item: feature name / owning project / public API surface / evidence source (Demo / Test / inferred). It is the unified input for the subsequent Quick Start / API Reference / SE Analysis phases — the three phases work from the same inventory so every Wiki dimension stays consistent.

⚙ The「Feature Inventory」also carries a per-feature **Coverage Status** field (`TODO / QS ✓ / API ✓ / SE ✓`). Steps 3–5 update it as they finish each feature; step 8 (Review) reconciles it into a Coverage Reconciliation Matrix. The feature set is **frozen after discovery** — later steps only mark status, they never add, remove, or rename features; any correction must flow back into the inventory and be re-reconciled.

⚙ Sub-items under the five fixed dimensions (see Structure Conventions) are always organized by feature.

## Structure Conventions

⚙ {ID}_{PageName}/ - Folder naming convention when producing Markdown. The tree structure formed by folders is the directory structure the final App renders for the Wiki.

⚙ index.md - Each {ID}_{PageName}/ must have exactly one fixed-name index.md file, otherwise the directory structure will be incomplete. md files may be left blank. More subdirectories can be added to represent sub-items.

⚙ Every directory in the output path MUST contain an index.md — this includes intermediate/parent directories, not just leaf directories. After creating any new subdirectory, immediately verify an index.md exists in every ancestor directory of that path. A common mistake is to create e.g. `2_design_patterns/0_Workflow/index.md` while forgetting `2_design_patterns/index.md`.

Ultimately, the directory will present the following structure. These are five fixed dimensions, and /.../ means you may extend sub-items and add content based on specific functional divisions under the dimension, with no depth limit.

> Wiki_Root/0_Welcome/

> Wiki_Root/1_QuickStart/.../

> Wiki_Root/2_API/.../

> Wiki_Root/3_SE_Analysis/.../

> Wiki_Root/4_Copyright/.../

## Directory Grammar

⚙ Naming grammar by level:
- **Top-level — the five fixed dimensions (single-digit prefix):** `0_Welcome` / `1_QuickStart` / `2_API` / `3_SE_Analysis` / `4_Copyright`.
- **Every sub-level at any depth (two-digit prefix `NN_`, `00`–`99`):** lowercase kebab-case for English wikis, Chinese names for Chinese-language wikis, **no spaces**. E.g. `00_user-registration/`, `01_data-export/`.

⚙ **Granularity rule:** one directory = one "independently describable, usable, verifiable capability unit". Each dimension gives each feature exactly one directory; never merge multiple features into one directory, and never split one feature across sibling directories — nest instead. Feature names always come from the「Feature Inventory」; never invent a name while writing.

⚙ **Cross-dimension name consistency:** the SAME feature name must be used identically in the `1_QuickStart`, `2_API`, and `3_SE_Analysis` trees (within a language). A feature written `00_user-registration` in QuickStart must also be `00_user-registration` in API and in SE Analysis.

⚙ Complex features may nest further sub-capabilities (e.g. `00_user-registration/00_email-verification/`), obeying the same two-digit + kebab-case rule at every level.

⚙ **The numeric prefix is a path device, never a title.** `0_Welcome`, `1_QuickStart`, `00_user-registration` are directory names. The moment text is *rendered to a reader* — a heading, a link label, a breadcrumb, a table cell naming a page — the prefix must be gone: write `QuickStart`, `User registration`. The renderer strips the prefix from navigation titles itself (`gen_tree.py`), so a hand-written `1_QuickStart` in prose is always a defect, never a match for the sidebar. Only two places keep the prefix: the link *destination* (`../1_QuickStart/index.md`) and discussion that is explicitly about the directory layout.

⚙ **A feature name is a feature name, not a class name.** Feature directories are named for the capability the reader looks for (`user-registration`, `data-export`), taken from the「Feature Inventory」. Type, class and namespace names belong in the page body, never in a directory name.

⚙ **A heading never restates the heading above it.** The page opens with one H1 — its title — and the next heading must introduce something the H1 did not already say. Two shapes are defects:

- **The restatement chain.** `# Workflow System — Quick Start` followed by `## Workflow System` followed by `### Quick Start` shows the reader the same words three times before any content. The page title is the title; delete the headings that repeat it and promote what they contained.
- **The dimension echo.** A heading straight after the H1 whose whole text is the name of the parent dimension (`## Quick Start` on a page under `1_QuickStart`, `## API` under `2_API`) tells the reader only what the sidebar already shows. Start with the first real section instead.

Either way, content must not be lost: deleting such a heading means promoting its sub-headings one level, not deleting the section. `validate-titles.py` fails on both shapes, and the sidebar is the authority on whether a name has already been said.

⚙ **Page-focus limit & leaf budget (default-split):** a feature page is NOT a single monolithic document — splitting is the default, not the exception. A page WITHOUT sub-pages is a **leaf**; keep it at or under **~300 lines** and at most **3 distinct topics**. When a leaf would exceed that, split it along capability/operation/endpoint/type boundaries into **2+ child page directories** (e.g. `00_{Feature}/00_{Operation}/index.md`), and recurse if a child leaf also grows too large. Each parent `index.md` is then only a **short overview** (well under ~200 lines) that links **every** direct child using the same-language cross-page link syntax from 【Links & Navigation】.

⚙ **Outline-first (mandatory order):** when a page needs splitting, DO NOT write the long page first and split afterwards. FIRST create the planned child-page directories — each with an (initially empty) `index.md`, and every ancestor `index.md` in place — then run `gen_tree.py` so the skeleton appears in the navigation, and ONLY THEN fill each leaf within its budget. Write toward an existing outline, never toward one page that silently grows.

⚙ **Depth is free per dimension:** sub-pages under a feature are independent per dimension — QuickStart splits by setup/operations, API by namespace/type, SE by page-group — so nesting deeper in one dimension never forces the same split in another. Only the feature's own top-level name must stay consistent across `1_QuickStart` / `2_API` / `3_SE_Analysis`.

⚙ **Atomic pages are opt-in, not the default:** a page that must genuinely stay a single document (a verbatim license/AUTHORS text, one self-contained spec) may opt out of the line budget by putting `<!-- cg:atomic -->` as the **first line** of its `index.md`; pages under the `4_Copyright` dimension are exempt automatically. Use this sparingly — it is the escape hatch, and the gate is enforced: `python validate-structure.py` reports every leaf over the hard cap and every parent overview that fails to link one of its children.

**Illustrative example only — not a fixed requirement.** Fictional project "Acme Console" with three features (`user-registration`, `data-export`, `theme`). Every directory contains an `index.md`.

```
Wiki_Root/
├── 0_Welcome/
│   └── index.md
├── 1_QuickStart/
│   ├── index.md
│   ├── 00_user-registration/
│   │   └── index.md
│   ├── 01_data-export/
│   │   └── index.md
│   └── 02_theme/
│       └── index.md
├── 2_API/
│   ├── index.md
│   ├── 00_user-registration/
│   │   ├── index.md
│   │   └── 00_register-endpoint/
│   │       └── index.md
│   ├── 01_data-export/
│   │   └── index.md
│   └── 02_theme/
│       └── index.md
├── 3_SE_Analysis/
│   ├── index.md
│   ├── 00_file-structure/
│   │   └── index.md
│   ├── 01_functional-structure/
│   │   └── index.md
│   ├── 02_design-patterns/
│   │   ├── index.md
│   │   ├── 00_user-registration/
│   │   │   └── index.md
│   │   ├── 01_data-export/
│   │   │   └── index.md
│   │   └── 02_theme/
│   │       └── index.md
│   ├── 03_data-flow/
│   │   ├── index.md
│   │   └── 00_user-registration/
│   │       └── index.md
│   └── 04_complexity/
│       ├── index.md
│       └── 00_user-registration/
│           └── index.md
└── 4_Copyright/
    └── index.md
```

## Localisation

⚙ **Every page title is written in the wiki's own language.** When a language tree is produced, each directory segment and each page heading must be translated — `00_workflow-system` becomes `00_工作流系统`, not a copy of the English folder. This is not optional polish: the sidebar renders the directory name, so an untranslated segment shows up as stray English in an otherwise translated wiki.

⚙ **The one exception is a code identifier.** A segment that *is* a public type, attribute, namespace or API name in the source — `MVVM`, `AOP`, `MonoBehaviour`, `00_VeloxPropertyAttribute`, `00_transitionsystem` — stays verbatim in every language, because translating it would break the reader's ability to grep for it. The test is mechanical, not aesthetic: **does this exact token appear in the source code as a type/namespace/API name?** If yes, keep it. If it is a descriptive English phrase (`prerequisites`, `install`, `complete-code`, `attached-behaviors`, `patterns-overview`), it is a translation gap and MUST be translated.

⚙ The two languages must stay aligned in *structure* (same numeric-prefix topology, machine-checked by `validate-structure.py`) and in *meaning* — a page's title in one language is the translation of its title in the other, at the same position in the tree.

## Links & Navigation

⚙ A Wiki page may only contain these kinds of links:

1. **External** — targets beginning `https://`, `http://`, `mailto:`, or `tel:`. They open in the system browser / mail client / dialer. Use sparingly.
2. **Same-language page link (cross-page)** — a relative Markdown link whose destination resolves like a filesystem path (honoring `.` / `..`) to another page **directory inside the same language tree**. End the target with the directory path, an explicit `/index.md`, or a trailing `/`. Use **real folder names including numeric prefixes** (`0_Welcome`, `00_user-registration`); never link to a display title. Links must never cross languages.
   Examples from page `1_QuickStart/00_user-registration/index.md`:
   - child page inside the same feature: `[Email verification](00_email-verification/index.md)`
   - sibling page in the same section: `[Data export](../01_data-export/index.md)`
   - section overview (parent): `[QuickStart overview](../index.md)`
   - any top-level dimension: `[Welcome](../../0_Welcome/)`
   A parent `index.md` links its sub-pages exactly this way.
3. **In-page anchor** — a `#slug` link to a heading on the **same** page. The App auto-assigns every heading an id (slug) derived from its exact final text: lower-case it; keep letters, digits, `_`, `-` (CJK characters are kept as-is); drop every other character (`.`, `:`, `(`, `)`, …); turn spaces and `_` into `-`; collapse runs of `-` and trim leading/trailing `-`; duplicate slugs get a `-1`, `-2`, … suffix. Only hand-write `#…` anchors for headings with plain, punctuation-free text — e.g. heading `## 2. Text Formatting` → `#2-text-formatting`; heading `## Overview` → `#overview`.

⚙ **Link labels never carry the numeric prefix.** The destination is a path and keeps it (`../1_QuickStart/00_user-registration/index.md`); the visible label is prose and must not (`[QuickStart](../1_QuickStart/index.md)`, `[User registration](../1_QuickStart/00_user-registration/index.md)`). `[1_QuickStart](../1_QuickStart/index.md)` is a defect. The label is the page's plain title — the same string the sidebar shows — or a natural phrase that reads correctly in the sentence.

⚙ **Prohibited:** any other local/absolute/`file:` link, a link to another language's content, a link that escapes the language root, a cross-page target carrying a `#`, or any target you cannot resolve to a real page or heading. When in doubt, do not link.

## Rendered Content Members

⚙ Besides ordinary Markdown, the body may use these fenced blocks. Each is checked by a validator; a malformed block renders as a silent hole, so validate rather than assume.

| Fence | Use it for | Validator |
|---|---|---|
| `mermaid` | flow, sequence, class, state, ER, git graphs | `validate-mermaid.js` (real parser) / `validate-mermaid.py` |
| `plantuml` | API call sequences, component and deployment diagrams | `validate-plantuml.py --engine java` / `validate-plantuml.py` |
| `plot` | **mathematical curves** — see below | `validate-plot.py` |
| `video` | Bilibili / YouTube / Vimeo embeds | — |

⚙ **Function plots (`plot`) — use a curve when the subject IS a function.** A page that describes a curve, a response, a decay or an easing family should draw it, not describe it in prose or enumerate it in a table. The body is a **JSON object** (the [function-plot](https://mauriciopoppe.github.io/function-plot/) options), so numbers are JSON numbers — `2*PI` is invalid, `6.283185307179586` is not:

````markdown
```plot
{
  "title": "easeInOutQuad",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [0, 1] },
  "data": [
    { "fn": "x < 0.5 ? 2*x^2 : 1 - (-2*x + 2)^2/2" }
  ]
}
```
````

⚙ Plot rules that bite: constants are **upper-case** (`PI`, `E` — lower-case `pi` is undefined and the curve silently vanishes); `"data"` is an array of objects with `fn` (or `x`/`y`/`r`); piecewise curves use the ternary `?:`; a non-`y = f(x)` graph type (`fnType` `parametric`/`polar`/`points`/`vector`, or `graphType` `scatter`) additionally needs `"sampler": "builtIn"`, and its parameter is `t` for parametric but **`theta`** for polar. Keep the domain tight around the interesting region — a default zoom shows nothing.

## Template Conventions

⚙ This SKILL ships with optional templates, collected in the “Template Index” table mapping `When | Template`.

⚙ Choose the template whose When matches the current scenario; the template body is stored escaped and must be restored before use.

## Code Style Conventions

⚙ **Indentation in code blocks MUST use actual space characters — tab characters (Tab / \t) are forbidden.** "Indentation" means a definite number of spaces, e.g. 4 spaces; a tab's rendered width is unpredictable across environments and must never appear in Wiki code blocks.

⚙ Before writing code blocks in Wiki output, scan source files under 【Project_Root】 to detect the project's dominant indentation width (2 spaces, 4 spaces, etc.). Generated code blocks MUST match that width. When detection is ambiguous, default to **4 spaces**.

⚙ When extracting code snippets from source files (Demo / Test / source), convert any tab characters to the detected space width (default 4 spaces) so every code block in the Wiki uses real space indentation.

## Accessibility Conventions

⚙ Respect content explicitly marked as non-public in the source code; avoid exposing such content in the Wiki

⚙ Avoid exposing sensitive information in the Wiki, such as passwords, keys, personal information, etc.

## Workflow

<!-- WORKFLOW -->
