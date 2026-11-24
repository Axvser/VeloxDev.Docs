# Runtime context

The session is both the `IRuntimeContext` the engine writes and the `ITaskContext` each node receives. `RuntimeContext` is the concrete default; the optional capabilities live on it and are deliberately not on the interface, so adding them does not break external implementations.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## IRuntimeContext

**Signature:** `interface IRuntimeContext : ITaskContext`

| Member | Type | Description |
| --- | --- | --- |
| `Uid` | `Guid` | Unique run-session identifier. |
| `Sequence` | `int` | Next log sequence number. |
| `Logs` | `ObservableCollection<string>` | Formatted log lines. |
| `CurrentEntry` | `CompileSegment?` | Segment currently executing. |
| `NodeIndex` | `int` | Index of the current node within its chain. |
| `BranchKey` | `object?` | Current branch key. |
| `Attempt` | `int` | Pass number over the graph; a redirect increments it, a retry does not. |
| `IsRunning` | `bool` | Whether a run is in progress. |
| `Status` | `string` | `Idle`, `Running`, `Paused`, `Completed` or `Stopped`. |
| `CurrentOrder` | `int` | The current node's compile-fixed order; `-1` on a stop. |
| `Target` | `INodeComponent?` | Optional node the caller wants reached. |
| `TargetReached` | `bool` | Set once `Target` is actually driven. |
| `Data` | `object?` | Chained payload; the interface adds a setter over `IContext.Data`. |
| `RedirectRequested` | `bool` | Whether the current drive reported anything. |
| `EndedWithError` | `bool` | Whether the flow ended early as a failure. |
| `PendingRedirectTarget` | `int?` | Engine-requested redirect target order. |
| `ActiveRedirectTarget` | `int?` | The pass's re-run target order. |
| `Log(string entry)` | `void` | Writes a plain line. |
| `Error(string message)` | `void` | Writes `[Error]` and marks the run to stop/redirect. |
| `Warn(string message)` | `void` | Writes `[Warning]`; the run continues with the value. |
| `ErrorAsync(string message)` / `WarnAsync(string message)` | `Task` | The line plus the host's `IExecutionErrorSink` record. |
| `Set(string key, object? value)` / `TryGet(string key, out object? value)` | `void` / `bool` | Shared variables (case-insensitive keys). |
| `RegisterOutput(INodeComponent node, object? value)` | `void` | Registers a node's output for this pass. |
| `ResetOutputs()` | `void` | Clears the output registry; called once per `RunAsync`. |
| `CollectGroupedInputs(IEnumerable<INodeComponent> inputNodes)` | `IReadOnlyDictionary<INodeComponent, object?>` | Outputs valid for this pass, keyed by source node. |

## RuntimeContext

**Signature:** `sealed partial class RuntimeContext : IRuntimeContext`

Implements every member above. Additional public members:

| Member | Type | Description |
| --- | --- | --- |
| `IsCompilePhase` | `bool` | Always `false`. |
| `Target` / `TargetReached` | | Target tracking. |
| `MaxParallelBranches` | `int?` | Cap on concurrent fan-out branches; null means no cap. |
| `PendingRedirectTarget` / `ActiveRedirectTarget` | `int?` | Redirect bookkeeping. |
| `Next()` | `int` | Atomically increments and returns the sequence number. |
| `LogWriter` | `ILogWriter?` | Diverts lines in addition to `Logs`. |
| `MaxRetainedLogs` | `int?` | Bound on the in-memory view; null keeps everything, `0` keeps none. |
| `ExecutionGate` | `IExecutionGate?` | Pause point between nodes. |
| `Observer` | `IExecutionObserver?` | Run timeline receiver. |
| `RetryPolicy` | `INodeRetryPolicy?` | Decides whether a thrown failure is retried. |
| `ErrorSink` | `IExecutionErrorSink?` | Structured failure receiver. |
| `HostRedirect` | `Func<IRuntimeContext, INodeComponent, INodeComponent?>?` | Fallback for nodes that do not implement `IRedirectable`. |
| `Compensation` | `IExecutionCompensation?` | Told about nodes a failed/cancelled run drove. |
| `CheckpointStore` | `IExecutionCheckpointStore?` | Where the run's place is saved. |
| `Outcome` | `RunOutcome` | Precise reading of `Status` + `EndedWithError`. |
| `LogWriteFailed` | `EventHandler<LogWriteFailedEventArgs>` | Raised when `LogWriter` throws. |
| `SnapshotLogs()` | `string[]` | Point-in-time copy, safe while the run appends. |

`Outcome` is `Unknown` until a run ends. It is only set on the concrete `RuntimeContext`; a host-supplied `IRuntimeContext` implementation keeps its own status and does not receive it.

## Capability resolution

The engine reads the optional capabilities only from the concrete `RuntimeContext` (or from the session behind a fan-out's `BranchRuntimeContext`). A host that implements `IRuntimeContext` itself therefore gets plain execution plus the log, but no gate, observer, retry, sink, compensation, checkpoint or host redirect. `MaxParallelBranches` and `LogWriter` follow the same rule.

`HostRedirect` is asked only for nodes that do not implement `IRedirectable`. A node's own invalid target is logged and ignored, and the flow carries on; an invalid host answer ends the flow, because a host that tried to place the run and named something impossible has a bug.

## Logs and threading

`Logs` is an `ObservableCollection<string>` guarded by an internal lock. The run may append while another thread enumerates, so outside the run's own thread use `SnapshotLogs()` instead of enumerating `Logs`.

Line format: `"{sequence:00}. {text}"`, with `[Error]`, `[Warning]`, `[Retry n]`, `[Checkpoint]`, `[Compensation]` and `[ErrorSink]` markers where applicable. A writer receives the line **before** the retention check and is called on the thread driving the run.

## Example

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    MaxRetainedLogs = 100,
    MaxParallelBranches = 4,
};

session.Log("before run");
Console.WriteLine(string.Join("\n", session.SnapshotLogs()));   // 01. before run
Console.WriteLine(session.Outcome);                             // Unknown

session.Set("region", "eu");
Console.WriteLine(session.TryGet("REGION", out var region) + " " + region); // True eu
```
