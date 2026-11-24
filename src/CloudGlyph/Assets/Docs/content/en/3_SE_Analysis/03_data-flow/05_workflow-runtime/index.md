# Workflow runtime

`RuntimeEngine.RunAsync` drives a `CompiledGraph`. It walks each segment, calls the node's `ReceiveAsync`, and writes the returned value into the session for the next node. The graph decides the shape; the engine decides the path, the payload and how the run ends.

The analysis splits into two operations:

- [Execution loop](00_execution-loop/index.md) — `RunAsync`, segment dispatch, node driving, joins and redirect.
- [Resilience and checkpoint](01_resilience-and-checkpoint/index.md) — pause gate, retry, observer, error sink, compensation, checkpoint and log writer.

```csharp
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Status} {session.Outcome} {session.Data}");
```

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.
