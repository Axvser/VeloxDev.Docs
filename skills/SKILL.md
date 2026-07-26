# Cloud Glyph Skills

## Responsibility

This skill system provides an AI Agent with a Wiki documentation authoring workflow. You must strictly follow this pipeline to produce documentation that meets the specification.

## Variable Conventions

> **Wiki_Root** — The root directory for output documents (the parent of `skills/`). The Agent may only create, modify, or delete documents under Wiki_Root.

> **Deploy_Mode** — Deployment mode:
> - `nested`: Wiki repo is a subdirectory inside a project; Agent should document the parent project (excluding the Wiki itself)
> - `standalone`: Wiki repo is used independently; Agent cannot auto-discover the project and must ask the user

> **Solution_Root** — The solution root of the project being documented
> - `nested` mode: Auto-discovered by Agent (parent of Wiki_Root)
> - `standalone` mode: Provided by the user

> **Project_List** — The list of projects being documented. In `nested` mode, exclude the Wiki repo's own projects (i.e. CloudGlyph project)

> **Language_List** — The language scope of the Wiki. The Agent should determine the user's desired languages in Step 1 via interactive tools or direct inquiry, then verify availability against `languages.json`. Unsupported languages should be recorded and reported at the end without interrupting the pipeline.

## Content Model

The Wiki uses a "directory-as-page" organization. The Agent must follow two core rules:

> **Rule 1: Directory name = navigation structure** — Each Wiki page corresponds to a directory. Directory names use `{number}_` prefix for ordering, e.g. `0_Welcome`, `01_project_structure`. The Agent must use appropriate numeric prefixes when creating directories.

> **Rule 2: Content file convention** — Each directory must have exactly one `index.md` file as the page content. Directories may contain child subdirectories for sub-pages (which also follow Rule 1).

> **Rule 3: Directory name must match the target language** — Directory names must be in the language of the content, not in English. For example, if `Language_List = ["zh"]`, use `0_欢迎` instead of `0_Welcome`, `1_快速入门` instead of `1_quickstart`, `2_API参考` instead of `2_api`, `3_架构分析` instead of `3_architecture`. Exception: Proper nouns and brand names (e.g. "VeloxDev", "MVVM", "AOP") that are universally recognized in their original form.

### Content Organization (Dimension-Based Decision)

The Wiki uses a "directory-as-page" organization. The Agent **must not** decide the structure based on project count alone. Instead, determine the **nature of the target** being documented:

#### Decision Rule

> **Is the target a self-contained framework, class library, or product?** (e.g. WPF, Entity Framework, VeloxDev, React, a NuGet library, a game engine, etc.)

| If... | Then... |
|---|---|
| **Yes** — it is a cohesive product/framework/library | Always use **Dimension** organization — the outermost structure is **fixed** (see below). Features discovered via Module Discovery are placed as sub-pages under each dimension. |
| **No** — the solution is a collection of independent apps/tools/services | **Ask the user** how to organize. Present the available options and let them decide. Do not guess. |

> **Rationale:** A framework with 40+ sub-projects is still one thing (the framework). A solution with 2 completely independent web apps is two separate things. Count alone cannot distinguish these cases.

#### Dimension Organization (for frameworks, libraries, products)

The outermost directory structure is **strictly fixed** — not determined by discovered categories. It always contains exactly these four dimensions:

| # | Directory | Purpose |
|---|---|---|
| 0 | `0_Welcome/` | Welcome page — project overview summary |
| 1 | `1_QuickStart/` | Quick Start — getting-started code samples for each feature |
| 2 | `2_API/` | API Reference — full API reference for each feature |
| 3 | `3_SE_Analysis/` | SE Analysis — software engineering analysis (file structure, design patterns, data flow, complexity) |

Then `{last_number}_Copyright/` (e.g. `4_Copyright/`) as the final page.

**Rules:**

- Each dimension directory is directly under `content/{lang}/` — no `{ProductName}/` or `{SolutionName}/` or `{Category}/` wrapper
each **feature** (discovered via Demo→Test→Source) gets its own sub-directory (e.g. `0_FeatureA/`, `1_FeatureB/`, `2_FeatureC/`), each containing `index.md`
- Under `3_SE_Analysis/`: the inner structure follows the SE Analysis spec — `0_file_structure/`, `1_feature_map/`, `2_design_patterns/{Feature}/`, `3_data_flow/{Feature}/`, `4_complexity/{Feature}/`
- Copyright is always the last number in the language's content tree

