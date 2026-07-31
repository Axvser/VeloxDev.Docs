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

| Feature | Owning Project | Public API Surface | Dependencies | Evidence |
|---|---|---|---|---|
| User registration | auth service | register(credentials) | database driver | Demo |
| Data export | report module | export(format) | template engine | Test |

## Output

- 「Feature Inventory」table (feature / owning project / public API surface / dependencies / evidence source)
- This inventory is the single feature input for the subsequent Quick Start / API Reference / SE Analysis phases — they must not introduce a different feature breakdown
