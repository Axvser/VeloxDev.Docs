# Workflow System — Verify & Run Declaration

## 1. Verification against the real repository

- **Compiler / runtime tests** — `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`:
    `CompileDecompositionTests.cs` (segment shapes), `RuntimeEngineRunTests.cs` (chain data flow, dynamic router, fan-out, `IGroupData` joins, terminal branch, error stop), `RuntimeRedirectTests.cs` (redirect contract, the 50-redirect cap), `EntrySemanticsTests.cs` (the three entry points), `CompileToReverseTests.cs` (Terminal / ancestor-cone / no-fabrication rules), `EngineHostContractFailureTests.cs` (a throwing router / redirect / attach ends the run instead of leaving it looking `"Running"`).
- **Host-capability tests** — `ExecutionGateTests.cs`, `ExecutionObserverTests.cs`, `ExecutionRetryTests.cs`, `ExecutionErrorSinkTests.cs`, `ExecutionCompensationTests.cs`, `ExecutionCheckpointTests.cs`, `CompilerLogWriterTests.cs`, `RuntimeContextLogConcurrencyTests.cs`, `NodeReportTests.cs`, `ParallelExecutionTests.cs`, `CompiledOutlineTests.cs`.
- **Value-type / topology tests** — `Src/Core/VeloxDev.Core.Test/WorkflowSystem/` (`AnchorTests`, `SlotEnumeratorTests`, `WorkflowTreeExTests`, …).
- **Serialization tests** — `Src/Core/VeloxDev.Core.Extension.Test/Serialization/ComponentModelExTests.cs`, `ExecutionCheckpointSerializationTests.cs`.
- **Demo** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` builds the full voltage-analysis chain (`Controller → Timer → Generate Dataset → [Stats, Dist, Anomaly] → Merge Report (IGroupData) → Enum Selector → [Report High/Low/Zero]`) and configures **all seven** host capabilities in `ConfigureRun`. Every full platform demo binds Run / Resume / Stop / Pause / "Continue from checkpoint" to it.
    Note: the `* Trimmed` sibling demos are **node-editor-only** — they reference neither `Common/Lib` nor the compiler/runtime. They are the authoritative trim-safety demo of the *editor* surface, not of this feature's compiled-execution layer.

## 2. Run declaration

- ✅ **Actually built and ran on 2026-10-01.** Command: `dotnet build -c Debug` then `dotnet run -c Debug` in a console project (`net10.0`, `Nullable` and `ImplicitUsings` enabled) that project-references `Src/Core/VeloxDev.Core`, `Src/Core/VeloxDev.Core.Extension` and `Src/Generators/VeloxDev.Core.Generator` (the last as an analyzer with `ReferenceOutputAssembly=false`), on .NET SDK 10.0.401. The program is the one printed in full on `07_complete-code` plus the component files named there.

  Recorded output:

```text
[1] Nodes=3 Links=2
[2] root: Completed data=tick->bias->print attempt=1 outcome=Completed
[2] orders: 0,1,2
[2] entries=1 first=ChainSegment
[2] outline: Execute | TickerNode → BiasNode → PrinterNode
[3] result: Completed data=tick->bias reached=True
[4] copy: Nodes=3 Links=2 Completed data=tick->bias->print
[5] paused: status=Paused isPaused=True running=True data=<null>
[5] resumed: status=Completed data=tick->bias->print outcome=Completed
[6] observed: NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
[6] sink on a clean run: 0 records
[7] checkpoint: attempt=1 outputs=1 shape=<three RuntimeId GUIDs>
[7] resume: status=Completed data=tick->bias->print outcome=Completed
[7] refused on a serialized copy: The checkpoint does not belong to this graph status=Idle
[8] retry: status=Completed data=ok drives=3 attempt=1 outcome=Completed
[8] retry logs: 01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
[9] logfile: fileLines=3 retained=2 snapshot=2
[9] retained: 02. BiasNode | 03. PrinterNode
[9] file head: 01. TickerNode
[10] compensate: status=Stopped outcome=Failed currentOrder=-1 reversed=[BoomNode]
[11] segments: ChainSegment, ParallelSegment
[11] MaxParallelBranches=null: overlap=True
[11] MaxParallelBranches=1:    overlap=False
```

  Every line matches the **Expected result** stated on the step it belongs to. Three lines worth reading twice:

  - `[8] … attempt=1` — a retry is **not** a pass over the graph, so the output registry's pass stamp does not move and join aggregation stays correct.
  - `[7] … refused … status=Idle` — the resume was refused *before the session was touched*, which is why `Status` still reads `Idle` rather than lying about a run that never happened.
  - `[11] … overlap=True` / `overlap=False` — the fan-out really is concurrent by default and serialised by a cap of one.

- ✅ **Also verified by the shipped test suite** (read, not re-executed): every contract above is pinned by the named tests in section 1, including the `MaxParallelBranches` cap and `MaxRetainedLogs` behavior, which no demo exercises.
- ⚠️ **Not verified by running a GUI host.** The per-platform demos (`Examples/Workflow/WPF/Demo`, `Avalonia/Demo`, `Blazor/Demo`, `MAUI/Demo`, `WinUI/Demo`, `WinForms/Demo`, `Jalium/Demo`) were **not** built or launched — they are GUI hosts (`net9.0-windows` for WPF, `net8.0` for Avalonia, plus MAUI/WinUI/Blazor workloads) whose claims on these pages are read from their source, not from a running app. Treat "where this lives in the real repository" as source-verified, not run-verified.
- ⚠️ **One claim I could not pin down.** Splitting the Quick Start's components across separate files is what the verified build used (and what the demo repository does). A probe with two generated components in **one** file also compiled, so "one component per file" is the demo's convention rather than a hard generator requirement; the single-file form of the *whole* program was not re-verified.
