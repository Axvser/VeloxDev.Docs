# Workflow System — Compensation, Checkpoints and Log Writers

The three seams that outlive a run in some way: `IExecutionCompensation` (what a run that ended badly already did), `IExecutionCheckpointStore` (where the run's place is kept) and `ILogWriter` (where its lines go).

Sources: `Runtime/Contracts/IExecutionCompensation.cs`, `Runtime/Contracts/IExecutionCheckpointStore.cs`, `Runtime/Contracts/ILogWriter.cs`.

---

## `IExecutionCompensation`

Told about the nodes a failed or cancelled run already drove, so the host can undo what it cares about. Configured as `RuntimeContext.Compensation`.

#### `IExecutionCompensation.CompensateAsync`

**Signature:** `Task CompensateAsync(NodeCompensation compensation, CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `compensation` | `NodeCompensation` | The node and what it produced, plus its compile order. |
| `cancellationToken` | `CancellationToken` | A token for the cleanup. It is **not** the run's — that one is already cancelled when this is called after a cancellation. Always `CancellationToken.None` from the engine. |

**Returns:** `Task`. Called **most recent first**, once per node that succeeded this run, and only when the run ends `RunOutcome.Failed` or `RunOutcome.Cancelled` — a completed run compensates nothing.

**Exceptions:** none that stop the rest. A compensation that throws is logged (`[Compensation] {node} was not compensated: {message}`) and the remaining nodes still run — the original failure stays the headline.

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.Compensation = new DelegateExecutionCompensation(
    c => Controller.RuntimeContext?.Log($"[Compensation] undo {NameOf(c.Node)} (attempt {c.Order})"));
```

**Notes:**

- **The engine does not roll anything back, and cannot.** A node's effects are its own — a property it wrote, a process it started, a file it left behind — and only the host knows which of those are reversible. So the engine hands over the successes and stops there.
- **The tree's undo stack is not a substitute.** It records model-structure changes only (a node's own property writes and a script's file effects were never submitted), it is one flat stack with no run boundary — so a failure could not unwind this run's entries without eating the user's — and it does not guarantee the chain completes.
- A node that was driven twice (a redirect re-run) appears **once**, at the position of its most recent success: "the effect still standing at the end of a run is the one that node's last success left behind". Pinned by `ExecutionCompensationTests.AfterARedirect_ASkippedPrefixNode_IsStillHandedBack_AndAReDrivenNodeOnlyOnce`.
- A node the redirect skipped as the contract-preserved prefix is still handed back — it was driven this run, and it is still in scope for cleanup.

### `NodeCompensation`

**Signature:**

```csharp
public readonly record struct NodeCompensation(
    IWorkflowNodeViewModel Node,
    object? Output,
    int Order);
```

| Field | Type | Description |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel` | The node that ran. |
| `Output` | `object?` | What it returned, as it was registered for downstream nodes. |
| `Order` | `int` | The node's compile order, or `-1` when it has none. |

**Verified order (Test — `ExecutionCompensationTests`):** a `s → a → b` chain cancelled inside `a` hands back `["a", "s"]` with outputs `["A", "S"]`.

---

## `IExecutionCheckpointStore`

Where a run's place is kept, so a later run can pick it up. Configured as `RuntimeContext.CheckpointStore`; with none configured the engine never writes one.

#### `IExecutionCheckpointStore.SaveAsync`

**Signature:** `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `checkpoint` | `ExecutionCheckpoint` | The state to keep. Immutable as far as the engine is concerned — it is a snapshot. |
| `cancellationToken` | `CancellationToken` | The run's token. |

**Returns:** `Task`.

**Exceptions:** a store that throws is **reported and ignored** — one `[Checkpoint] the run's place was not saved: {message}` log line, and the run carries on. "A place you cannot write down is not a reason to stop working." Pinned by `ExecutionCheckpointTests.AStoreThatThrows_DoesNotStopTheRun`.

#### `IExecutionCheckpointStore.LoadAsync`

**Signature:** `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken cancellationToken)`

| Parameter | Type | Description |
|---|---|---|
| `cancellationToken` | `CancellationToken` | The caller's token. |

**Returns:** `Task<ExecutionCheckpoint?>` — the checkpoint, or `null` when nothing was ever saved.

**Notes:**

- **One store, one run.** The engine writes the run's *current* state — not a history — so a store holds a single latest `ExecutionCheckpoint`. A host that keeps several runs' places keeps several stores, or keys its own implementation by `IRuntimeContext.Uid`.
- **Written after each node succeeds, from inside the drive.** A fan-out's branches interleave, so two saves can be in flight at once even though nothing here runs on a second thread; an implementation that writes a file must serialise its own writes. `FileCheckpointStore` does exactly that with a `SemaphoreSlim`.
- **`LoadAsync` is the host's call, not the engine's.** `RuntimeEngine.RunAsync` takes the checkpoint it should resume from as its `resumeFrom` argument; the host decides when there is one worth resuming. The demo's controller holds a `CheckpointSource` delegate for exactly this.
- Shipped implementations: `InMemoryCheckpointStore` (Core — see `Checkpointing`) and `FileCheckpointStore` (`VeloxDev.Core.Extension` — see `mvvm-serialization`).

---

## `ILogWriter`

Where a compiled run's log lines go, in addition to `IRuntimeContext.Logs`.

#### `ILogWriter.Write`

**Signature:** `void Write(string line)`

| Parameter | Type | Description |
|---|---|---|
| `line` | `string` | One already-formatted log line, prefix included, exactly as it appears in `IRuntimeContext.Logs`. |

**Returns:** nothing.

**Exceptions:** a writer that throws does **not** reach the run. `RuntimeContext.AppendLog` runs inside node frames, so an escaping exception would surface as a *node* failure and the engine would read it as a redirect request. Instead the failure is reported on `RuntimeContext.LogWriteFailed` and the line is dropped.

**Example (Demo / Test):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
```

**Notes:**

- **Lines arrive in the order they happened**, and a fan-out's branches interleave, so a writer that cares about grouping must do that itself. `IRuntimeContext.Logs` receives the same lines **in the same order**, which makes the two views comparable line for line (`CompilerLogWriterTests.AWriter_ReceivesExactlyWhatLogsReceived_InTheSameOrder`).
- **Writes happen on the thread driving the run** — normally the host's `SynchronizationContext`. A writer that touches the file system synchronously therefore puts that IO on that thread; queue the line and drain it on a background thread if that matters.
- **A writer is not a filter and cannot change semantics**: `Error` and `Warn` still mark the run for a redirect, whatever the writer does with the text (`CompilerLogWriterTests.AWriter_DoesNotChangeWarnSemantics`).
- Pair it with `RuntimeContext.MaxRetainedLogs`: the writer is the full-fidelity record, the in-memory collection is the bounded view a host can leave in memory.

### `LogWriteFailedEventArgs`

**Signature:** `public sealed class LogWriteFailedEventArgs(string line, Exception error) : EventArgs`

| Member | Type | Description |
|---|---|---|
| `Line` | `string` | The line that could not be written. It is in `IRuntimeContext.Logs` regardless. |
| `Error` | `Exception` | What the writer threw. |

Raised on `RuntimeContext.LogWriteFailed` so a broken sink is visible instead of merely quiet — the line is still dropped, and the run still continues.
