#!/usr/bin/env python3
"""Generate skills/SKILL.md — master agent skill index.

Scans the skills/ directory for all first-level subdirectories containing
SKILL.md, reads their metadata, and auto-generates the Sub-Skill Directory
Index table (Section 2). Sections 1, 3, and 4 are hardcoded as literal
templates, ensuring they remain stable across regenerations.

How to add a new sub-skill:
  1. Create skills/<name>/SKILL.md with a `# Title` and `## When to Load`
  2. (Optional) Add the directory name to CATEGORIES below to place it in
     a specific category group; otherwise it appears under "Other".
  3. Run: python skills/generate_skill_index.py
  4. The index table in skills/SKILL.md will update automatically.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Categories: map directory name -> (heading, display order)
# ---------------------------------------------------------------------------
CATEGORIES: dict[str, dict] = {
    # Core Analysis
    "repo-reading":  {"category": "Core Analysis", "order": 10, "scenario": "External repo reading strategy & understanding"},
    "api-docs":      {"category": "Core Analysis", "order": 20, "scenario": "API best-practice discovery from test code → technical docs"},
    "se-analysis":   {"category": "Core Analysis", "order": 30, "scenario": "Software engineering: architecture, class diagrams, sequences, API flows"},
    # Document Creation
    "tutorial":      {"category": "Document Creation", "order": 100, "scenario": "Step-by-step tutorials and getting-started guides"},
    "migration":     {"category": "Document Creation", "order": 110, "scenario": "Migration guides and version upgrade documentation"},
    "comparison":    {"category": "Document Creation", "order": 120, "scenario": "Technology comparison and evaluation documentation"},
    # Operations & Community
    "faq":           {"category": "Operations & Community", "order": 200, "scenario": "FAQ, common issues, and troubleshooting"},
    "contribution":  {"category": "Operations & Community", "order": 210, "scenario": "Contribution guides and community collaboration docs"},
    "adr":           {"category": "Operations & Community", "order": 220, "scenario": "Architecture Decision Records (ADR) and meeting notes"},
    # Quality Assurance
    "review":        {"category": "Quality Assurance", "order": 300, "scenario": "Wiki content review and quality checks"},
    "translation":   {"category": "Quality Assurance", "order": 310, "scenario": "Cross-language document translation and adaptation"},
    "generation":    {"category": "Quality Assurance", "order": 320, "scenario": "Automated Wiki content generation from data or code"},
    # Final Delivery
    "welcome-page":  {"category": "Final Delivery", "order": 400, "scenario": "Replace welcome page with beautiful HTML landing"},
}

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT     = os.path.join(SKILLS_DIR, "SKILL.md")


# ===================================================================
# Hardcoded front-matter (Sections 1, 3, 4 + Section 2 intro)
# ===================================================================
HEADER = """# Cloud Glyph — Agent Skill Index

> **Entry point.** This file is the root index of the agent's skill system.
> The agent MUST read this file first, then strictly follow the Framework
> Execution Pipeline (§3) to produce Wiki content.
>
> *Auto-generated — do not edit manually. Rerun `python skills/generate_skill_index.py` to regenerate.*

---

## 1. Context & Prerequisites

### Template Repository Identity

