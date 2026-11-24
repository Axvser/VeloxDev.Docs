# Workflow runtime

`RuntimeEngine.RunAsync` drives a `CompiledGraph`: it walks the compiled segments, calls each node's `ReceiveAsync`, and writes the returned value into the session for the next node. The graph decides the shape; the engine decides the path, the payload and how the run ends.

- [Runtime engine](00_runtime-engine/index.md) — `RuntimeEngine`, `RunOutcome`, the data-flow contracts and `IGroupData`.
- [Runtime context](01_runtime-context/index.md) — `IRuntimeContext` and `RuntimeContext`, including the optional capabilities.
- [Resilience contracts](02_resilience-contracts/index.md) — redirect, retry, pause gate, observer, error sink and compensation.
- [Checkpoint and log](03_checkpoint-and-log/index.md) — `ExecutionCheckpoint`, `IExecutionCheckpointStore` and the log-writer contracts.

```csharp
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Status} {session.Outcome} {session.Data}");
```

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx` in `VeloxDev.Core`. Every capability beyond plain execution is optional and configured on the session; with none configured the run behaves as it did before those capabilities existed. For a task-oriented walkthrough, see [Workflow runtime](../../1_QuickStart/05_workflow-runtime/index.md).