```
# Example: Dimension organization (framework / library / product)
# Outer: fixed dimensions — Welcome / QuickStart / API / SE_Analysis / Copyright
# Inner: per-feature sub-pages under each dimension
content/en/
├── 0_Welcome/                         ← Fixed dimension: Welcome
│   └── index.md
├── 1_QuickStart/                      ← Fixed dimension: Quick Start
│   ├── index.md                       ← Overview (optional)
├── 0_FeatureA/              ← Feature A
│   │   └── index.md
│   ├── 1_FeatureB/             ← Feature B
│   │   └── index.md
│   ├── 2_FeatureC/             ← Feature C
│   │   └── index.md
│   └── ...                     ← More features...
├── 2_API/                       ← Fixed dimension: API Reference
│   ├── index.md                 ← Overview (optional)
│   ├── 0_FeatureA/              ← Feature A
│   │   └── index.md
│   ├── 1_FeatureB/              ← Feature B
│   │   └── index.md
│   └── ...                      ← More features...
├── 3_SE_Analysis/               ← Fixed dimension: SE Analysis
│   ├── index.md                 ← Overview
│   ├── 0_file_structure/        ← Repository layout
│   │   └── index.md
│   ├── 1_feature_map/           ← Feature responsibility map
│   │   └── index.md
│   ├── 2_design_patterns/       ← Design patterns
│   │   ├── index.md
│   │   ├── 0_FeatureA/          ← Feature A
│   │   │   └── index.md
│   │   └── 1_FeatureB/          ← Feature B
│   │       └── index.md
│   ├── 3_data_flow/             ← Data flow / sequence diagrams
│   │   ├── index.md
│   │   ├── 0_FeatureA/
│   │   │   └── index.md
│   │   └── 1_FeatureB/
│   │       └── index.md
│   └── 4_complexity/            ← Complexity analysis
│       ├── index.md
│       ├── 0_FeatureA/
│       │   └── index.md
│       └── 1_FeatureB/
│           └── index.md
└── 4_Copyright/                       ← Copyright (last number)
	└── index.md
```

#### Per-Project Organization (only when user explicitly chooses this)

If the user opts for per-project structure (e.g. a solution containing multiple independent apps), it is the **same dimension organization** but wrapped in a `{Project}/` directory. Each project gets its own copy of the four fixed dimensions:

