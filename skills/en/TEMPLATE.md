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
