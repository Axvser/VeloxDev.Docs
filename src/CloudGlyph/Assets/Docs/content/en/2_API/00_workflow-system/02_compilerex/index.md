# Workflow System — Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`

The compile/run pipeline. `CompilerViewModel.CompileAsync` decomposes the sub-graph reachable from a node into acyclic compiled graphs (`CompiledGraph` of `ChainSegment` / `BranchSegment` / `ParallelSegment`) and gives every `ICompileTimeAware` node a compile identity (`CompileContext`). `RuntimeEngine.RunAsync` then drives those segments, calling each node's single execution entry, `IWorkflowNodeViewModelHelper.ReceiveAsync`.

Everything in this namespace is `public`. Two types are deliberately `internal` — `BranchRuntimeContext` and `CompileKeyNormalizer` — and are documented as such on the pages where they appear, because they explain behavior that is otherwise invisible.

## Sections

The namespace is large enough that this page is an overview only. It is split into five sub-pages:

| Page | Contents |
|---|---|
| [Compile Pipeline](00_compile-pipeline/index.md) | `CompilerViewModel`, `CompileRole`, the compiled model (`CompiledGraph` / `CompileSegment` / `ChainSegment` / `BranchSegment` / `ParallelSegment` / `BranchOption`), the compile-time contracts (`ICompileContext` / `CompileContext` / `ICompileTimeAware` / `ICompileTimeRouter` / `RouterCompileMode`), `CompiledOutline` |
| [Runtime Engine](01_runtime-engine/index.md) | `RuntimeEngine.RunAsync` (including the `resumeFrom` overload), `IRuntimeContext`, `IRuntimeAware`, `IRedirectable`, `RunOutcome` |
| [The Session: RuntimeContext and GroupData](01_runtime-engine/00_runtime-context/index.md) | `RuntimeContext` — all members, including the host-capability properties — and `IGroupData` / `GroupData` |
| [Execution Contracts](02_execution-contracts/index.md) | The host-capability layer: `IExecutionGate`, `IExecutionObserver`, `INodeRetryPolicy`, `IExecutionErrorSink`, `IExecutionCompensation`, `IExecutionCheckpointStore`, `ILogWriter`, and their record/enum payloads |
| [Execution Implementations](03_execution-implementations/index.md) | The shipped implementations of those contracts: `ManualExecutionGate`, `DelegateExecutionGate`, `DelegateExecutionObserver`, `DelegateExecutionErrorSink`, `DelegateExecutionCompensation`, `DelegateLogWriter`, `TextWriterLogWriter`, `ExponentialBackoffRetry` |
| [Checkpointing](04_checkpointing/index.md) | `ExecutionCheckpoint`, `InMemoryCheckpointStore`, `BranchRuntimeContext` (internal), and the resume/refuse contract |

Serialization of the compiled artifacts and of a checkpoint lives in a different assembly and is documented separately: see [Namespace: VeloxDev.MVVM.Serialization](../03_mvvm-serialization/index.md) (`CompiledGraphEx`, `CheckpointEx`, `FileCheckpointStore`).

> For how the engine-driven (Compiler) path and the node-driven broadcast path reach the *same* `ReceiveAsync` — entry points, parameters, and timing — see [Execution Mechanism (Compiler vs non-Compiler)](../05_execution-mechanism/index.md).

## Evidence

- **Demo** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/` (`WorkflowDemoSession.cs` configures all seven host capabilities on one session; `ControllerViewModel.cs` compiles then drives; `PythonScriptNodeViewModel.cs` implements `IRedirectable`), consumed by the WPF / Avalonia / Blazor / MAUI / WinUI / WinForms / Jalium full demos.
- **Test** — `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/` (`RuntimeEngineRunTests`, `RuntimeRedirectTests`, `ExecutionCheckpointTests`, `ExecutionCompensationTests`, `ExecutionErrorSinkTests`, `ExecutionGateTests`, `ExecutionObserverTests`, `ExecutionRetryTests`, `ParallelExecutionTests`, `CompilerLogWriterTests`, `RuntimeContextLogConcurrencyTests`, `NodeReportTests`, `EngineHostContractFailureTests`, `CompiledOutlineTests`, `EntrySemanticsTests`, `CompileDecompositionTests`, `CompileToReverseTests`, plus the shared `ProbeGraph.cs` / `ProbeNodes.cs` harness).

## The host-capability layer, in one paragraph

For the engine's whole life before 2026-09-27 it had exactly one answer to a failure (redirect) and no seam for a host to hold, watch, retry, record, undo or resume a run. That layer adds seven optional seams — a pause **gate**, an **observer**, a **retry policy**, an **error sink**, a **compensation**, a **checkpoint store** and a **log writer** — every one of which is read off the host's concrete `RuntimeContext` and every one of which, left unset, reproduces the pre-2026-09-27 behavior byte for byte, down to the log lines and the number of drives. They are resolved through a private `Session()` helper so they keep working *inside* a parallel fan-out, and most of them are deliberately **not** members of `IRuntimeContext`, because adding a member to that interface would break every external implementation.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/**`, `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/**`.*
