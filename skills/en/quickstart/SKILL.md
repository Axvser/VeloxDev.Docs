# Quick Start

## Responsibility

Write a self-contained runnable tutorial for each feature module, using top-level APIs to build a real working example.

## Writing Principles

### Runnable and Complete

The goal of Quick Start is not minimal code snippets, but guiding the reader from zero to a **truly runnable** project or feature. Each Quick Start should:

- **Have a clear start and end** — begin with project setup/dependency installation, end with verifying the feature works
- **Be replicable** — the reader can follow step by step and get a working program
- **Be practical** — solve a real business scenario or functional need

### Top-Level API First

Use the module's highest-level API (attributes, extension methods, Fluent API, base classes) to show **what it looks like to use**, not **how it's implemented internally**. Low-level interface implementation and manual patterns belong in the API reference.

### Material Source

Use the「Feature Inventory」produced by the 【Analysis Paradigm】 directly: each feature's evidence source (Demo / Test / inferred) is already recorded. Prioritize by evidence — fully read all Demo source files first, then tests; examples for features marked *inferred* must be noted as such in the page. Do not redo feature discovery.

### Reproducibility Contract

Every Quick Start is a **contract that a human can reproduce end-to-end**. On top of the structure below, obey:

- **Prerequisites are mandatory and derived from build metadata, not from Demos** — read the project's declared `TargetFrameworks` / `TargetFramework` and dependency minimums (csproj/project files, package manifests) to state the actual supported targets, SDK/runtime and package versions. A Demo or test only proves one *tested* configuration — it is never the minimum supported version. State required services with how to obtain/start them.
- **Every numbered step states an observable "Expected result"** — what the reader sees/hears/verifies after completing it, not only at the end.
- **Complete Code is a single minimal runnable block** — no `...` / ellipses; symbol self-consistency: every identifier used is defined in the sample, in a prior step, or traced to a real file (with path).
- **Run Declaration is mandatory** — the page must end by honestly declaring whether the writer actually built and ran it (✅, with recorded output) or only statically verified it (⚠️).

### Sub-pages (default-split)

A feature's Quick Start is normally **split into sub-pages** rather than one long page. Split when the page would exceed **~300 lines** or cover more than **3 distinct topics** — group by step or by operation:

```
00_{Feature}/                        ← overview + table of contents
├── index.md
├── 00_prerequisites/
├── 01_setup/
├── 02_{operation-a}/
├── 03_{operation-b}/
└── 09_verification/                 ← Verification + Complete Code + Run Declaration
```

- Each sub-page keeps its own **Expected result** assertions.
- The parent `index.md` is a short overview that links the sub-pages; do not duplicate their body there.
- The **Run Declaration** footer stays at the end of the last content page (the one holding the Complete Code).

### Structure

```
# {Feature Name}

## Quick Start

### 1. Prerequisites

- **Supported target(s) from the project's declared `TargetFrameworks`** (e.g. `netstandard2.0;net6.0`) — the Demo's runtime is only a *tested* configuration, never the requirement
- {SDK/runtime}: version required by the supported target (e.g. .NET SDK 6.0+ for `net6.0`)
- {Package manager}: version
- {Required services}: (e.g. a running database, API key) — and how to obtain/start them
- If any prerequisite cannot be verified locally, the Run Declaration below MUST be ⚠️.

### 2. Install / Add Dependency

How to install / add dependencies (using the package manager appropriate to the project's tech stack)

**Expected result:** {observable outcome, e.g. package appears in the manifest / command exits 0}

### 3. Basic Setup / Registration

Register services, create instances, configure settings, etc.

**Expected result:** {e.g. object constructs, service starts, config loads}

### 4. Core Usage (Step by Step)

Combine top-level APIs step by step, from simple to complete, each with runnable code

**Expected result:** {e.g. output value, UI state, HTTP status}

### 5. Verification

How to run and verify the feature works (expected output, UI effect, etc.)

### 6. Complete Code

A single minimal complete runnable block. NO `...` / ellipses. Symbol self-consistency: every identifier used is defined in this sample, in a prior step, or traced to a real file (with path).

### 7. Run Declaration

- ✅ Actually built and ran on {date}; recorded output: {paste actual output}
- OR ⚠️ Not actually run — statically verified only. Keep this declaration honest; it is the reproducibility contract.
```

### Output Location

```
Wiki_Root/1_QuickStart/
├── index.md                    ← Overview
├── 00_{feature-a}/
│   └── index.md
├── 01_{feature-b}/
│   └── index.md
└── ...
```

> Directory names must come from the Feature Inventory and be identical across the `1_QuickStart`, `2_API`, and `3_SE_Analysis` trees (cross-dimension consistency).

## Post-Write Action

After writing Quick Start content:

- [ ] **Update the Feature Inventory** — set this feature's Coverage Status to `QS ✓` (see module-discovery)
- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run the project's build command to verify the new content embeds correctly
