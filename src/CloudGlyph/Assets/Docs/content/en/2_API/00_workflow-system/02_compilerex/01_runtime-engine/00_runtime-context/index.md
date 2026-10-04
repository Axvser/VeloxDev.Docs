# Workflow System — The Session: `RuntimeContext` and `GroupData`

The concrete session object a host hands to `RuntimeEngine.RunAsync`, and the join payload the engine boxes into `Data` at a multi-input node.

Sources: `Runtime/Model/RuntimeContext.cs`, `Runtime/Model/GroupData.cs`.

---

## `RuntimeContext`

`public sealed partial class : IRuntimeContext`. `IsCompilePhase => false`, always: only the compile phase is true. Construction is `new RuntimeContext { Data = seed, Target = target, ExecutionGate = gate, ... }`.

It carries three groups of members: the shared session context (`Uid` / `Sequence` / `Logs` / blackboard), the execution position and decision state the engine maintains (bound to UI progress), and the host-capability seams described at the bottom of this page.

### Shared context and execution position

| Name | Type | Description |
|---|---|---|
| `Uid` | `Guid` | Session identity; defaults to `Guid.NewGuid()`. |
| `Sequence` | `int` | Next sequence number; defaults to `0`. |
| `Logs` | `ObservableCollection<string>` | The retained log lines. |
| `CurrentEntry` | `CompileSegment?` | Segment currently executing. |
| `NodeIndex` | `int` | Index of the current node within its chain; defaults to `-1`. |
| `BranchKey` | `object?` | Current branch key. |
| `Attempt` | `int` | Graph pass count. |
| `IsRunning` | `bool` | Whether a run is in progress. |
| `Status` | `string` | `"Idle"` by default; the engine writes `Running` / `Paused` / `Completed` / `Stopped`. |
| `CurrentOrder` | `int` | The compile-time `Order` of the node currently executing; defaults to `-1`. |
| `Data` | `object?` | The chained payload (the interface's writable `new Data`). |
| `Sender` / `Receiver` | `IWorkflowSlotViewModel?` | Slot endpoints. Always `null` under a compiled run — the engine drives the graph, not edges. |
| `IsCompilePhase` | `bool` | Always `false`. |

### Decision state

| Name | Type | Description |
|---|---|---|
| `Target` | `IWorkflowNodeViewModel?` | Optional node the run should reach (result/terminal runs). |
| `TargetReached` | `bool` | Set when the matching node is actually driven. |
| `RedirectRequested` | `bool` | Whether this drive reported anything at all. The getter reads `ReportedLevel is not null`; assigning `true` counts as the gravest reading, an error. |
| `EndedWithError` | `bool` | The flow ended early with status code `-1`. |
| `PendingRedirectTarget` | `int?` | Engine-requested redirect target Order. |
| `ActiveRedirectTarget` | `int?` | The pass's redirect target Order; `null` on the first pass. |
| `Outcome` | `RunOutcome` | How the last run ended; `RunOutcome.Unknown` until then. |

### Methods

| Member | Signature | Notes |
|---|---|---|
| `Next` | `int Next()` | Returns the next sequence number via `Interlocked.Increment`. |
| `Log` | `void Log(string entry)` | Appends `"{NN}. {entry}"`. |
| `Error` | `void Error(string message)` | Appends `"{NN}. [Error] {message}"` and sets the reported level to `Error`. |
| `Warn` | `void Warn(string message)` | Appends `"{NN}. [Warning] {message}"` and sets the reported level to `Warning`. |
| `ErrorAsync` | `Task ErrorAsync(string message)` | `Error(message)` then awaits the configured `ErrorSink` with `ExecutionReportLevel.Error` and `CancellationToken.None`. |
| `WarnAsync` | `Task WarnAsync(string message)` | The same at `ExecutionReportLevel.Warning`. |
| `Set` / `TryGet` | `void Set(string key, object?)` / `bool TryGet(string key, out object?)` | The shared-variable blackboard, keyed case-insensitively (`StringComparer.OrdinalIgnoreCase`). An empty/whitespace key is ignored on write. |
| `RegisterOutput` | `void RegisterOutput(IWorkflowNodeViewModel node, object? value)` | Stores `(Attempt, value)` keyed by node reference identity. Also the run's "this node succeeded" signal: the node moves to the end of the compensation list rather than being recorded twice. |
| `ResetOutputs` | `void ResetOutputs()` | Clears the output registry and the completed list. Called once at the start of every `RunAsync`. |
| `CollectGroupedInputs` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?> CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel> inputNodes)` | Builds the join dictionary, pre-sized to the source count. Keeps only outputs registered **this pass**, or the contract-preserved prefix before `ActiveRedirectTarget` (`source Order < target`). |
| `SnapshotLogs` | `string[] SnapshotLogs()` | A point-in-time copy of `Logs`, safe to enumerate while the run is appending. |

#### `RuntimeContext.SnapshotLogs`

**Signature:** `public string[] SnapshotLogs()`

**Returns:** `string[]` — a copy of `Logs` taken under the session's log lock.

**Exceptions:** none.

**Example (Test):**

```csharp
// CompilerEx/RuntimeContextLogConcurrencyTests.cs
var context = new RuntimeContext { MaxRetainedLogs = 16 };
// a writer task logs in a loop while this reader runs
_ = context.SnapshotLogs().Length;          // must never throw
Assert.IsTrue(context.SnapshotLogs().Length <= 16);
```

**Notes:** `ObservableCollection<T>` is not thread-safe. Without the lock a reader (`Enumerable.ToList`) reads `Count` and then `CopyTo`, and any `Add`/`RemoveAt` in between makes the destination array too short — throwing `ArgumentOutOfRangeException: Source array was not long enough ... (Parameter 'sourceArray')`. Use `SnapshotLogs()` for anything outside the run's own thread; enumerating `Logs` live is only safe on the driving thread.

### Events

#### `RuntimeContext.LogWriteFailed`

**Signature:** `public event EventHandler<LogWriteFailedEventArgs>? LogWriteFailed;`

Raised when the configured `LogWriter` throws. The line is still kept in `Logs` and the run carries on — diagnostics never change what the run does. `LogWriteFailedEventArgs` exposes `string Line` (the line that could not be written) and `Exception Error` (what the writer threw).

### Host-capability properties

These are the 2026-09-27 seams. All default to "off", and with all of them off a run behaves exactly as it did before they existed — the same log lines and the same number of drives. Each is documented in full on `Execution contracts` and `Checkpointing`.

| Name | Type | Default | Effect when set |
|---|---|---|---|
| `ExecutionGate` | `IExecutionGate?` | `null` | Awaited before each node; lets a host hold a long run. While it holds, `Status` is `"Paused"`; on release, back to `"Running"`. |
| `Observer` | `IExecutionObserver?` | `null` | Receives every observation of the run's timeline. |
| `RetryPolicy` | `INodeRetryPolicy?` | `null` | Decides whether a node that **threw** gets another go. |
| `ErrorSink` | `IExecutionErrorSink?` | `null` | Receives every failure as a record rather than only as a log line. |
| `Compensation` | `IExecutionCompensation?` | `null` | Told about the nodes a failed or cancelled run already drove, most recent first. |
| `CheckpointStore` | `IExecutionCheckpointStore?` | `null` | Where the run's place is written after each node succeeds. |
| `LogWriter` | `ILogWriter?` | `null` | Diverts the run's lines somewhere other than the in-memory `Logs`. |
| `MaxRetainedLogs` | `int?` | `null` | Caps how many lines `Logs` keeps (oldest dropped first). `0` keeps none while `LogWriter` still receives every line. |
| `MaxParallelBranches` | `int?` | `null` | Caps how many branches of one fan-out may be in flight at once. `null` = no cap; `1` serialises the group. |

> **Why these are not on `IRuntimeContext`.** Adding a member to that interface would break every external implementation of the contract, and all of them are host **policy** rather than session state: `MaxParallelBranches` and `MaxRetainedLogs` say what the host would rather do, and the six capability objects are seams it opts into. The engine reads them by downcasting to this concrete class through a private `Session()` helper, which also unwraps a fan-out's `BranchRuntimeContext` — so a gate or observer keeps working *inside* a parallel group rather than silently dying in exactly the place a wide graph spends its time. A host that brings its own `IRuntimeContext` implementation simply gets the uncapped, unobserved, pre-2026-09-27 behavior.

---

## `IGroupData` / `GroupData`

| Type | Notes |
|---|---|
| `public interface IGroupData : IReadOnlyDictionary<IWorkflowNodeViewModel, object?>` | The join contract. Key = the source node (reference identity), value = that node's output this run. A consumer detects it with `context.Data is IGroupData g`. |
| `public readonly struct GroupData : IGroupData` | The struct the engine constructs and boxes into `IRuntimeContext.Data` before driving a join point. The indexer throws `KeyNotFoundException` for an unregistered source; use `TryGetValue` to read safely. |

**Example (Test):**

```csharp
// CompilerEx/RuntimeEngineRunTests.cs — JoinWithTwoUpstreams_ReceivesGroupDataKeyedBySourceNode
var group = (IGroupData)joinPayload;
Assert.AreEqual(2, group.Count);
Assert.IsTrue(group.TryGetValue(a, out var va) && Equals(va, "AV"));
Assert.IsTrue(group.TryGetValue(b, out var vb) && Equals(vb, "BV"));
```

**Notes:** the engine injects a `GroupData` only when the node's compile identity registered more than one `InputNodes`; a single-input node keeps the bare chained payload. **Demo:** `PythonHelper.BuildInputPayload` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/PythonHelper.cs`) rebuilds the script payload as `{ inputPortName: sourceOutput }` when `ctx.Data is IGroupData`.
