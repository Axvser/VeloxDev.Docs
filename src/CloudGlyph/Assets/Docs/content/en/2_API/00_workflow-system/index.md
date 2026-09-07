# Workflow System — API Reference

Public surface of the `workflow-system` feature, grouped by namespace, plus cross-cutting pages for the headline member contracts and the execution mechanism. Every type below exists in the real source; source paths are cited. Where a behavior is inferred from source rather than Demo/Test evidence it is marked *inferred*.

## API — Sections

This feature's API reference is split into:

- [00_workflowsystem](00_workflowsystem/index.md) — the core `VeloxDev.WorkflowSystem` surface (builder attributes, component interfaces, geometry/value types, default view-models, selectors, spatial map, render-readiness)
- [01_standardex](01_standardex/index.md) — the `VeloxDev.WorkflowSystem.StandardEx` standard behavior extensions
- [02_compilerex](02_compilerex/index.md) — the `VeloxDev.Core.WorkflowSystem.CompilerEx` compile pipeline, compiled model, and runtime engine
- [03_mvvm-serialization](03_mvvm-serialization/index.md) — `VeloxDev.MVVM.Serialization.ComponentModelEx` save/load helpers
- [04_key-member-contracts](04_key-member-contracts/index.md) — entry-template form of the headline top-level APIs
- [05_execution-mechanism](05_execution-mechanism/index.md) — how the Compiler (engine-driven) and non-Compiler (broadcast) paths both reach a node's `ReceiveAsync`
