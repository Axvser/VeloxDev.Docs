# Error sink and compensation

The engine already writes each failure as a log line. A sink turns those failures into records, and a compensator is told which nodes a bad run already drove — the engine itself rolls nothing back.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## ExecutionFailurePhase

**Signature:** `enum ExecutionFailurePhase`

| Value | Meaning |
| --- | --- |
| `Node = 0` | A node threw or reported an error. |
| `Router` | A router threw while resolving its key. |
| `Redirect` | A node or host policy threw while resolving a redirect. |
| `Run` | The run itself failed: the redirect cap, or a cancellation. |

## ExecutionReportLevel

**Signature:** `enum ExecutionReportLevel`

| Value | Meaning |
| --- | --- |
| `Warning = 0` | A node called `WarnAsync`; nothing went wrong. |
| `Error` | A node called `ErrorAsync`, threw, or the engine gave up. |

Everything the engine records on its own is an error.

## ExecutionError

**Signature:** `readonly record struct ExecutionError(ExecutionFailurePhase Phase, INodeComponent? Node, string Message, Exception? Error, int Attempt, int Order, ExecutionReportLevel Level = ExecutionReportLevel.Error)`

| Member | Type | Description |
| --- | --- | --- |
| `Phase` | `ExecutionFailurePhase` | Where the failure came from. |
| `Node` | `INodeComponent?` | The node, or null for a run-level failure. |
| `Message` | `string` | The message the engine recorded. |
| `Error` | `Exception?` | The exception, when there was one. |
| `Attempt` | `int` | The pass number. |
| `Order` | `int` | The node's compile order, or `-1`. |
| `Level` | `ExecutionReportLevel` | Warning or error. |

## IExecutionErrorSink

**Signature:** `interface IExecutionErrorSink`

| Member | Type | Description |
| --- | --- | --- |
| `OnErrorAsync(ExecutionError error, CancellationToken cancellationToken)` | `Task` | Called once per record, in order. |

Two ways in: the engine reports what it sees itself, and a node reports through `ErrorAsync`/`WarnAsync` (which await the sink). The synchronous `Error`/`Warn` write to the log only, because they must stay non-blocking. A sink that throws is swallowed and logged; reporting a failure must not add one. The token is the run's for engine reports and `CancellationToken.None` for a node's own report.

## DelegateExecutionErrorSink

**Signature:** `sealed class DelegateExecutionErrorSink(Action<ExecutionError> observe) : IExecutionErrorSink`

Wraps a synchronous action; throws `ArgumentNullException` for a null delegate.

## NodeCompensation

**Signature:** `readonly record struct NodeCompensation(INodeComponent Node, object? Output, int Order)`

| Member | Type | Description |
| --- | --- | --- |
| `Node` | `INodeComponent` | A node the run drove. |
| `Output` | `object?` | What it produced; null when that drive failed. |
| `Order` | `int` | Compile order, or `-1`. |

## IExecutionCompensation

**Signature:** `interface IExecutionCompensation`

| Member | Type | Description |
| --- | --- | --- |
| `CompensateAsync(NodeCompensation compensation, CancellationToken cancellationToken)` | `Task` | Called once per driven node, most recent first. |

- Called only when the run ends `Failed` or `Cancelled`; a completed run compensates nothing.
- Every node the run registered is included, including the one that failed (with a null output) and nodes the redirect prefix preserved.
- Called most recent first, in drive order reversed; rerun nodes appear once, at their latest position.
- The cleanup token is **not** the run's: after cancellation, that one is already cancelled.
- A compensation that throws is logged and the rest still run.
- The tree's undo stack is not a substitute: it records model-structure changes only, has no run boundary and does not guarantee a complete chain.

## DelegateExecutionCompensation

**Signature:** `sealed class DelegateExecutionCompensation(Action<NodeCompensation> compensate) : IExecutionCompensation`

Wraps a synchronous action; throws `ArgumentNullException` for a null delegate.

## Example

```csharp
var compensated = new List<string>();
var session = new RuntimeContext
{
    Data = "seed",
    ErrorSink = new DelegateExecutionErrorSink(e => Console.WriteLine($"{e.Phase}:{e.Level}:{e.Message}")),
    Compensation = new DelegateExecutionCompensation(
        c => compensated.Add($"{c.Node.GetType().Name}:{c.Output ?? "null"}")),
};

await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Outcome} [{string.Join(",", compensated)}]");
```
