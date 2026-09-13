# Review

## Responsibility

Review and correct each deliverable one by one

## Reviewer Assignment

### Delegate by default

Reviewing your own output invites self-approval: the fixes you already believe in, the samples you are already convinced are correct. Whenever the run environment can launch an **independent reviewer** — a separate sub-agent whose context did NOT take part in the writing phases (e.g. Claude: spawn the `wiki-reviewer` sub-agent installed with this SKILL, or any fresh-context sub-agent; other hosts: their equivalent) — you MUST delegate this phase to it. This is the default path, not an optimization. A writer judging its own Review checklist will tend to wave itself through; an independent reviewer does not share that bias.

Hand the reviewer a self-contained brief:

- **Paths** — Project_Root; Wiki_Root for each selected language; the Feature Inventory working file; the validator scripts directory.
- **Access** — read-only. The reviewer reports findings; the WRITER applies fixes.
- **Instructions** — trust nothing the writer asserted. Re-check code authenticity and the public API surface against Demo / test files, never against the writer's prose. Run every machine validator itself (`validate-links.py`, `validate-structure.py`, `validate-titles.py`, `validate-plot.py`, `validate-plantuml.py --engine java`, `validate-mermaid.js`, `validate-katex.js`, `gen_tree.py`) and paste the raw output. Produce the Coverage Reconciliation Matrix independently from the Feature Inventory.
- **Output** — an ordered FAIL / PASS list with file paths, plus the Coverage Reconciliation Matrix.

After the report returns, the WRITER triages and fixes the findings only — and never "re-reviews" and clears its own findings.

### Fallback when no separate agent exists

If the platform cannot spawn an independent reviewer (single-context hosts), review in-process while assuming you will rubber-stamp your own work, and counter it:

- Every machine validator runs and its raw output is cited — a PASS quotes output, not intent.
- For every page, name one thing you would challenge if you had NOT authored it, then fix or justify it.
- Write the Coverage Reconciliation Matrix from the Feature Inventory file, not from memory.
- Anything that can only be confirmed "by the author" is downgraded to a residual and marked as such.

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
- [ ] **Plots (structural)** — `python validate-plot.py <Wiki_Root>` reports no ERROR: every ```plot body is a JSON object, `data` is an array, and each expression (`fn`/`x`/`y`/`r`) uses only the characters the renderer's whitelist accepts
- [ ] **Curve over prose** — for every page describing a mathematical behaviour (an easing family, a decay, a response curve, a distribution), confirm the page **draws it with `plot`** rather than only tabulating or narrating it. A table of easing formulas where one plot would show the shape is a WARN, and the reviewer must say so explicitly.
- [ ] Fix every reported **ERROR** — a real-engine error means the diagram/math will not render, it is authoritative
- [ ] **If the engines are unavailable** (no node/java on the machine), fall back to the dependency-free structural pre-checks `validate-plantuml.py` / `validate-mermaid.py` / `validate-katex.py` / `validate-plot.py` (heuristic) and explicitly note that real-render validation was not run

---

### Title & Localisation Audit (HARD GATE)

The sidebar renders directory names and the pages render headings and link labels. Both are read by humans, so both must be *titles*, not paths, and both must be *in the reader's language*.

- [ ] **No numeric prefix in visible text** — `python validate-titles.py <content root>` reports no ERROR. It flags a `NN_` token that reaches a link label, a heading, or the inner text of an `<a>`; link *destinations* are exempt. Any hit is a defect: a reader must never see `1_QuickStart`, only `QuickStart`.
- [ ] **Every page title is translated** — in each non-English language tree, every directory segment is either the translation of its English counterpart or a literal code identifier (`MVVM`, `AOP`, `MonoBehaviour`, `00_VeloxPropertyAttribute` — a token that exists as a type/namespace/API name in the source). An untranslated descriptive segment (`prerequisites`, `install`, `complete-code`, `attached-behaviors`, `patterns-overview`) is an ERROR.
- [ ] **The exception is justified by source, not by convenience** — for every segment kept verbatim in a translated tree, grep 【Project_Root】 for that exact token as a type, namespace or API name. "It is a technical word" is not sufficient; "it is `VeloxDev.MVVM`" is.
- [ ] **Headings and body prose match the page's language** — an untranslated section heading inside a translated page is the same defect as an untranslated directory name.
- [ ] **No heading restates the heading above it** — `python validate-titles.py` also reports the "restatement chain" (`# Workflow System — Quick Start` / `## Workflow System` / `### Quick Start`) and the "dimension echo" (a heading straight after the H1 that only names the parent dimension). Fix by deleting the repeated heading and promoting its sub-headings, never by deleting the section.
- [ ] **Cross-language meaning parity** — for each language, the page at a given position in the tree is the translation of the page at the same position in the other. `validate-structure.py` checks the topology; the wording is checked here, page by page.

---

### Welcome Page Audit