```
content/en/
├── 0_Welcome/                         ← Global Welcome (project overview)
│   └── index.md
├── 1_MyApp/                           ← Project wrapper
│   ├── index.md                       ← Project overview
│   ├── 0_QuickStart/                  ← Fixed dimension: Quick Start
│   │   ├── index.md
│   │   ├── 0_FeatureA/
│   │   │   └── index.md
│   │   └── 1_FeatureB/
│   │       └── index.md
│   ├── 1_API/                         ← Fixed dimension: API Reference
│   │   ├── index.md
│   │   ├── 0_FeatureA/
│   │   │   └── index.md
│   │   └── 1_FeatureB/
│   │       └── index.md
│   ├── 2_SE_Analysis/                 ← Fixed dimension: SE Analysis
│   │   ├── index.md
│   │   ├── 0_file_structure/
│   │   │   └── index.md
│   │   ├── 1_feature_map/
│   │   │   └── index.md
│   │   ├── 2_design_patterns/
│   │   │   ├── 0_FeatureA/
│   │   │   │   └── index.md
│   │   │   └── 1_FeatureB/
│   │   │       └── index.md
│   │   ├── 3_data_flow/
│   │   │   └── ...
│   │   └── 4_complexity/
│   │       └── ...
│   └── 3_Copyright/                   ← Copyright (last number for this project)
│       └── index.md
├── 2_MyLib/                           ← Another project wrapper
│   ├── index.md
│   ├── 0_QuickStart/
│   │   └── ...
│   ├── 1_API/
│   │   └── ...
│   ├── 2_SE_Analysis/
│   │   └── ...
│   └── 3_Copyright/
│       └── index.md
└── ...
```
```

## Code Authenticity Priority (CRITICAL)

Every code snippet in Wiki documentation **must** come from a real source. The Agent must follow this strict priority hierarchy when discovering API usage examples:

> **Priority 1 (Highest) — Demo/Example projects**
> Scan `Examples/` or `samples/` directories for real-world usage. These show the intended top-level API surface and the most idiomatic patterns.
> 
> **Priority 2 — Unit Tests**
> Extract usage patterns from test files (e.g. `*Test*.cs`, `*Spec*.cs`). Tests exercise real APIs with real parameters and edge cases.
>
> **Priority 3 (Fallback) — Source code self-discovery**
> Only when no Demo or Test exists for a module: read the source code interfaces, extract method signatures, and construct minimal usage examples. These must be explicitly marked as *inferred* if not verified against an actual call site.
>
> **Rule 1 (Mandatory full read):** If a module has Demo code (Priority 1), the Agent **must read ALL source files** under that module's Demo directory in full. Do not skim just a few lines. The documentation must reflect every usage pattern shown in the Demo — initialization, configuration, core API call chains, error handling, and edge cases. Likewise, if no Demo exists but tests exist, the Agent must read all test files in full.
>
> **Rule 2 (No fabrication):** If a code block contains a class name, method name, or API call that does not exist in the codebase, it is a **fabrication** and must be fixed before the Review step. The Agent must verify every referenced symbol by searching the actual source files.

## Code Styling

The SKILL system imposes **no requirements** on code indentation or formatting style in documentation code blocks. The Agent should follow the indentation style already present in the project's own source files (tabs, spaces, etc.), or use whichever produces readable, consistent output.

## Workflow

> 0.Start

> 1.Deploy mode detection and variable confirmation

> 2.Tech stack analysis

> 3.Constraint loading

> 4.Module discovery

### Content Writing Phase (Steps 5-8)

Pages are written in **reader consumption order**: Quick Start → APIs → Architecture → Copyright. This order ensures that earlier pages can reference later ones where appropriate.

#### ⚡ Per-Module Micro-Loop (Steps 5→6→7)

When `Project_List` contains **multiple modules**, Steps 5→6→7 execute as a **micro-loop per module**, not as three batch passes across all modules. This prevents context overload and ensures each module's API and analysis chapters benefit from the module-specific Quick Start written just before them.

**Pre-step (mandatory per module):** Before entering the micro-loop, the Agent **must read all** Demo/Test source files for that module in full to form a complete understanding of its API surface. Do not begin writing after reading only a subset of files.

**Correct pattern — per-module micro-loop:**
```
For Module A:
  Pre-step: Read all Demo/Test source files for Module A in full
  5.Write【Quick Start for Module A】
  6.Write【APIs for Module A】
  7.Write【SE Analysis for Module A】
For Module B:
  Pre-step: Read all Demo/Test source files for Module B in full
  5.Write【Quick Start for Module B】
  6.Write【APIs for Module B】
  7.Write【SE Analysis for Module B】