Cloud Glyph is a **GitHub template repository** ([github.com/Axvser/CloudGlyph](https://github.com/Axvser/CloudGlyph)). The workspace you are currently in is most likely a **repository cloned from that template**. This means the Wiki authoring pipeline defined here applies universally — it is designed for writing documentation for any software repository.

### Root Directory Selection

If you have a user interaction tool available, prompt the user to select a **root directory** that contains the target project(s) to document. All Wiki content you produce must cover the entirety of that root directory. If the user does not specify one, use the workspace root itself.

**You MUST strictly respect `.gitignore`** — any file or directory matched by `.gitignore` rules is off-limits for analysis; do not read or reference them.

### Language Selection (Before Pipeline Starts)

**Default output language is English (`en/`) only.** The agent MUST begin the pipeline with a language selection step:

1. Announce to the user that the Wiki will be written in **English by default**
2. Ask the user (if interaction tools are available) whether they want **additional languages**. Present the available options from `config/languages.json` (e.g., `zh` for Chinese).
3. The user may also directly specify languages in their request (e.g., "Write Wiki in English and Japanese")
4. If the user selects additional languages, set the active language list to `["en", ...selected...]`
5. **All pipeline steps respect this list.** Only the languages in the active list receive content. Skip translation and mirroring for unselected languages.
6. If the user cannot be reached (no interaction), produce **English only**.

### Git Branch Strategy for `skills/`

The `skills/` directory contains agent instruction files, not user project content. Follow this protocol:

1. Isolate `skills/` content in a **local-only branch** named `docs/skills` that is **never pushed** to the user's remote.
2. If the user's repository receives updates (new commits on `main` / `master`), merge those changes into `docs/skills` to keep the skills context current.
3. Under normal circumstances, merging upstream changes into `docs/skills` will **not produce conflicts** since `skills/` does not exist in the upstream. If a conflict arises (e.g., someone created a `skills/` directory in the upstream), **ask the user** how to resolve it.

---

## 2. Wiki Content Authoring Model

The agent writes Wiki pages by working with flat files under `src/CloudGlyph/Assets/Docs/content/`.

### Directory as Node, One `index.md` Per Page

```
content/en/2_Architecture/overview/index.md   →  tree node "Architecture" > "overview"
content/en/2_Architecture/deployment/index.md  →  tree node "Architecture" > "deployment"
```

- **Directory name** is the URL-safe path key.
- **Numeric prefix** (`1_`, `2_`, `2.5_`) controls sort order; it is **stripped** from the displayed title.
- The prefix-stripped directory name becomes the **page title** (e.g. `2_Architecture` → `"Architecture"`).
- A directory containing `index.md` becomes a **tree node**; subdirectories become **children**.
- Encoding: **UTF-8** (required for multi-language).

### Supported Wiki Content Syntax

Based on **AvalonMarkdown v4.0.0** (`markdown-it 14` + `highlight.js 11` + `KaTeX 0.16` + `Mermaid 11` + `plantuml-encoder`), the following syntax is fully supported:

| Category | Syntax / Description |
|---|---|
| **Standard Markdown** | Headings `#`, bold `**`, italic `*`, links `[text](url)`, images `![alt](src)`, lists, blockquotes `>`, horizontal rules `---`, tables, strikethrough `~~text~~` |
| **Math Formulas** | Inline `$E = mc^2$`, block `$$...$$` (KaTeX rendered) |
| **Code Highlighting** | `` ```lang ... ``` `` where `lang` is any highlight.js supported language (VS Code-style theme) |
| **Mermaid Diagrams** | `` ```mermaid ... ``` `` supports: flowchart, sequence, pie, git, class diagrams |
| **PlantUML** | `` ```plantuml ... ``` `` auto-encoded and rendered via PlantUML online service (SVG output, dark/light aware) |
| **Task Lists** | `- [x] done` / `- [ ] todo` (custom styled checkboxes) |
| **Footnotes** | `text[^1]` followed by `[^1]: detail` |
| **Video Embeds** | Direct video files (`.mp4`/`.webm`/`.ogg`/`.mov`/`.avi`/`.mkv`); auto-detected embeds for YouTube, Bilibili, Vimeo |
| **HTML + CSS** | Full inline HTML support including `<style>`, `<div>`, `<span>`, and `@keyframes` animations |
| **Preview Config** | Dynamically adjustable: font size, line height, code language labels, copy button toggle, max code block height |

### Diagram Validation (Mandatory)

Every Mermaid or PlantUML diagram **must** be validated for syntax correctness before the document is committed. Diagrams with syntax errors break rendering for all readers.

| Validation Rule | Mermaid | PlantUML |
|---|---|---|
| **Direction & type** | Verify `flowchart`/`sequenceDiagram`/`classDiagram`/`pie`/`git` is correct for the content | Verify `@startuml`/`@enduml` markers are present and balanced |
| **Arrow syntax** | `->>`/`-->>`/`-x`/`--)` match standard Mermaid arrow rules | `->`/`-->`/`-down->`/`-right->` follow PlantUML arrow convention |
| **Node/participant labels** | All participants referenced in arrows must be declared | All participants must be declared before use |
| **Bracket/brace balance** | `{}` `[]` `()` are properly paired — no unclosed blocks | `{}` `[]` `()` are properly paired — no unclosed blocks |
| **Keyword casing** | Mermaid keywords (`participant`, `loop`, `alt`, `opt`, `rect`) are lowercase | PlantUML keywords (`participant`, `actor`, `boundary`, `note`, `alt`) are lowercase |
| **Indentation** | Block structures (`loop`/`alt`/`opt`) have consistent indentation to mark scope | Block structures (`alt`/`else`/`group`/`loop`) have consistent indentation |
| **No ambiguous characters** | Avoid unescaped `"` `(` `)` `[` `]` inside labels — use `()` or `[]` wrapping consistently | Avoid special characters in labels without proper escaping |

**Before writing a diagram**, the agent MUST mentally trace the diagram logic to ensure all connections are valid. **After writing**, the agent MUST re-read the code block as if parsing it and confirm every rule above passes.

### Multi-Language

- **Default is English-only** (`en/`). Additional languages are opt-in — see §1 (Language Selection).
- Language config source file: `config/languages.json` — lists all available language codes
- To add a language, create `content/{code}/` with at least one `index.md`
- **Never manually edit** `content/languages_index.json` or `content/*/tree.json` (build-generated, listed in `.gitignore`)
- When multiple languages are active, directory structures must be mirrored across all active languages

### Reference

For the full project structure, startup flow, and theme mechanism, see the root [`SKILL.md`](../SKILL.md).

---

## 3. Framework Execution Pipeline

This is the **mandatory execution sequence**. The agent MUST follow steps 1-8 in order. Pre-insertion hooks and post-insertion hooks may be injected around the core steps based on the project's tech stack or user request.

```
┌─────────────────────────────────────────────────────────────┐
│                    PRE-INSERTION HOOKS                      │
│  (hot-pluggable rule sets auto-injected by tech stack)      │
│  e.g., .NET conventions, Python packaging, JS toolchain     │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Git Status Confirmation                            │
│  Step 2: Project File Analysis (read content, not names)    │
│  Step 3: Test & Demo Discovery (Demo > Test priority)       │
│  Step 4: Quick Start Writing (per module, from Demo/Test)   │
│  Step 5: Software Engineering Analysis (with src citation)  │
│  Step 6: API Deep Dive (semantic + full-code + security)    │
│  Step 7: Review & Quality Gate (coverage, truth, syntax)    │
│  Step 8: Welcome Page (beautiful HTML landing)              │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    POST-INSERTION HOOKS                      │
│  (pluggable quality processes, e.g., final audit,           │
│   terminology alignment, cross-reference check)             │
└─────────────────────────────────────────────────────────────┘
```

### Pre-Insertion Hooks (Hot-Pluggable)

The agent should analyze the project's tech stack and **auto-inject** relevant rule sets before executing the standard steps. Use the **Reference Index (§8)** to look up documentation conventions for the detected tech stack and apply them throughout the pipeline.

The agent checks the root for well-known signature files and loads the appropriate convention set:

| Detection File(s) | Tech Stack | Convention Reference |
|---|---|---|
| `.slnx` / `.csproj` / `.vbproj` / `.fsproj` | .NET (C#, VB, F#) | §8 — .NET |
| `Cargo.toml` | Rust | §8 — Rust |
| `package.json` + `tsconfig.json` | TypeScript | §8 — TypeScript / JavaScript |
| `package.json` (no `tsconfig.json`) | JavaScript / Node.js | §8 — TypeScript / JavaScript |
| `pyproject.toml` / `setup.py` | Python | §8 — Python |
| `go.mod` | Go | §8 — Go |
| `CMakeLists.txt` / `Makefile` + `.c`/`.cpp` | C / C++ | §8 — C / C++ |
| `pom.xml` / `build.gradle` | Java | §8 — Java |
| None of the above | Generic | §8 — Generic / Unknown |

**User-specified**: the user may also directly request specific rule sets or conventions to be applied, overriding auto-detection.

---

## 4. Sub-Skill Directory Index

Sub-skills are organized into independent directories by scenario. The agent MUST
**only read a sub-skill's `SKILL.md` when the user's request matches that
scenario** — never pre-load them.
"""

FOOTER = """

---

## 5. Framework Step Details

### Step 1: Git Status Confirmation

Cloud Glyph is a GitHub template repository. Confirm with the user whether the workspace is a fresh clone from the template or an existing project. Based on this:

- If fresh from template: proceed normally — no Git strategy needed beyond the `docs/skills` branch rule (§1).
- If an existing project: ensure `skills/` is on a local-only `docs/skills` branch as specified in §1. **If the branch does not exist, create it now.**
- Check whether the user's repository has recent upstream changes. If so, consider merging them into `docs/skills` before starting the pipeline to ensure the skills context is current.

### Step 2: Project File Analysis (Read Content, Not Names)

Analyze the root directory's structure by **reading actual file contents**, not by guessing from directory/file names. Directory names can be misleading (e.g., `src/Models` might contain DTOs, not domain models).

**Procedure** (token-efficient):
1. **Read entry point files** first — `Program.cs`, `main.rs`, `index.ts`, `main.py`, `cmd/` — to understand the application bootstrap
2. **Read project definition files** — `.csproj`, `Cargo.toml`, `package.json`, `pyproject.toml` — to understand dependencies, target frameworks, and build configuration
3. **Read key configuration files** — `appsettings.json`, `tsconfig.json`, `.env.example`, `docker-compose.yml` — to understand runtime setup
4. **Scan the directory tree** (without reading every file) to build a module map; read only one representative file per directory to confirm its purpose
5. **Produce a module responsibility map** listing each significant directory, its confirmed purpose (based on content), and its key files

**During this step, consult §8 (Reference Index)** for tech-stack-specific documentation conventions that will guide how you document the project.

**Rules:**
- ❌ Never say "X directory is for Y" without reading at least one file in that directory
- ✅ Read fewer, more strategic files rather than bulk-scanning everything
- ✅ If a directory contains only generated/cache files (node_modules, bin, obj, .git), skip it

### Step 3: Test & Demo Discovery (Demo > Test Priority)

Find and analyze how the project's APIs are actually used. The priority order is:

1. **Demo projects/examples** (`samples/`, `examples/`, `demo/`, `*-demo`) — **highest priority**. These show the **intended public usage** of the API. Examine them first.
2. **Test projects** (`*Test*/`, `*Spec*/`, `tests/`) — second priority. Note that some APIs may only be accessible in tests due to `InternalsVisibleTo` or test-specific build configurations. **Cross-reference with demo code** before concluding an API's public surface.
3. **Direct source code analysis** — only when neither demo nor test exists for a given module. If you must resort to this, **document must explicitly note** that no example usage was found.

**Output:** For each module/feature, produce:
- The API signatures found (from demos or tests)
- Real invocation examples (verbatim from demo/test code)
- Which source the example came from (demo project path or test file path)
- The confidence level: `demo` / `test` / `inferred-from-source`

### Step 4: Quick Start Writing (Per Module, from Demo/Test)

For each functional module identified in Step 2, write a **Quick Start** guide:

1. **Scope the module** — what it does, its main class(es), its key capability
2. **Extract a runnable example** from the demo or test code found in Step 3
3. **Reconstruct the setup steps** — installation, configuration, initialization code
4. **Walk through the example step by step** — what each line does, what to expect
5. **Include expected output** — if the demo/test has assertions, show what the correct result looks like
6. **Link to the full demo/test file** for readers who want the complete picture

**Format:** Place each module's Quick Start under `content/en/{Project}/quickstart/{module}/`.

### Step 5: Software Engineering Analysis (with Source Citation)

Produce a rigorous software engineering analysis. Use **Mermaid class diagrams** for inheritance and type relationships, **Mermaid sequence diagrams** for execution flows, and **Mermaid flowcharts** for architectural overviews.

**Mandatory rules:**
- ✅ **Every code snippet** in the analysis must come from an **actual file** in the target repository. After including a code snippet, you MUST be able to state which file and which line range it came from.
- ✅ **Every diagram** must pass the Diagram Validation checklist (§2).
- ❌ **Never fabricate** method signatures, class names, or execution flows.
- ✅ When a code snippet is **inferred** (no demo/test available, derived from source reading), **the document must explicitly note this** with a callout like: `> **Note:** No example usage found for this API. The following is inferred from source code analysis.`
- ✅ Use **KaTeX formulas** for algorithmic complexity or domain-specific calculations where applicable.

**Standard pages** (under `content/{lang}/{Project}/architecture/`):

| Page | Content | Rendering |
|---|---|---|
| `01_project_structure.md` | Module map, dependency graph | Mermaid flowchart + tables |
| `02_class_hierarchy.md` | Core types, interfaces, inheritance | Mermaid class diagram |
| `03_startup_flow.md` | Bootstrap sequence, DI registration | Mermaid sequence diagram |
| `04_request_lifecycle.md` | Request → response processing pipeline | Mermaid sequence + flowchart |
| `05_data_flow.md` | State changes, event-driven patterns | Mermaid flowchart |
| `06_dependencies.md` | External dependencies and integration points | Tables + arch diagram |

### Step 6: API Deep Dive (Semantic + Full-Code + Security)

For every public API identified in Steps 2-3, produce a comprehensive reference page that goes beyond signature documentation to cover:

**Semantic level:**
- **What problem does this API solve?** — the higher-level intent, not just the method name
- **When to use it vs. alternatives** — decision guidance for the reader
- **Preconditions and postconditions** — what must be true before calling, what is guaranteed after

**Full-code level:**
- **Complete method signature** with all parameters, generics, and return type
- **Parameter semantics** — not just types, but what each parameter means in the domain
- **Exception table** — every exception that can be thrown, and under what conditions
- **Overload resolution** — if multiple overloads exist, explain when each is appropriate

**Security coverage:**
- **Authentication/Authorization requirements** — does this API require specific roles or permissions?
- **Input validation** — what sanitization or validation does the API perform? What should the caller do?
- **Rate limiting / throttling** — if applicable, document limits
- **Data sensitivity** — does this API handle PII, secrets, or other sensitive data?
- **Safe defaults** — document default values and whether they are secure by default
- **Audit logging** — does the API log calls for security audit?

**Output location:** `content/{lang}/{Project}/api/{Module}/` — one page per major class or API surface.

### Step 7: Review & Quality Gate

This is the **final mandatory step** before delivery. The agent MUST perform all checks below and correct any issues found. If the user's request matches the "Review" scenario only, this step runs standalone.

**Checklist:**

- [ ] **Module coverage audit** — cross-reference the list of modules identified in Step 2 against the pages written in Steps 4-7. Every module must be represented. If any module was missed, flag it and write its documentation.
- [ ] **Code truth verification** — every code block in non-diagram sections (Quick Start, API Deep Dive) must be checked: open the actual source file and confirm every method name, parameter, and type used actually exists with the documented signature. **No fabricated code**.
- [ ] **Diagram syntax validation** — re-validate every Mermaid and PlantUML diagram against the Diagram Validation table in §2. No syntax errors permitted.
- [ ] **Formula validation** — check all KaTeX `$...$` and `$$...$$` blocks for balanced delimiters and correct LaTeX syntax.
- [ ] **Link integrity** — all `[text](path)` internal references resolve to existing Wiki pages.
- [ ] **Structural consistency** — numeric prefixes are correct, `index.md` exists in every directory.
- [ ] **Multi-language parity** — if additional languages were selected in §1, verify all pages exist in every active language directory. Skip this check for unselected languages.

**Pre-commit flow:**
1. Run through the checklist
2. For any failed item, apply corrections immediately
3. Re-check after corrections
4. Only when all items are ✅, mark the quality gate as passed

### Step 8: Welcome Page — Beautiful HTML Landing

Replace the generic `0_Welcome/index.md` with a project-specific, visually rich landing page using Cloud Glyph's inline HTML + CSS capabilities. This step **must** be loaded from `welcome-page/SKILL.md` for full instructions and templates.

**Core requirements:**
- **Zero fabricated content** — every project name, feature, and description must come from Steps 2-6
- **Reuse Cloud Glyph's battle-tested CSS template** — 4 animations (`float`, `shimmer`, `pop-in`, `glow-pulse`), card-based responsive layout, gradient text effects
- **3-step user workflow** — adapted to the project's actual use case (install → configure → use)
- **Feature grid** — max 8 cards, each mapping to a verified module or capability
- **Footer badges** — 3-4 key project attributes with glow-dot decorations
- **Staggered entrance animations** — `animation-delay` cascading across cards
- **Per-language output** — write `content/{lang}/0_Welcome/index.md` for every language in the active language list (§1). Default is English only.

**Source material for content:**
- Project name → Step 2 (build/config file)
- Tagline → Step 2 (project overview)
- Step workflow → Step 4 (Quick Start flow)
- Feature cards → Steps 3, 5, 6 (verified capabilities)
- Footer badges → Step 2 (license, platform, dependencies)

**Output location:** `content/{lang}/0_Welcome/index.md`

---

## 6. Post-Insertion Hooks (Pluggable)

After the 8-step pipeline completes, the agent may inject additional processes based on the project's characteristics or user request. These are **optional but recommended**:

| Hook | Trigger | Description |
|---|---|---|
| **Terminology Alignment** | Multi-language projects (languages selected in §1) | Scan non-English pages for inconsistent translations of key terms; align against a glossary |
| **Cross-Reference Validation** | Complex multi-module projects | Check that pages in different modules link to each other where dependencies exist |
| **Changelog Generation** | Git history available | Generate a release notes page from commit history between tags |
| **README Export** | Root `README.md` exists | Optionally generate an `index.md` in the Wiki root that mirrors the `README.md` |
| **Full-Text Search Index** | User request | Build a search-keyword index page mapping terms to the pages where they appear |
| **Custom User Request** | User specifies | Any additional processing the user requests |

---

## 7. Usage Rules

1. Always start from **this file** — understand context (§1), content model (§2), and the pipeline (§3)
2. **Execute the pipeline strictly in order** (§5, Steps 1-8) — do not skip steps unless the user explicitly excludes one
3. Respect pre-insertion hooks (§3) by detecting the project's tech stack before starting Step 1
4. After completing all 8 steps, apply any relevant post-insertion hooks (§6)
5. **Notify the user** at each step boundary — announce which step you are starting and which comes next
6. After completing the task, **do NOT retain** sub-skill context for unrelated future tasks
7. New sub-skills can be added by creating a directory with `SKILL.md` and running the generator

---

## 8. Reference Index: Documentation Conventions by Tech Stack

This index helps the agent optimize Wiki content for different technology stacks. When the Pre-Insertion Hooks (§3) detect a specific tech stack, the agent SHOULD consult this table to apply the appropriate documentation conventions.

### Detection Key

| Signature Files | Tech Stack | Conventions Apply |
|---|---|---|
| `.slnx` / `.sln` / `.csproj` / `.vbproj` / `.fsproj` | .NET (C#, VB, F#) | ✅ |
| `Cargo.toml` | Rust | ✅ |
| `package.json` + `tsconfig.json` | TypeScript | ✅ |
| `package.json` (no `tsconfig.json`) | JavaScript / Node.js | ✅ |
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python | ✅ |
| `go.mod` | Go | ✅ |
| `CMakeLists.txt` / `Makefile` (with `.c`/`.cpp`/`.h` sources) | C / C++ | ✅ |
| `pom.xml` / `build.gradle` | Java (Maven / Gradle) | ✅ |
| `Gemfile` | Ruby | ✅ |
| `*.swift` + `Package.swift` | Swift | ✅ |
| None of the above detected | Generic / Unknown | ✅ (fallback defaults) |

### .NET (C# / VB / F#)

| Convention | Guidance |
|---|---|
| **API doc style** | XML doc comments (`/// <summary>`, `<param>`, `<returns>`, `<exception>`) are standard. Document all `public` types and members. |
| **Visibility awareness** | `internal` types are not part of public API. `private protected` is implementation detail. Check for `[EditorBrowsable(EditorBrowsableState.Never)]` and `[Obsolete]` attributes. |
| **Test accessibility** | Watch for `InternalsVisibleTo` in `.csproj` or `AssemblyInfo.cs` — APIs used only in tests via `[InternalsVisibleTo]` are NOT public API. |
| **Async pattern** | Document `Task` / `Task<T>` / `ValueTask<T>` return types explicitly. Indicate whether methods support cancellation via `CancellationToken`. |
| **Nullability** | Respect nullable reference types (`string?` vs `string`). Document nullability contracts in the API reference. |
| **Dependency Injection** | Document which services should be registered in DI and with what lifetime (`AddSingleton`, `AddScoped`, `AddTransient`). |
| **Configuration** | Document `IOptions<T>` / `IConfiguration` binding patterns if the library uses .NET configuration. |
| **Naming conventions** | Use `PascalCase` for public members, `camelCase` for parameters, `_camelCase` for private fields. Document any deviation. |

### Rust

| Convention | Guidance |
|---|---|
| **API doc style** | Rustdoc (`///`, `//!`) is standard. Document all `pub` items. Provide `# Examples` blocks in doc comments. |
| **Module hierarchy** | Document the `mod.rs` / `lib.rs` structure. Show the re-export tree (`pub use`). |
| **Traits** | Document required vs provided trait methods. Show blanket implementations. Note trait bounds for generic types. |
| **Error handling** | Document `Result<T, E>` return types. Show which error variants are possible. If the crate uses `thiserror` or `anyhow`, document the error pattern. |
| **Feature flags** | Document `Cargo.toml` feature flags and their effects. Show `#[cfg(feature = "...")]` gated APIs. |
| **Async** | If using `tokio` / `async-std`, document which runtime is required and spawning patterns. |
| **Naming conventions** | `snake_case` for functions/methods, `PascalCase` for types/traits, `SCREAMING_SNAKE_CASE` for constants. |

### TypeScript / JavaScript

| Convention | Guidance |
|---|---|
| **API doc style** | JSDoc / TSDoc (`/** */`) is standard. Document all exported functions, classes, and interfaces. |
| **Module system** | Document whether the project uses ESM (`import`/`export`) or CJS (`require`/`module.exports`). Note `"type": "module"` in `package.json`. |
| **Type exports** | Distinguish `interface` vs `type` aliases. Document generic type parameters. Note `readonly` and optional (`?`) members. |
| **Async patterns** | Document `Promise<T>` and `async/await` usage. Note callback-style APIs if they exist. |
| **Configuration** | Document `tsconfig.json` path aliases (`paths`), `"strict"` mode implications. |
| **Package exports** | Document the `"exports"` field in `package.json` — which subpaths are public API. |
| **Testing** | Note the test framework (Jest, Vitest, Mocha). Document test runner configuration if relevant to API usage. |
| **Naming conventions** | `camelCase` for functions/variables, `PascalCase` for classes/types/interfaces, `UPPER_CASE` for constants. |

### Python

| Convention | Guidance |
|---|---|
| **API doc style** | Docstrings (`""" """`) are standard. NumPy/Google-style or Sphinx-compatible formats are common. Document all public modules, classes, and functions. |
| **Module visibility** | `_single_underscore` prefix = internal (not public API). `__dunder__` = special methods. Document `__all__` exports in `__init__.py`. |
| **Type hints** | Use `def foo(x: int) -> str:` style in modern Python. Document `Optional`, `Union`, `Protocol`, `TypedDict` types. |
| **Async patterns** | Document `async def` / `await` usage. Note if `asyncio` or `trio` is required. |
| **Dependency management** | Document `pyproject.toml` / `requirements.txt` dependencies. Note optional extras (`[extra]` in `pyproject.toml`). |
| **Package structure** | Document the module hierarchy through `__init__.py` re-exports. Show the public surface of the package. |
| **Naming conventions** | `snake_case` for functions/methods/variables, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants. |

### Go

| Convention | Guidance |
|---|---|
| **API doc style** | `godoc` comments (`// FunctionName ...`). Document all exported identifiers. Include runnable `Example` functions. |
| **Interface conventions** | Document which interfaces the package expects consumers to implement. Show the `io.Reader`/`io.Writer`-style composition patterns. |
| **Error handling** | Document sentinel errors (`var ErrX = errors.New(...)`) and error types. Show `errors.Is` / `errors.As` patterns. |
| **Context** | Document functions that take `context.Context` as first parameter. Explain cancellation and deadline behavior. |
| **Goroutine safety** | Document whether types are safe for concurrent access. Note mutex or channel synchronization patterns. |
| **Naming conventions** | `camelCase` for unexported, `PascalCase` for exported. `Acronyms` are all-caps (`HTTP`, `URL`). |

### C / C++

| Convention | Guidance |
|---|---|
| **API doc style** | Doxygen (`/** */` or `///`) is standard for C++. Plain `/* */` comments are common in C. |
| **Header/Source separation** | Document `.h` / `.hpp` headers as the public API surface. `.c` / `.cpp` files are implementation details unless they define public symbols. |
| **Memory management** | Document ownership semantics: who allocates, who frees. Note `malloc`/`free`, `new`/`delete`, `unique_ptr`/`shared_ptr` patterns. |
| **Preprocessor** | Document `#define` macros, `#ifdef` feature gates, and compile-time configuration options. |
| **ABI / Linkage** | Note `extern "C"` for C-compatible APIs. Document `dllexport` / `dllimport` if applicable. |
| **Naming conventions** | `snake_case` (C/STL) or `PascalCase` (many C++ projects). Document the project's specific convention. |

### Java (Maven / Gradle)

| Convention | Guidance |
|---|---|
| **API doc style** | Javadoc (`/** */`) is standard. Document all `public` and `protected` members. Include `@param`, `@return`, `@throws` tags. |
| **Package visibility** | Package-private (no access modifier) is not public API. `public` is the public surface. |
| **Annotations** | Document relevant annotations: `@Override`, `@Deprecated`, `@Nullable`/`@NonNull`, `@Inject`, `@Bean`, `@Service`. |
| **Build configuration** | Document Maven (`pom.xml`) or Gradle (`build.gradle`) coordinates for dependency inclusion. |
| **Module system** | If using Java 9+ modules (`module-info.java`), document which packages are exported. |
| **Naming conventions** | `PascalCase` for classes/interfaces, `camelCase` for methods/fields, `SCREAMING_SNAKE_CASE` for constants. |

### Generic / Unknown (Fallback)

When the tech stack cannot be determined from well-known signatures, apply these universal conventions:

- **Public API surface**: Document whatever is exported / `public` at the module/package level
- **Entry points**: Look for standard bootstrap entry points and document startup flow
- **Configuration**: Document configuration files, environment variables, CLI arguments
- **Testing**: Document the test framework and how to run tests regardless of language
- **Dependencies**: Document third-party dependencies and their roles
- **Naming**: Observe and document the project's actual naming convention (do not enforce one)

### Usage

1. During **Pre-Insertion Hooks** (§3), detect the tech stack from signature files
2. Consult this index for the matching tech stack conventions
3. Apply these conventions throughout Steps 2-7 of the pipeline
4. If multiple tech stacks are detected (e.g., a .NET backend + TypeScript frontend), apply each stack's conventions to the relevant modules
"""


# ===================================================================
# Utility helpers
# ===================================================================

def discover_sub_skills(skills_dir: str) -> list[str]:
    """Return sorted list of directory names under skills_dir that contain SKILL.md."""
    dirs = []
    for entry in sorted(os.listdir(skills_dir)):
        full = os.path.join(skills_dir, entry)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "SKILL.md")):
            dirs.append(entry)
    return dirs


def read_title(skill_md: str) -> str:
    """Extract the first `# Title` from a SKILL.md file."""
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^#\s+(.+)", line)
                if m:
                    return m.group(1).strip()
    except OSError:
        pass
    return "Untitled"


def read_keywords(skill_md: str) -> str:
    """Extract trigger keywords from the sub-skill."""
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return ""

    # Look for sections that list trigger scenarios: "When to Load", "Applicability"
    section_names = r"(?:When to Load|Applicability)"

    # Try to find one of these sections
    m = re.search(
        rf"##\s+{section_names}\s*\n(.*?)(?:\n##\s|\Z)",
        text,
        re.DOTALL,
    )
    if not m:
        # Fallback: look for quoted phrases anywhere in the document
        quoted = re.findall(r'"([^"]*)"', text)
        if quoted:
            return ", ".join(quoted[:5])
        return ""

    block = m.group(1).strip()
    # Collect quoted strings first
    keywords = re.findall(r'"([^"]*)"', block)
    if keywords:
        return ", ".join(keywords[:5])

    # Fallback: pick first bullet items
    bullets = []
    for line in block.splitlines():
        line = line.strip().lstrip("- *")
        if line and not line.startswith("#"):
            bullets.append(line)
    return ", ".join(bullets[:5])


def get_scenario(dir_name: str) -> str:
    """Return the scenario description for a given sub-skill directory name."""
    entry = CATEGORIES.get(dir_name)
    if entry:
        return entry["scenario"]
    return dir_name.replace("-", " ").title()


# ===================================================================
# Index table generation
# ===================================================================

def build_category_tables(dirs: list[str]) -> str:
    """Group discovered sub-skills by category and produce markdown tables."""
    # Collect entries
    entries: list[tuple[str, str, str, str]] = []  # (category_name, dir_name, scenario, keywords)

    for d in dirs:
        skill_path = os.path.join(SKILLS_DIR, d, "SKILL.md")
        info = CATEGORIES.get(d)
        cat_name = info["category"] if info else "Other"
        scenario = get_scenario(d)
        keywords = read_keywords(skill_path)
        entries.append((cat_name, d, scenario, keywords))

    # Sort by category order, then directory name
    def sort_key(e):
        info = CATEGORIES.get(e[1])
        cat_order = info["order"] if info else 999
        return (cat_order, e[1])

    entries.sort(key=sort_key)

    # Group by category
    groups: dict[str, list[tuple[str, str, str]]] = {}
    for cat_name, d, scenario, keywords in entries:
        groups.setdefault(cat_name, []).append((d, scenario, keywords))

    # Render
    parts = []
    for cat_name in [
        "Core Analysis",
        "Document Creation",
        "Operations & Community",
        "Quality Assurance",
        "Final Delivery",
        "Other",
    ]:
        if cat_name not in groups:
            continue
        parts.append(f"### {cat_name}\n")
        parts.append("| Path | Scenario | Trigger Keywords |")
        parts.append("|---|---|---|")
        for d, scenario, keywords in groups[cat_name]:
            path = f"`skills/{d}/SKILL.md`"
            kw = keywords if keywords else "(see sub-skill for details)"
            scenario = scenario.replace("|", "\\|") if scenario else "—"
            parts.append(f"| {path} | {scenario} | {kw} |")
        parts.append("")

    return "\n".join(parts)


# ===================================================================
# Main
# ===================================================================

def main() -> int:
    dirs = discover_sub_skills(SKILLS_DIR)
    if not dirs:
        print("No sub-skill directories found under", SKILLS_DIR)
        return 1

    table = build_category_tables(dirs)
    content = HEADER.strip() + "\n\n" + table.strip() + "\n" + FOOTER.strip() + "\n"

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(content)

    count = len(dirs)
    print(f"✅ Regenerated {OUTPUT}")
    print(f"   Found {count} sub-skill{'s' if count > 1 else ''}: {', '.join(dirs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
