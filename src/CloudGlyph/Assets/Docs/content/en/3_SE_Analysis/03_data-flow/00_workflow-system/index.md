# Data Flow — Workflow System

PlantUML sequence diagrams trace the core data flows of the workflow-system feature. Participants are declared before use, `activate`/`deactivate` are balanced, and `alt/else/end` blocks are balanced.

## Sub-pages

| Page | Flow |
|---|---|
| [Connect Flow](00_connect/index.md) | Build one connection: `SendConnection` → `ReceiveConnection` → `CreateLink` |
| [Compile and Run (Root)](01_compile-and-run/index.md) | Compile a graph (`CompileRole.Root`) and drive it with `RuntimeEngine.RunAsync` |
| [Reverse / Terminal Cone Flow](02_terminal-cone/index.md) | Reverse-compile a result (`CompileRole.Terminal`) and track `Target` / `TargetReached` |
| [Redirect Re-run](03_redirect/index.md) | An in-node `Error()` → `IRedirectable` → whole-graph re-run |
| [Parallel Fan-Out and Its Concurrency Cap](04_parallel-and-cap/index.md) | A fan-out group running concurrently, and `MaxParallelBranches` serialising it |
| [Resume From a Checkpoint](05_resume-from-checkpoint/index.md) | Write a checkpoint after each success, then resume from it (and have a foreign one refused) |
| [Broadcast Dispatch (non-Compiler)](06_broadcast/index.md) | Edge-level broadcast dispatch (`StandardBroadcastAsync`) — the non-Compiler path |
| [Host Capabilities Around One Drive](07_host-capabilities/index.md) | The capabilities wrapped around a single node drive: gate, observer, retry, error sink, compensation |

## Where the flows meet

Every path above ends in the same method — `IWorkflowNodeViewModelHelper.ReceiveAsync(ITaskContext, CancellationToken)` — and a node tells them apart only by the **context type** it receives. The Compiler path passes the run's `IRuntimeContext`; the broadcast path passes a fresh `TaskContext` per edge. For the parameter-by-parameter comparison see the `05_execution-mechanism` page in the API dimension.

Two invariants hold across all the diagrams:

- **The engine owns downstream dispatch during a compiled run.** Nodes are driven through their helper directly; their `ReceiveCommand` / `BroadcastCommand` are never triggered (`EntrySemanticsTests.CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`).
- **`context.Data` is the only meaningful member under a compiled run.** `Sender` and `Receiver` are always `null` there, because the engine drives the graph rather than its edges.
