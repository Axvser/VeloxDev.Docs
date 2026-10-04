# Workflow System — Retry Policy and Error Sink

Two seams about things going wrong: `INodeRetryPolicy` decides whether a node that threw gets another go, and `IExecutionErrorSink` receives every failure as a record rather than only as a log line.

Sources: `Runtime/Contracts/INodeRetryPolicy.cs`, `Runtime/Contracts/IExecutionErrorSink.cs`.

---

## `INodeRetryPolicy`

#### `INodeRetryPolicy.NextRetryAsync`

**Signature:** `Task<TimeSpan?> NextRetryAsync(NodeFailure failure, CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `failure` | `NodeFailure` | The node that failed, what it threw, which retry this is, and how long the failed attempt took. |
| `cancellationToken` | `CancellationToken` | The run's token. The engine also honours it during the wait. |

**Returns:** `Task<TimeSpan?>` — the delay before the next attempt, or `null` to give the failure back to the engine's ordinary path.

**Exceptions:**

| Exception | Condition |
|---|---|
| `OperationCanceledException` | Propagated — cancelling the run during the decision ends it. |
| any other | Treated as "no more retries": the policy's bug must not replace the node's own failure. A `[Retry] {node} was not retried: the policy failed to decide ({message})` line is logged. |

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
// The publish node's first delivery fails on purpose; this is what gets it through.
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
```

**Notes:**

- **Only thrown exceptions are retried.** A node that calls `IRuntimeContext.Error` or `IRuntimeContext.Warn` is making a deliberate redirect request — control flow the node asked for, not a failure to try again (`ExecutionRetryTests.ANodeThatAsksForARedirect_IsNotRetried`).
- **A retry is not an attempt.** `IRuntimeContext.Attempt` counts passes over the graph, and it is also the output registry's stamp — so a retry must not move it. Retry numbering is the policy's own and reaches the log as `[Retry n]`.
- The node is re-driven from the **same input** it started with, not from whatever the failed attempt left behind.
- **Cancellation is never retried.** The wait between attempts honours the run's token (`ExecutionRetryTests.CancellingDuringTheRetryWait_EndsTheRun`).
- Returning `null` leaves the failure on the engine's path: a redirect for an `IRedirectable` node, otherwise the flow ends. **A policy that always returns a delay retries forever** — the run has no other cap; use `NodeFailure.RetryNumber` to stop eventually.
- While retrying, no `[Error]` line is written — "an attempt that is going to be retried is not an error yet" — but a `[Retry 1]` line is.

### `NodeFailure`

**Signature:**

```csharp
public readonly record struct NodeFailure(
    IWorkflowNodeViewModel Node,
    Exception Error,
    int RetryNumber,
    TimeSpan Elapsed);
```

| Field | Type | Description |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel` | The node that failed. |
| `Error` | `Exception` | What it threw. |
| `RetryNumber` | `int` | Which retry this decision is about — `1` for the first. |
| `Elapsed` | `TimeSpan` | How long the failed attempt took. |

---

## `IExecutionErrorSink`

Receives every failure a compiled run records. Configured as `RuntimeContext.ErrorSink`.

#### `IExecutionErrorSink.OnErrorAsync`

**Signature:** `Task OnErrorAsync(ExecutionError error, CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `error` | `ExecutionError` | The record: which node, which phase, what exception, on which pass, at which log level. |
| `cancellationToken` | `CancellationToken` | The run's token when the **engine** is reporting; `CancellationToken.None` for a record a **node** sent itself, which carries no token — a report is a record, not work to be interrupted. |

**Returns:** `Task`. Awaiting is the point: it keeps the host's records in the order the run made them and tells the node its report landed.

**Exceptions:** none that reach the run. A sink that throws is swallowed and written to the run's log (`[ErrorSink] the failure was not recorded: {message}`) — reporting a failure must not add one. Pinned by `ExecutionErrorSinkTests.AThrowingErrorSink_DoesNotTurnAWarningIntoAFailure`.

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
// Diagnostics is an ObservableCollection<ExecutionError> — the sink is just its Add.
context.ErrorSink = new DelegateExecutionErrorSink(Diagnostics.Add);
```

**Notes:**

- The run already writes each of these as a log line; a sink is for a host that wants them as **data** — to count them, store them, or show them in a panel. The engine deliberately does not classify: what a failure means is the host's business, so it gets the fields and decides.
- **Two ways in.** The engine reports what it sees itself (a node that threw, a host contract that gave up, the redirect cap, a cancellation), and a node reports through `ErrorAsync` / `WarnAsync`. A node calling the **synchronous** `Error` / `Warn` is writing to the log only, by design — those methods have to stay non-blocking.

### `ExecutionError`

**Signature:**

```csharp
public readonly record struct ExecutionError(
    ExecutionFailurePhase Phase,
    IWorkflowNodeViewModel? Node,
    string Message,
    Exception? Error,
    int Attempt,
    int Order,
    ExecutionReportLevel Level = ExecutionReportLevel.Error);
```

| Field | Type | Description |
|---|---|---|
| `Phase` | `ExecutionFailurePhase` | Where it came from. |
| `Node` | `IWorkflowNodeViewModel?` | The node involved, or `null` for a run-level failure. |
| `Message` | `string` | The message the engine recorded. |
| `Error` | `Exception?` | The exception, when there was one. |
| `Attempt` | `int` | The run's attempt number. |
| `Order` | `int` | The node's compile order, or `-1` when it has none. |
| `Level` | `ExecutionReportLevel` | `Error` unless a node reported a warning. Everything the engine records on its own is an error. |

### `ExecutionFailurePhase`

**Signature:** `public enum ExecutionFailurePhase`

| Member | Value | Meaning |
|---|---|---|
| `Node` | 0 | A node threw, or asked to redirect through `IRuntimeContext.Error`. |
| `Router` | 1 | A router threw while resolving its route key at run time. |
| `Redirect` | 2 | A node threw while resolving where to redirect to (the host's `IRedirectable` implementation). |
| `Run` | 3 | The run itself failed — the redirect cap, or a cancellation that ended it. |

### `ExecutionReportLevel`

**Signature:** `public enum ExecutionReportLevel { Warning = 0, Error = 1 }`

| Member | Value | Meaning |
|---|---|---|
| `Warning` | 0 | The node called `Warn` / `WarnAsync`: worth knowing, nothing went wrong. |
| `Error` | 1 | The node called `Error` / `ErrorAsync`, threw, or the engine itself gave up. |

**Notes:** the engine's own records never carry `Warning`. A cancellable run reports a `Run`-phase record with `Node == null` and the `OperationCanceledException`, and deliberately writes **no** `[Error]` log line — a host stopping its own run is not a failure, and an `[Error]` line would make a later reader of `Logs` think one had happened.

**Recorded phases, by scenario (Test evidence — `CompilerEx/ExecutionErrorSinkTests.cs`, `EngineHostContractFailureTests.cs`):**

| Scenario | Records | Phase |
|---|---|---|
| A node throws, and no `IRedirectable` can place it | 2 — the node's own failure, then the engine's decision that the flow ends | `Node`, then `Node` with `Error == null` |
| A node calls `ErrorAsync` | 2 — the node's record, then the engine's | `Node` |
| A node calls `WarnAsync` | 1 | `Node`, `Level == Warning` |
| A router throws | 1 | `Router` |
| `IRedirectable.ResolveRedirectAsync` throws | 1 | `Redirect` |
| The host cancels the run | 1 | `Run`, `Node == null`, `Error` is the `OperationCanceledException` |
| The redirect cap is exceeded | 1 | `Run` |
