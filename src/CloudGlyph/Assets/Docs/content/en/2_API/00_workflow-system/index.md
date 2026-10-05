# Workflow System — API Reference

Public surface of the `workflow-system` feature, grouped by namespace, plus cross-cutting pages for the headline member contracts and the execution mechanism. Every type below exists in the real source; source paths are cited. Where a behavior is inferred from source rather than Demo/Test evidence it is marked *inferred*.

## API — Sections

This feature's API reference is split into:

- [Namespace: VeloxDev.WorkflowSystem](00_workflowsystem/index.md) — the core `VeloxDev.WorkflowSystem` surface (builder attributes, component interfaces, geometry/value types, default view-models, selectors, spatial map, render-readiness)
- [Namespace: VeloxDev.WorkflowSystem.StandardEx](01_standardex/index.md) — the `VeloxDev.WorkflowSystem.StandardEx` standard behavior extensions
- [Namespace: VeloxDev.Core.WorkflowSystem.CompilerEx](02_compilerex/index.md) — the `VeloxDev.Core.WorkflowSystem.CompilerEx` compile pipeline, compiled model, runtime engine, and the host-capability layer
- [Key Member Contracts](03_key-member-contracts/index.md) — entry-template form of the headline top-level APIs
- [Execution Mechanism (Compiler vs non-Compiler)](04_execution-mechanism/index.md) — how the Compiler (engine-driven) and non-Compiler (broadcast) paths both reach a node's `ReceiveAsync`
- [GUI Input](05_gui-input/index.md) — the routed pointer/keyboard surface: `WorkflowInput`, `IInputEvents`, the fifteen standard types, and the alias discipline platform code must follow

### Inside `compilerex`

`VeloxDev.Core.WorkflowSystem.CompilerEx` is large, so its page is an overview over five sub-pages:

| Sub-page | Contents |
|---|---|
| [Compile Pipeline](02_compilerex/00_compile-pipeline/index.md) | `CompilerViewModel`, `CompileRole`, `CompiledGraph` + the three segments, `BranchOption`, the compile-time contracts, `CompiledOutline` |
| [Runtime Engine](02_compilerex/01_runtime-engine/index.md) | `RuntimeEngine.RunAsync` (with `resumeFrom`), `IRuntimeContext`, `IRuntimeAware`, `IRedirectable`, `RunOutcome` |
| [The Session: RuntimeContext and GroupData](02_compilerex/01_runtime-engine/00_runtime-context/index.md) | `RuntimeContext` — every member, including the host-capability properties — and `IGroupData` / `GroupData` |
| [Execution Contracts](02_compilerex/02_execution-contracts/index.md) | `IExecutionGate`, `IExecutionObserver`, `INodeRetryPolicy`, `IExecutionErrorSink`, `IExecutionCompensation`, `IExecutionCheckpointStore`, `ILogWriter` + payload types |
| [Execution Implementations](02_compilerex/03_execution-implementations/index.md) | `ManualExecutionGate`, the `Delegate*` adapters, `TextWriterLogWriter`, `ExponentialBackoffRetry` |
| [Checkpointing](02_compilerex/04_checkpointing/index.md) | `ExecutionCheckpoint`, `InMemoryCheckpointStore`, `BranchRuntimeContext` (internal) |

All six links above are reachable from [Namespace: VeloxDev.Core.WorkflowSystem.CompilerEx](02_compilerex/index.md), which is the overview page for the namespace.

## Coverage note — the 2026-09-27 host-capability layer

The compile/run core is fully covered by Demo + Test evidence. The host-capability layer added on 2026-09-27 is covered like this:

| Member group | Evidence |
|---|---|
| `IExecutionGate`, `IExecutionObserver`, `INodeRetryPolicy`, `IExecutionErrorSink`, `IExecutionCompensation`, `IExecutionCheckpointStore`, `ILogWriter` | **Demo** — all seven are configured together on one session by `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` (`ConfigureRun`), and **Test** (`CompilerEx/Execution*Tests.cs`, `CompilerLogWriterTests.cs`) |
| `MaxRetainedLogs`, `SnapshotLogs` | **Test** only (`CompilerLogWriterTests.cs`, `RuntimeContextLogConcurrencyTests.cs`) — no demo sets either |
| `MaxParallelBranches` | **Test** only (`ParallelExecutionTests.cs`) — no demo sets it, so no demo demonstrates a concurrency cap |
| `Target` / `TargetReached` | **Test** only (`CompileToReverseTests.cs`, `RuntimeEngineRunTests.cs`) — the Agent extension reads them, no demo sets `Target` |
| `RunOutcome`, `CompiledOutline` | **Demo** (`WorkflowDemoSession.cs` reads `Outcome`; `TreeViewModel.cs` binds `CompiledOutline.Of`) + **Test** |

Both `internal` types that matter behaviorally — `BranchRuntimeContext` and `CompileKeyNormalizer` — are documented on the pages where they appear and marked `internal`, so the public surface stays an exact statement of what a consumer can call.
