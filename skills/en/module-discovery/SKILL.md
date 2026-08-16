# Feature Inventory Discovery

## Responsibility

Execute the discovery flow defined in 【TEMPLATE · Analysis Paradigm】 and produce the「Feature Inventory」as the unified input for Quick Start, API Reference, and SE Analysis

## Workflow

### 1. Follow the Analysis Paradigm

Strictly follow the discovery order defined in the Analysis Paradigm, regardless of project size; never infer features from directory structure alone:

1. **Entry-point understanding** — read README, entry files, build scripts, etc., to form a candidate feature list
2. **Demo / Example first** — fully read all source files under Examples/, samples/, demo, etc., and extract feature and API evidence
3. **Test-driven** — when a Demo is missing, fully read the corresponding test files and extract feature boundaries and typical usage
4. **Source fallback** — only when the above are absent, infer from source and explicitly mark as *inferred*

### 2. Record Ownership and Dependencies

Read the dependency declarations from project definition files (build manifests, dependency manifests, etc.) and record each feature's owning project and dependencies; the exact file format and fields depend on the project's actual tech stack.

### 3. Generate the Feature Inventory

| Feature | Owning Project | Public API Surface | Dependencies | Evidence | Coverage Status |
|---|---|---|---|---|---|
| User registration | auth service | register(credentials) | database driver | Demo | QS ✓ / API ✓ / SE ✓ |
| Data export | report module | export(format) | template engine | Test | QS ✓ / API — / SE — |
| Theme customization | renderer | setTheme(palette) | — | *inferred* | TODO |

### 4. Coverage Status State Machine

Each feature carries a Coverage Status field tracking how far the three writing dimensions have covered it.

- `TODO` — discovered, not written yet.
- `QS ✓` — QuickStart page written (step 3). `API ✓` — API Reference page written (step 4). `SE ✓` — SE Analysis page written (step 5).
- Append a token each time a dimension completes; e.g. `QS ✓ / API ✓ / SE ✓`.

Rules:

- **Steps 3, 4, 5 MUST update this column immediately** after finishing a feature in their dimension. Do not leave it stale.
- **The feature set is frozen after this step.** Steps 3–5 may only mark status; they may NOT add, remove, or rename features. Any correction must flow back into the inventory and be re-reconciled.
- The inventory is a working artifact maintained **outside Wiki_Root** (e.g. `CloudGlyph_Child_Git/.workflow/feature-inventory.md`) and carried into step 8 Review for reconciliation. It is regenerated each run, so a future template sync removing it is expected.

## Output

- 「Feature Inventory」table (feature / owning project / public API surface / dependencies / evidence source / coverage status)
- The inventory is the single feature input for the subsequent Quick Start / API Reference / SE Analysis phases — they must not introduce a different feature breakdown, and they must keep the Coverage Status column up to date