... (repeat for each module)
Then 8.Write【Copyright】 (global, one pass)
```

**Wrong pattern — batch per step (do NOT do this):**
```
5.Write【Quick Start for ALL modules】   ← Token explosion, context loss
6.Write【APIs for ALL modules】
7.Write【SE Analysis for ALL modules】
```

For **single-project** tier (only 1 module), the micro-loop collapses naturally to one iteration; treat it the same way.

> 5.Write【Quick Start】— `1_QuickStart/{Feature_N}/` (e.g. `1_QuickStart/0_FeatureA/index.md` with getting-started code samples)

> 6.Write【APIs】— `2_API/{Feature_N}/` (e.g. `2_API/0_FeatureA/index.md` with full API reference documentation)

> 7.Write【Software Engineering Analysis】— `3_SE_Analysis/.../{Feature}/` (architecture, class diagrams, sequences). Under `3_SE_Analysis/`, each sub-group (`0_file_structure/`, `1_feature_map/`, `2_design_patterns/`, `3_data_flow/`, `4_complexity/`) contains per-feature sub-pages.

> 8.Write【Copyright】— `{N}_Copyright/` (e.g. `4_Copyright/index.md`), where `N` is the last number in the language's content tree

### Polish & Publish (Steps 9-11)

> 9.Write【Welcome】— `0_Welcome/` (or `0_欢迎/` for zh). Execute after all content pages exist but before Review. Welcome summarizes all other pages.

> 10.【Review — Quality Gate 🔴 REQUIRED】— Load `skills/en/review/SKILL.md` and execute each check item, covering at minimum:
>     - Module coverage: Verify every module in the module list is documented
>     - Code authenticity: For every code block on every page, verify class names / method names / parameters / namespaces match source code
>     - Diagram syntax: Mermaid / PlantUML / KaTeX syntax validation
>     - Structural consistency: numeric prefixes, index.md presence, no local Markdown links
>     - Navigation index: Run `python gen_tree.py` to rebuild tree.json
>     - Project build: Run `dotnet build` to verify compilation

> 11.End

### Workflow Continuity

The workflow must **never silently stop** due to tool-call limits, token limits, timeouts, or any other infrastructure constraint. If the Agent reaches an execution limit or encounters a discontinuity:

1. **Do not fabricate results** to simulate completion
2. **Record observation** of where the workflow stopped and what has been done
3. **Ask the user** whether to continue, providing the current progress summary and estimated remaining work
4. Resume from the recorded checkpoint upon user confirmation

This rule applies to all phases: Module Discovery, Content Writing, and Review. A partial output is acceptable only if the user explicitly agrees to terminate early.

## Skill Index

Sub-skills are organized into independent directories by scenario. The Agent should only load a sub-skill's `SKILL.md` when the user's request matches the corresponding scenario — do not pre-load.

### Foundation Setup

| Path | Scenario | Trigger Keywords |
|---|---|---|
| `skills/en/context-setup/SKILL.md` | Variable confirmation — determine WIKI_ROOT, Solution_Root, Project_List, Language_List | Initialize workspace context, Determine Wiki root, Confirm solution and project list, Confirm language support scope |
| `skills/en/tech-analysis/SKILL.md` | Tech stack analysis — identify project tech stack, entry points, and dependency chain | Analyze this repository, Understand project structure, Find entry points, Understand what this project does, How is this project organized |

### Constraint Loading

| Path | Scenario | Trigger Keywords |
|---|---|---|
| `skills/en/lang-constraints/SKILL.md` | Load documentation conventions for the detected tech stack | Tech stack detected, need to load language conventions, Apply .NET documentation conventions, Apply Rust documentation conventions, Apply TypeScript documentation conventions, Apply Python documentation conventions, Apply Go documentation conventions, Apply C/C++ documentation conventions, Apply Java documentation conventions |
| `  skills/en/lang-constraints/c-cpp/SKILL.md` | C / C++ documentation conventions |  |
| `  skills/en/lang-constraints/dotnet/SKILL.md` | .NET documentation conventions (C# / VB / F#) |  |
| `  skills/en/lang-constraints/go/SKILL.md` | Go documentation conventions |  |
| `  skills/en/lang-constraints/java/SKILL.md` | Java documentation conventions |  |
| `  skills/en/lang-constraints/python/SKILL.md` | Python documentation conventions |  |
| `  skills/en/lang-constraints/rust/SKILL.md` | Rust documentation conventions |  |
| `  skills/en/lang-constraints/typescript/SKILL.md` | TypeScript / JavaScript documentation conventions |  |

### Content Writing

| Path | Scenario | Trigger Keywords |
|---|---|---|
| `skills/en/api-docs/SKILL.md` | API documentation — extracting API docs from code analysis | Extract API from test code, Generate API documentation, Create API reference from tests, Document public APIs |
| `skills/en/copyright/SKILL.md` | Copyright — writing copyright notices and license information | Write copyright notice, Document license information, Add contributor credits, Generate attribution |
| `skills/en/module-discovery/SKILL.md` | Module discovery — analyze solution structure, discover all functional modules | Discover modules in solution, Analyze project dependencies, Identify module responsibility boundaries, Map inter-module call relationships |
| `skills/en/quickstart/SKILL.md` | Quick Start — module-level Quick Start documentation | Write quick start tutorial, Create getting started guide, Write walkthrough for beginners, Write complete example |
| `skills/en/se-analysis/SKILL.md` | Software engineering analysis — architecture, class diagrams, sequences, API flow | Perform software engineering analysis, Draw architecture diagram, Analyze source code flow, Create class hierarchy document, Document request lifecycle |
| `skills/en/welcome-page/SKILL.md` | Welcome page — beautiful HTML landing page | Beautify welcome page, Design landing page, Replace welcome page, Create Hero section for Wiki |

### Quality Assurance

| Path | Scenario | Trigger Keywords |
|---|---|---|
| `skills/en/review/SKILL.md` | Review — Wiki content review and quality check | Review documentation quality, Check link validity, Audit Wiki content, Verify document structure, Ensure rendering compatibility |

