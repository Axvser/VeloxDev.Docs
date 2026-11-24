# Gate and observer

A run can be held between nodes and watched as a timeline. Neither capability is required, and neither can change where the run goes.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## IExecutionGate

**Signature:** `interface IExecutionGate`

| Member | Type | Description |
| --- | --- | --- |
| `WaitAsync(CancellationToken cancellationToken)` | `Task` | Awaited before each node; hold the returned task to pause. |

The gate pauses **between** nodes, never inside one: a node already being driven runs to completion. Cancellation must throw rather than return, so a stopped run does not keep driving. While the gate holds, `IRuntimeContext.Status` is `Paused` and `IsRunning` stays `true`; on release it returns to `Running`.

## ManualExecutionGate

**Signature:** `sealed class ManualExecutionGate : IExecutionGate`

| Member | Type | Description |
| --- | --- | --- |
| `IsPaused` | `bool` | Whether the run is currently held. |
| `Pause()` | `void` | Holds the run at its next node boundary; idempotent. |
| `Resume()` | `void` | Releases a held run; no-op when not held. |
| `WaitAsync(CancellationToken)` | `Task` | Returns a completed task while open; otherwise waits and throws `OperationCanceledException` if the token fires. |

`Pause` and `Resume` are safe from any thread, including the one the run is on. The gate is a `TaskCompletionSource` that exists only while closed, completed outside its lock.

## DelegateExecutionGate

**Signature:** `sealed class DelegateExecutionGate(Func<CancellationToken, Task> wait) : IExecutionGate`

Wraps a delegate; throws `ArgumentNullException` for a null delegate. `WaitAsync` forwards to it.

## ExecutionObservationKind

**Signature:** `enum ExecutionObservationKind`

| Value | Meaning |
| --- | --- |
| `RunStarted = 0` | The run began; `Node` is null. |
| `BranchStarted` | A fan-out branch began; `Node` is null. |
| `NodeStarted` | A node is about to be driven. |
| `NodeSucceeded` | A node returned without throwing. |
| `NodeFailed` | A node threw or reported an error. |
| `NodeRetried` | A node is being driven again; the retry number is in `Detail`. |
| `RunEnded` | The run ended; `Node` is null. |

## ExecutionObservation

**Signature:** `readonly record struct ExecutionObservation(ExecutionObservationKind Kind, INodeComponent? Node, string? Detail, int Attempt, TimeSpan Elapsed)`

`Attempt` is the run's pass number, not the retry number. `Detail` is free-form: a failure message, a retry counter, a branch label.

## IExecutionObserver

**Signature:** `interface IExecutionObserver`

| Member | Type | Description |
| --- | --- | --- |
| `OnObservedAsync(ExecutionObservation observation, CancellationToken cancellationToken)` | `Task` | Called once per observation; must not block. |

A broken observer never changes the run: an exception is logged and the drive continues. Nothing is observed while `RuntimeContext.Observer` is null.

## DelegateExecutionObserver

**Signature:** `sealed class DelegateExecutionObserver(Action<ExecutionObservation> observe) : IExecutionObserver`

Wraps a synchronous action; throws `ArgumentNullException` for a null delegate.

## IRuntimeAware

**Signature:** `interface IRuntimeAware`

| Member | Type | Description |
| --- | --- | --- |
| `AttachRuntimeContext(IRuntimeContext context)` | `void` | Receives the session immediately before each drive. |

The same object is already the parameter `ReceiveAsync` receives, so implementing this loses nothing and changes no behaviour. Use it only when the node wants the session outside a drive, for example to bind progress. An exception here is logged and the drive continues.

## Example

```csharp
var gate = new ManualExecutionGate();
var observed = new List<ExecutionObservationKind>();
var session = new RuntimeContext
{
    Data = "seed",
    ExecutionGate = gate,
    Observer = new DelegateExecutionObserver(o => observed.Add(o.Kind)),
};

var run = new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
gate.Resume();   // or Pause() from inside a node handler
await run;

Console.WriteLine(session.Status);          // Completed
Console.WriteLine(string.Join(",", observed));
```
