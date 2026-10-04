# Workflow System — Execution Contracts

The seven optional seams a host plugs into a compiled run, plus their payload types. Every contract here is read off the host's `RuntimeContext`; with none configured the run behaves exactly as it did before they existed (see `RuntimeContext — host capabilities`).

Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Contracts/` — `IExecutionGate.cs`, `IExecutionObserver.cs`, `INodeRetryPolicy.cs`, `IExecutionErrorSink.cs`, `IExecutionCompensation.cs`, `IExecutionCheckpointStore.cs`, `ILogWriter.cs`.

## The seven seams

| Contract | Session property | One line |
|---|---|---|
| `IExecutionGate` | `ExecutionGate` | Pauses the run between nodes. |
| `IExecutionObserver` | `Observer` | Watches what the run did, in order. |
| `INodeRetryPolicy` | `RetryPolicy` | Decides whether a node that threw gets another go. |
| `IExecutionErrorSink` | `ErrorSink` | Receives failures as records rather than log lines. |
| `IExecutionCompensation` | `Compensation` | Hands back the successes of a run that ended badly. |
| `IExecutionCheckpointStore` | `CheckpointStore` | Writes down the run's place so a later run can pick it up. |
| `ILogWriter` | `LogWriter` | Diverts the run's lines out of memory. |

This page covers the first two. The others have their own pages:

- `Retry and error sinks` — `INodeRetryPolicy`, `NodeFailure`, `IExecutionErrorSink`, `ExecutionError`, `ExecutionFailurePhase`, `ExecutionReportLevel`
- `Compensation, checkpoints and logs` — `IExecutionCompensation`, `NodeCompensation`, `IExecutionCheckpointStore`, `ILogWriter`, `LogWriteFailedEventArgs`

---

## `IExecutionGate`

The pause point of a compiled run. `RuntimeEngine` awaits it before driving each node, so a host can hold a long run and let it go again.

#### `IExecutionGate.WaitAsync`

**Signature:** `Task WaitAsync(CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `cancellationToken` | `CancellationToken` | The run's token. It **must** be honoured. |

**Returns:** `Task` — a completed task lets the run proceed; holding the returned task pauses it. The same gate is asked again before the next node, so releasing it resumes the run.

**Exceptions:**

| Exception | Condition |
|---|---|
| `OperationCanceledException` | Required on cancellation. `RuntimeEngine.RunAsync` turns it into `Status = "Stopped"`. |

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
Gate.Resume();                          // a run never starts holding the last run's pause
context.ExecutionGate = Gate;           // Gate is a ManualExecutionGate
```

**Notes:**

- **It pauses between nodes, never inside one.** A node already being driven runs to completion — the same rule the tool layer states for half-finished mutations, and the reason a pause cannot corrupt a graph.
- **Cancellation must *throw*, not return.** Returning normally on cancellation would leave the caller looping, and a run stopped by the host while paused has to end rather than hang.
- While the gate holds, the engine writes `Status = "Paused"` and puts it back to `"Running"` on release — a paused run has no other bindable state, since `IsRunning` only distinguishes running from not. An open gate costs nothing: the engine checks `IsCompleted` first and does not even write the status.
- Inside a fan-out the gate is resolved through the branch facade, so it holds the branches too (`ExecutionGateTests.AClosedGate_AlsoHoldsTheBranchesOfAFanOut`).

---

## `IExecutionObserver`

Watches a compiled run: who was driven, in what order, how it went. The seam to hang OpenTelemetry (or anything else that wants a run's timeline) on.

#### `IExecutionObserver.OnObservedAsync`

**Signature:** `Task OnObservedAsync(ExecutionObservation observation, CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `observation` | `ExecutionObservation` | What happened: kind, node, detail, attempt, elapsed. |
| `cancellationToken` | `CancellationToken` | The run's token. |

**Returns:** `Task`. Must not block — the run is waiting on it.

**Exceptions:** none that reach the run. **A broken observer never changes a run**: a throw is swallowed and written to the run's own log (`[Observer] {kind} was not observed: {message}`), because an observation is a diagnostic and not evidence.

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.Observer = new DelegateExecutionObserver(Observe);

// Only the summary is written, on RunEnded — a run drives twenty-odd nodes and a line each would drown the log.
private void Observe(ExecutionObservation observation)
{
    switch (observation.Kind)
    {
        case ExecutionObservationKind.NodeStarted:
            _nodesDriven++;
            break;
        case ExecutionObservationKind.NodeRetried:
            _retries++;
            break;
        case ExecutionObservationKind.RunEnded:
            var outcome = (Controller.RuntimeContext as RuntimeContext)?.Outcome;
            Controller.RuntimeContext?.Log(
                $"[Observer] {_nodesDriven} nodes driven, {_retries} retried, pass {observation.Attempt}, " +
                $"{observation.Elapsed.TotalSeconds:0.0}s, {outcome}");
            _nodesDriven = 0;
            _retries = 0;
            break;
    }
}
```

### `ExecutionObservationKind`

**Signature:** `public enum ExecutionObservationKind`

| Member | Value | `Observation.Node` |
|---|---|---|
| `RunStarted` | 0 | `null` |
| `BranchStarted` | 1 | `null`; the detail carries `"branch {index}"` |
| `NodeStarted` | 2 | the node about to be driven |
| `NodeSucceeded` | 3 | the node that returned without throwing |
| `NodeFailed` | 4 | the node that threw or requested a redirect; the detail carries the message |
| `NodeRetried` | 5 | the node being driven again; the detail carries the retry number |
| `RunEnded` | 6 | `null`; the elapsed time is the whole run's |

### `ExecutionObservation`

**Signature:**

```csharp
public readonly record struct ExecutionObservation(
    ExecutionObservationKind Kind,
    IWorkflowNodeViewModel? Node,
    string? Detail,
    int Attempt,
    TimeSpan Elapsed);
```

| Field | Type | Description |
|---|---|---|
| `Kind` | `ExecutionObservationKind` | What happened. |
| `Node` | `IWorkflowNodeViewModel?` | The node this is about, or `null` for a run- or branch-level observation. |
| `Detail` | `string?` | Free-form context: a failure message, a retry counter, a branch key. |
| `Attempt` | `int` | The run's attempt number — which pass over the graph this is. A retry is **not** a new attempt and does not move it. |
| `Elapsed` | `TimeSpan` | How long the step took, where that is meaningful. |

**Notes:** one shape with a kind — rather than one method per kind — so a new kind does not break an existing observer; it is the same shape the run's own events already take in this library.

**Observed order for a linear chain (Test):**

```text
RunStarted, NodeStarted, NodeSucceeded, NodeStarted, NodeSucceeded, RunEnded
```

`CompilerEx/ExecutionObserverTests.cs` — `AChain_ReportsRunAndNodeStartAndSuccess_InDriveOrder`; `AFanOut_ReportsEveryBranch` counts two `BranchStarted` and three `NodeStarted` (the source plus both branch nodes); `AThrowingObserver_ChangesNothingAboutTheRun` pins that a throwing observer leaves `Status == "Completed"`.

## Sub-pages

| Page | Contents |
|---|---|
| [Retry Policy and Error Sink](01_retry-and-error-sinks/index.md) | `INodeRetryPolicy`, `NodeFailure`, `IExecutionErrorSink`, `ExecutionError`, `ExecutionFailurePhase`, `ExecutionReportLevel` |
| [Compensation, Checkpoints and Log Writers](02_compensation-checkpoints-and-logs/index.md) | `IExecutionCompensation`, `NodeCompensation`, `IExecutionCheckpointStore`, `ILogWriter`, `LogWriteFailedEventArgs` |