- [ ] The page is the template body **and nothing else** — no prose paragraphs, tables, feature inventories, "Explore the documentation" sections or repository links after the closing `</div>`
- [ ] **Every feature card is a link** (`<a class="feat-link" href="…">`) pointing at that feature's QuickStart page (or the QuickStart overview when the feature has none), with `.feat-link` present in the stylesheet so the link adds no underline or colour
- [ ] No trailing dot-separated tagline row (`· No database · Open source · MIT`, the former `.glow-dot` row)
- [ ] The hero's link labels carry no numeric prefix (see Title & Localisation Audit)

---

### Structural Consistency

- [ ] Numeric prefixes follow conventions (e.g. `01_`, `02_`)
- [ ] `index.md` exists in **every** page directory (root and sub-pages) — machine-enforced by `validate-structure.py` (see below); do not rely on `gen_tree.py` creating it
- [ ] Code block indentation uses real spaces, not tab characters, matching the Code Style Conventions
- [ ] **Links** — every link is exactly one of the three allowed kinds and resolves (see 【Links & Navigation】): external `http(s):`/`mailto:`/`tel:` opens in the system app; a same-language cross-page link resolves to an existing page directory in the same language root; a `#…` anchor equals the auto slug of a heading on that same page. No other local/absolute/cross-language links.
- [ ] **Run the link validator** — `python validate-links.py <Wiki_Root>` reports no ERROR (each `#…` matches a real heading slug in that file; each cross-page target exists under the same language root)
- [ ] **Run the structure validator** — `python validate-structure.py <content root>` reports no ERROR. It machine-checks the structural rules that have no other gate: every directory (root, intermediate and leaf) contains an index.md; a **leaf** page stays within the split budget (≈300 lines, hard cap) — an over-long leaf is an ERROR telling you to split it into `NN_` sub-pages (outline-first); a **parent** index.md is a short overview that links EVERY child page (a missing child link is an ERROR); the tree shape is identical across the selected languages; and the QuickStart (`1_*`) / API (`2_*`) feature sets agree within each language. Pages under `4_Copyright` and pages whose index.md starts with `<!-- cg:atomic -->` are exempt from the line budget.
- [ ] Pages exceeding **~300 lines / 3 topics** are split into sub-pages (outline-first), with the parent `index.md` acting as an overview/table of contents that links every child — machine-checked by `validate-structure.py`
- [ ] **Prune stale entries** — Deletion is limited to page directories that are ALL of: (a) not on this run's output list, (b) not a prior page recorded during Context Setup's scan (previous runs' valid output must be preserved and updated in place), and (c) not linked from any kept page — run `python validate-links.py <Wiki_Root>` to confirm no kept page points at them. List every candidate explicitly before deleting; if deleting them empties a parent directory that no kept page references, remove that directory too. Never delete a page merely because this run did not rewrite it.

---

### Cross-language Parity

- [ ] If multi-language is enabled, **every** page exists in **all** selected languages
- [ ] No missing or outdated pages across language versions
- [ ] Run `python validate-structure.py <content root>`; its cross-language tree-shape check reports no ERROR. The script compares structure (numeric-prefix topology), so page-by-page confirm translations are current wording too.

---

### Navigation Index Verification

- [ ] **Run navigation script** — Execute `python gen_tree.py` (or the actual script for the project) to rebuild `tree.json`
- [ ] **Verify script output** — Confirm the generated `tree.json` includes **all** new pages with correct nesting
- [ ] **Build the project** — Run the project's build command to verify compilation

---

## Pre-Commit Verification Flow

> **Assign the review first** — when an independent reviewer sub-agent can be launched, delegate the entire checklist below to it (see Reviewer Assignment) and fix what it reports; the in-process fallback applies only to hosts without sub-agents.

1. Walk through the checklist item by item; **fix issues immediately** before moving to the next item
2. Code authenticity issues → search source to confirm signatures, then fix docs
3. Diagram/KaTeX/plot issues → run the real-engine validators (`validate-plantuml.py --engine java`, `validate-mermaid.js`, `validate-katex.js`) plus `validate-plot.py`, fix every ERROR, re-run until clean
4. Link issues → run `python validate-links.py <Wiki_Root>`, fix every ERROR, re-run until clean
5. Title/localisation issues → run `python validate-titles.py <content root>` (numeric prefix leaking into visible text; untranslated directory titles); fix every ERROR, re-run until clean, then walk the Welcome Page Audit
6. Structure issues → run `python validate-structure.py <content root>` (index.md coverage in every directory, cross-language tree shape, QuickStart/API feature parity); fix every ERROR, re-run until clean
7. Reconcile the **Coverage Reconciliation Matrix**: if any Demo/Test feature has a ❌, or the matrix was not written, the quality gate FAILS
8. Run the **Reproducibility Spot-check** against the QuickStart pages
9. Run `python gen_tree.py`, confirm no pages are missing (once structure is clean there is no missing index.md, so `--strict` is unnecessary here)
10. Run the project's build command, confirm compilation succeeds
11. Only after all items are ✅, mark the quality gate as passed
