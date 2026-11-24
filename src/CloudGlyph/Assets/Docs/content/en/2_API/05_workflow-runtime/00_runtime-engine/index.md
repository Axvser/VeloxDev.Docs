# Runtime engine

The engine walks a compiled graph entry by entry. `ChainSegment` drives its nodes in order; `BranchSegment` drives the router and then the chosen option; `ParallelSegment` starts every branch from the same payload. A node's return value becomes the next node's payload.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx` (engine and run outcome) and `VeloxDev.WorkflowSystem` (data-flow contracts).

## RuntimeEngine

**Signature:** `sealed class RuntimeEngine`

### RunAsync

**Signature:** `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct, ExecutionCheckpoint? resumeFrom = null)`

| Parameter | Type | Description |
| --- | --- | --- |
| `graph` | `CompiledGraph` | The graph to drive; a null graph returns immediately. |
| `context` | `IRuntimeContext` | The session; a null context returns immediately. |
| `ct` | `CancellationToken` | Cancelling stops the run at the next node boundary. |
| `resumeFrom` | `ExecutionCheckpoint?` | A checkpoint to carry on from; its shape must match `graph`. |

**Returns:** `Task` — completes when the run ends. The result is written to the session: `Status`, `EndedWithError`, `Outcome`, `Data`, `Attempt`, `Logs`.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `InvalidOperationException` | `resumeFrom` was taken over a different graph, or the redirect cap (50) is exceeded. |

The checkpoint shape is checked **before** the session is touched, so a refused resume leaves `Status` at `Idle`.

## Execution semantics

- **Chains** run in segment order. A later pass skips nodes whose `Order` is below a redirect target; a skipped node's registered output is re-applied to `Data` so the target receives the same payload as the previous pass.
- **Branches** drive the router, then select an option with `Equals(option.Key, key)`. A missing or terminal option ends the run with `Completed`.
- **Fan-out** branches run concurrently as interleaved async operations, each with its own `BranchRuntimeContext` (payload and redirect request are branch-local; logs, identity and the output registry are shared). The first redirect request in branch order wins; a terminal branch ends the whole run.
- **Joins** are detected by the compiler: when a node's `InputNodes` has more than one entry, `Data` is replaced with a `GroupData` over the upstream outputs.
- **Failures**: `Warn` is a note and the value still flows; `Error` or an uncaught exception counts as a `null` result and either redirects through `IRedirectable`/`HostRedirect` or ends the flow with `EndedWithError` and `Status = "Stopped"`.
- **Cancellation** sets `Status = "Stopped"`, `EndedWithError = false`, so `Outcome` is `Cancelled`.
- **Attempt** counts passes over the graph; a redirect increments it, a retry does not.

## RunOutcome

**Signature:** `enum RunOutcome`

| Value | Condition |
| --- | --- |
| `Unknown = 0` | Not started, or still going. |
| `Completed` | `Status == "Completed"`; every entry was walked. |
| `Cancelled` | `Status == "Stopped"` and `EndedWithError == false`. |
| `Failed` | `Status == "Stopped"` and `EndedWithError == true`. |

There is deliberately no `Stopped` member: both paths that produce that string are covered by `Cancelled` and `Failed`.

## Data-flow contracts

### IContext

**Signature:** `interface IContext` — `object? Data { get; }`.

### IAccessContext

**Signature:** `interface IAccessContext : IContext`

| Member | Type | Description |
| --- | --- | --- |
| `IsCompilePhase` | `bool` | `true` for a static compile check, `false` at run time. |
| `Sender` | `ISlotComponent?` | Upstream output slot. |
| `Receiver` | `ISlotComponent?` | Downstream input slot. |

### ITaskContext

**Signature:** `interface ITaskContext : IAccessContext` — adds no members; it is the payload shape `ReceiveAsync` receives.

### TaskContext

**Signature:** `readonly struct TaskContext : ITaskContext`

| Member | Type | Description |
| --- | --- | --- |
| `TaskContext(object? data = null, ISlotComponent? sender = null, ISlotComponent? receiver = null)` | constructor | Carries the payload and the edge ends. |
| `IsCompilePhase` | `bool` | Always `false`. |
| `Data` / `Sender` / `Receiver` | | The stored values; all nullable. |
| `Deconstruct(out object?, out ISlotComponent?, out ISlotComponent?)` | `void` | Tuple-style unpacking. |

## IGroupData and GroupData

**Signature:** `interface IGroupData : IReadOnlyDictionary<INodeComponent, object?>`

`GroupData` (`readonly struct`, `IGroupData`) wraps a read-only dictionary. The key is the **source node reference**, the value is that node's output for the run. An upstream that was not driven this pass is absent, so `TryGetValue` returns `false` rather than a stale value; the indexer throws `KeyNotFoundException` for an absent key.

```csharp
var group = (IGroupData)ctx.Data!;
foreach (var pair in group)
    Console.WriteLine($"{pair.Key.GetType().Name}={pair.Value}");
```

## Example

```csharp
var graph = (await new CompilerViewModel().CompileAsync(start, CompileRole.Root))[0];
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);

Console.WriteLine($"{session.Status} / {session.Outcome} / attempt {session.Attempt}");
Console.WriteLine(session.Data);
```
