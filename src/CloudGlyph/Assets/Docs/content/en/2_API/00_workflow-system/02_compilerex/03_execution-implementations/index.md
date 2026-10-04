# Workflow System — Execution Implementations

The implementations that ship with the execution contracts. Every seam has a delegate form for a host that already has the logic, and the two that need real behavior — the pause gate and the retry policy — have a concrete class.

Sources: `Runtime/Model/ExecutionGates.cs`, `ExecutionObservers.cs`, `ErrorSinks.cs`, `Compensations.cs`. Log writers and the retry policy are on `the next page`.

## What ships with what

| Contract | Implementations |
|---|---|
| `IExecutionGate` | `DelegateExecutionGate`, `ManualExecutionGate` |
| `IExecutionObserver` | `DelegateExecutionObserver` |
| `IExecutionErrorSink` | `DelegateExecutionErrorSink` |
| `IExecutionCompensation` | `DelegateExecutionCompensation` |
| `ILogWriter` | `DelegateLogWriter`, `TextWriterLogWriter` |
| `INodeRetryPolicy` | `ExponentialBackoffRetry` |
| `IExecutionCheckpointStore` | `InMemoryCheckpointStore` (Core), `FileCheckpointStore` (`VeloxDev.Core.Extension`) |

---

## `DelegateExecutionGate`

**Signature:** `public sealed class DelegateExecutionGate(Func<CancellationToken, Task> wait) : IExecutionGate`

The one-liner form for a host that already has the logic.

| Member | Signature | Notes |
|---|---|---|
| constructor | `DelegateExecutionGate(Func<CancellationToken, Task> wait)` | Throws `ArgumentNullException` when `wait` is `null`. |
| `WaitAsync` | `Task WaitAsync(CancellationToken)` | Calls `_wait(cancellationToken)`. |

---

## `ManualExecutionGate`

**Signature:** `public sealed class ManualExecutionGate : IExecutionGate`

A gate the host opens and closes by hand: `Pause` holds the run at its next node boundary, `Resume` lets it go. Releasable from any thread — including the one the run is on.

| Member | Type | Description |
|---|---|---|
| `IsPaused` | `bool` | Whether the run is currently held. |
| `Pause()` | `void` | Holds the run at its next node boundary. Idempotent while already paused. |
| `Resume()` | `void` | Lets a held run continue. A no-op when it is not held. |
| `WaitAsync(CancellationToken)` | `Task` | Returns a completed task while the gate is open; otherwise waits on the parked gate. |

**Exceptions:** `WaitAsync` throws `OperationCanceledException` when the token fires — cancellation throws rather than returning, because a caller that came back without the gate being opened would keep driving, which is the opposite of stopping.

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
public ManualExecutionGate Gate { get; } = new();

// A run never starts holding the last run's pause: the gate is the host's hand, and each Run is a new round.
context.ExecutionGate = Gate;
```

**Verified behavior (Test — `CompilerEx/ExecutionGateTests.cs`, and reproduced against the shipped library):**

| Assertion | Value |
|---|---|
| `b.Calls` while held | empty — a held run must not drive the next node |
| `context.IsRunning` while held | `true` — paused is not stopped |
| `context.Status` while held | `"Paused"` |
| `context.Status` after `Resume` | `"Completed"` |

**Notes:**

- Built the way this repository already builds "hold here until someone says go" (`VeloxDev.Core.Timing.TimeSourceCore`): a `TaskCompletionSource<bool>` that exists **only** while the gate is closed, replaced rather than completed in place, and completed **outside** the lock. The last two are not style — completing under the lock re-enters continuations that may come straight back for the same lock, and a blocking wait on the caller's thread would deadlock a UI-driven run. No boolean is polled: a run that spun on a flag would burn the thread it is supposed to be yielding.
- An open gate costs nothing: `WaitAsync` returns a completed task without allocating.
- A paused run cancelled by the host ends rather than hangs: `Status = "Stopped"`, `Outcome = RunOutcome.Cancelled`.

---

## `DelegateExecutionObserver`

**Signature:** `public sealed class DelegateExecutionObserver(Action<ExecutionObservation> observe) : IExecutionObserver`

The one-liner form for a host wiring a panel or a counter. `OnObservedAsync` calls `_observe(observation)` and returns `Task.CompletedTask` — called once per observation, on the thread driving the run. The constructor throws `ArgumentNullException` when `observe` is `null`.

---

## `DelegateExecutionErrorSink`

**Signature:** `public sealed class DelegateExecutionErrorSink(Action<ExecutionError> observe) : IExecutionErrorSink`

The one-liner form for a host that just counts or stores. `OnErrorAsync` calls `_observe(error)` and returns `Task.CompletedTask`. The constructor throws `ArgumentNullException` when `observe` is `null`.

**Example (Demo):** `new DelegateExecutionErrorSink(Diagnostics.Add)`, where `Diagnostics` is an `ObservableCollection<ExecutionError>`.

---

## `DelegateExecutionCompensation`

**Signature:** `public sealed class DelegateExecutionCompensation(Action<NodeCompensation> compensate) : IExecutionCompensation`

The one-liner form for a host undoing one thing per node. `CompensateAsync` calls `_compensate(compensation)` and returns `Task.CompletedTask` — once per successfully driven node, most recent first. The constructor throws `ArgumentNullException` when `compensate` is `null`.

## Sub-pages

| Page | Contents |
|---|---|
| [Log Writers and the Retry Policy](01_log-writers-and-retry/index.md) | `DelegateLogWriter`, `TextWriterLogWriter`, `ExponentialBackoffRetry` |
