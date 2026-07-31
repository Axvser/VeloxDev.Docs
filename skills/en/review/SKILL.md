# Review

## Responsibility

Review and correct each deliverable one by one

## Checklist

### Feature Inventory Coverage Audit

- [ ] Cross-reference the「Feature Inventory」produced by the Analysis Paradigm, verifying every feature is documented across Quick Start / API Reference / SE Analysis
- [ ] Immediately fill any missing features

---

### Usage Completeness Audit

- [ ] Each feature module's Quick Start covers its top-level API (attributes/fluent/extension methods)
- [ ] API reference covers all public types and members found during discovery
- [ ] Code examples demonstrate both **declarative** and **imperative** usage styles

---

### Demo Read Verification (Pre-check)

Before starting the per-page audit, verify whether the writing phase fulfilled the mandatory full-read obligation:

- [ ] For every module with Demo code, confirm the documentation covers usage patterns from **all source files** in that module's Demo directory, not just a few snippets
- [ ] For every module with only tests, confirm the documentation covers key usages and edge cases from the test files
- [ ] If a Demo exists but the documentation clearly misses patterns → **mark as FAIL**, require the Agent to re-read the full Demo and rewrite

---

### Code Authenticity Verification (CRITICAL — Full Per-Page Audit)

For **every page** in the Wiki, extract all code blocks containing API references. For each reference:

- [ ] **Discovery Priority compliance** — Verify that code samples came from Demo projects (Priority 1) or Tests (Priority 2) first. If only Priority 3 (inferred from source) was used, confirm it is explicitly marked as *inferred*.
- [ ] **Class/method names** — search the codebase to confirm each type and member exists **with the documented signature**
- [ ] **Namespace/module paths** — verify they match the actual project structure and source declarations; never invent paths
- [ ] **Method parameters and return types** — cross-check against the source declaration; document must match reality
- [ ] **Exception declarations** — if the doc lists thrown exceptions, confirm they exist in the method signature or doc comments
- [ ] **Property/field names** — every property or field referenced must be present on the declared type
- [ ] **Removed/deprecated APIs** — flag any doc references to deprecated or removed members for correction
- [ ] **No fabricated code** — every code block must trace back to a real source file

---

### Diagram Syntax Validation

- [ ] **Mermaid** — direction/type valid, participants declared, brackets balanced, arrows correct
- [ ] **KaTeX** — all `$...$` and `$$...$$` inline/block pairs are balanced, no mismatched delimiters
- [ ] **PlantUML** — `@startuml` / `@enduml` paired, participants declared before use, `activate`/`deactivate` paired, `alt`/`else`/`end` structure correct

---

### Structural Consistency

- [ ] Numeric prefixes follow conventions (e.g. `01_`, `02_`)
- [ ] `index.md` exists in **every** page directory (root and sub-pages)
- [ ] Code block indentation uses real spaces, not tab characters, matching the Code Style Conventions
- [ ] No local Markdown links (`[text](local/path/)`) — use relative navigation via the tree instead
- [ ] **Prune untracked entries** — Any document page or directory **not produced by the current workflow** must be deleted. If removing all affected files empties a parent directory and that does not break the current output structure, the empty directory must also be removed.

---

### Cross-language Parity

- [ ] If multi-language is enabled, **every** page exists in **all** selected languages
- [ ] No missing or outdated pages across language versions

---

### Navigation Index Verification

- [ ] **Run navigation script** — Execute `python gen_tree.py` (or the actual script for the project) to rebuild `tree.json`
- [ ] **Verify script output** — Confirm the generated `tree.json` includes **all** new pages with correct nesting
- [ ] **Build the project** — Run the project's build command to verify compilation

---

## Pre-Commit Verification Flow

1. Walk through the checklist item by item; **fix issues immediately** before moving to the next item
2. Code authenticity issues → search source to confirm signatures, then fix docs
3. Diagram syntax issues → fix and re-validate
4. Run `python gen_tree.py`, confirm no pages are missing
5. Run the project's build command, confirm compilation succeeds
6. Only after all items are ✅, mark the quality gate as passed
