# Review

## Responsibility

Review and correct each deliverable one by one

## Checklist

### Coverage Reconciliation Matrix (HARD GATE)

Build the matrix from the Feature Inventory's Coverage Status column. The matrix MUST be written into the Review output — it is a deliverable, not a thought exercise.

| Feature | Evidence | QuickStart | API | SE Analysis | Status |
|---|---|---|---|---|---|
| User registration | Demo | ✅ | ✅ | ✅ | PASS |
| Data export | Test | ✅ | ✅ | ❌ missing data-flow sub-page | FAIL |
| Theme customization | *inferred* | ✅ | ⚠️ partial: `setTheme` only | ✅ | PASS (residual) |

Rules:

- **Features with Demo/Test evidence MUST be ✅ across all three dimensions (QuickStart / API / SE Analysis). Any ❌ ⇒ the entire Review FAILS.** Fix immediately and re-run before continuing.
- **Only *inferred* features may carry residual ⚠️ items**, and each residual MUST state a one-line reason (e.g. "API surface not fully covered by evidence").
- After reconciliation, write the final status back into the Feature Inventory (`PASS` / `FAIL` / `RESIDUAL`).
- If the inventory carries `TODO` or a stale status that a completed page contradicts → FAIL; the status machine was not respected.

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

### Reproducibility Spot-check

- [ ] Every QuickStart has a mandatory **Prerequisites** block (SDK/runtime/package-manager versions, target framework, required services)
- [ ] Prerequisites are derived from the project's declared `TargetFrameworks`/dependency minimums — **not** from a Demo's runtime (a Demo proves one tested config, never the minimum)
- [ ] Every numbered step states an observable **Expected result**
- [ ] The complete-code block contains **no `...` / ellipses**; every identifier is defined in the sample, a prior step, or traced to a real file
- [ ] The page ends with a **Run Declaration** footer: `✅ actually built/ran` (recorded output) or `⚠️ not actually run` (static verification only, marked)
- [ ] For any `✅` declaration, the recorded output matches the step's stated expected results

---

### Diagram & Formula Validation (real-engine render + fallback pre-check)

Diagrams and math are validated by the **actual rendering engines** — ground truth, not by eye or heuristics. **One-time setup** in `<CloudGlyph_Child_Git>/src/CloudGlyph/Assets/Docs/scripts/`: run `npm install` (provides mermaid/katex/jsdom) and place `plantuml.jar` next to the script (or pass `--jar <path>`). Then run:

- [ ] **PlantUML (real engine)** — `python validate-plantuml.py <Wiki_Root> --engine java`; the actual `plantuml.jar -checkonly` must report no errors
- [ ] **Mermaid (real parser)** — `node validate-mermaid.js <Wiki_Root>`; the real `mermaid.parse` must not throw
- [ ] **KaTeX (real renderer)** — `node validate-katex.js <Wiki_Root>`; the real `katex.renderToString` must not throw on any `$...$` / `$$...$$`
- [ ] Fix every reported **ERROR** — a real-engine error means the diagram/math will not render, it is authoritative
- [ ] **If the engines are unavailable** (no node/java on the machine), fall back to the dependency-free structural pre-checks `validate-plantuml.py` / `validate-mermaid.py` / `validate-katex.py` (heuristic) and explicitly note that real-render validation was not run

---

### Structural Consistency

- [ ] Numeric prefixes follow conventions (e.g. `01_`, `02_`)
- [ ] `index.md` exists in **every** page directory (root and sub-pages)
- [ ] Code block indentation uses real spaces, not tab characters, matching the Code Style Conventions
- [ ] No local Markdown links (`[text](local/path/)`) — use relative navigation via the tree instead
- [ ] Pages exceeding **~300 lines / 3 topics** are split into sub-pages, with the parent `index.md` acting as an overview/table of contents
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
3. Diagram/KaTeX issues → run the real-engine validators (`validate-plantuml.py --engine java`, `validate-mermaid.js`, `validate-katex.js`), fix every ERROR, re-run until clean
4. Reconcile the **Coverage Reconciliation Matrix**: if any Demo/Test feature has a ❌, or the matrix was not written, the quality gate FAILS
5. Run the **Reproducibility Spot-check** against the QuickStart pages
6. Run `python gen_tree.py`, confirm no pages are missing
7. Run the project's build command, confirm compilation succeeds
8. Only after all items are ✅, mark the quality gate as passed
