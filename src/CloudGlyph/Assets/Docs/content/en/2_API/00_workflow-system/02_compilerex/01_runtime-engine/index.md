# Workflow System — Runtime Engine

The run half of `VeloxDev.Core.WorkflowSystem.CompilerEx`. `RuntimeEngine` walks a compiled graph and drives each node through `IWorkflowNodeViewModelHelper.ReceiveAsync`; the session contract `IRuntimeContext` carries identity, logs, position, the blackboard and the output registry through the whole run.

Sources: `Runtime/RuntimeEngine.cs`, `Runtime/Contracts/IRuntimeContext.cs`, `Runtime/Contracts/IRuntimeAware.cs`, `Runtime/Contracts/IRedirectable.cs`, `Runtime/Contracts/RunOutcome.cs`.

---

## `RuntimeEngine`

`public sealed class`, no constructor state. The engine owns downstream dispatch — nodes never broadcast during a compiled run. It is instantiated per run (`new RuntimeEngine()`).

#### `RuntimeEngine.RunAsync`

**Signature:**

```csharp
Task RunAsync(
    CompiledGraph graph,
    IRuntimeContext context,
    CancellationToken ct,
    ExecutionCheckpoint? resumeFrom = null);
```

| Parameter | Type | Description |
|---|---|---|
| `graph` | `CompiledGraph` | The compiled graph to drive. A `null` graph returns immediately. |
| `context` | `IRuntimeContext` | The session. A `null` context returns immediately. |
| `ct` | `CancellationToken` | The host's token: cancelling stops the run at the next node boundary. |
| `resumeFrom` | `ExecutionCheckpoint?` | Optional checkpoint to carry on from, normally the one `RuntimeContext.CheckpointStore` holds. Nodes it records as done are not driven again. |

**Returns:** `Task` — completes when the run ends. Inspect `Status`, `Outcome`, `Data`, `TargetReached`, `Attempt` and `Logs` afterwards.

**Exceptions:**

| Exception | Condition |
|---|---|
| `InvalidOperationException` | `resumeFrom` was taken over a different graph (`Shape` mismatch). Refused **before the session is touched** — `Status` stays `"Idle"` and nothing is driven. |
| `InvalidOperationException` | The run redirected more than 50 times (`MaxRedirects`). `Status` is set to `"Stopped"`, `EndedWithError = true`, `CurrentOrder = -1` **before** the throw. |
| `OperationCanceledException` | The host's `ct` fired. Swallowed into `Status = "Stopped"`; not propagated to the caller. |

**Example (Demo):**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs (the Run/Resume drive)
var graph = Compiler.Graphs.FirstOrDefault();
if (graph is null) return;

var context = new RuntimeContext { IsRunning = true, Data = SeedPayload };
ConfigureSessionWith(context);                       // the host policy hook
ExecutionCheckpoint? place = resume ? await CheckpointSource(ct) : null;
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**Notes:** a redirect is implemented uniformly as "re-run the whole graph with a target Order". Nodes with `Order < target` are the contract-preserved prefix and are skipped; `Attempt` counts the passes.

### Segment handling inside a run

| Segment | Behavior |
|---|---|
| `ChainSegment` | Drives `Nodes` one by one. A node whose `Order <` the redirect target, or one the checkpoint records as done, is skipped. On each drive: `RedirectRequested` is cleared, the node is driven, and what it reported decides where the run goes. |
| `BranchSegment` | Drives the router itself, then picks the key — `branch.IsDynamic ? ResolveRouteKey(context) : branch.CompileKey` — records it on `BranchKey`, and drives the chosen option's sub-graph. A terminal option (or no match) returns "the run ends here". When the redirect target is at or after the router (`target < routerOrder` is false), the router is **not** re-driven (re-route only) but the branch *is* still entered, so a redirect aimed inside the branch drives the nodes at and after the target again. |
| `ParallelSegment` | Fan-out group. Restores `Data = sourceData` so every branch starts from the fan-out source's output, then runs the branches **concurrently** as interleaved async operations on the caller's `SynchronizationContext`. `MaxParallelBranches` caps how many may be in flight at once. A terminal hit inside any branch ends the whole run; when several branches request a redirect the first in branch order wins and the others are logged and ignored. |

### Per-node drive

For each node the engine: awaits `ExecutionGate.WaitAsync` (writing `Status = "Paused"` only while the gate is actually closed), sets `TargetReached = true` when the node is `Target`, injects the session into `IRuntimeAware` nodes, sets `CurrentOrder` from the compile identity, logs the node's type name, and — when the identity carries more than one `InputNodes` — replaces `Data` with `GroupData(CollectGroupedInputs(inputs))`. It then calls `Helper.ReceiveAsync(context, ct)`, registers the output and writes `context.Data = result`.

The drive loop is where a retry policy is consulted (on a thrown exception only), where a thrown exception becomes an `ExecutionFailurePhase.Node` error record, and where a successful drive saves a checkpoint. Injected `AttachRuntimeContext` calls happen **inside** the failure discipline, so a host implementation that throws ends the run instead of silently skipping the node.

---

## `IRuntimeContext : ITaskContext`

The run-session contract. It inherits `Data`, `Sender`, `Receiver` and `IsCompilePhase` from `IAccessContext`, and re-declares `Data` with a setter.

| Member | Type | Description |
|---|---|---|
| `Uid` | `Guid` | Run-session identity. |
| `Sequence` | `int` | Next execution sequence number (auto-incremented). |
| `Logs` | `ObservableCollection<string>` | Log lines, each prefixed `NN. ` (sequence number, dot, space). |
| `CurrentEntry` | `CompileSegment?` | The segment currently executing. |
| `NodeIndex` | `int` | Index of the current node within its chain. |
| `BranchKey` | `object?` | The current branch key. |
| `Attempt` | `int` | Graph pass count = `1 + redirect count`. Also the output registry's pass stamp. A retry does **not** move it. |
| `IsRunning` | `bool` | Whether a run is in progress. |
| `Status` | `string` | `Idle` / `Running` / `Paused` / `Completed` / `Stopped`. |
| `CurrentOrder` | `int` | The current node's compile-time `Order`; `-1` = absolute stop. |
| `Target` | `IWorkflowNodeViewModel?` | Optional node the run should track (result/terminal runs set it). |
| `TargetReached` | `bool` | Whether `Target` was actually driven. `false` = its branch was not taken. |
| `Data` | `object?` (get **and set**) | The chained result. The engine writes each node's return value back for the next node. |
| `RedirectRequested` | `bool` | Whether this drive reported anything at all. Cleared before each drive. |
| `EndedWithError` | `bool` | The flow ended early — the run is `"Stopped"` with status code `-1`. |
| `PendingRedirectTarget` | `int?` | The engine-requested redirect target `Order`; `RunAsync` re-runs the whole graph with it. |
| `ActiveRedirectTarget` | `int?` | The target Order the current pass is working with; `null` on the first pass. The output collector uses it to tell the contract-preserved prefix from stale branches. |
| `Log(string)` | `void` | Push a plain log line. |
| `Error(string)` | `void` | Push an `[Error]` line **and** mark the run for a redirect. Synchronous and void on purpose — it runs inside a node's frame and must never block or throw. |
| `Warn(string)` | `void` | Push a `[Warning]` line. A note, not a stop: the run carries on with whatever the node returned. |
| `ErrorAsync(string)` | `Task` | `Error` plus the host's record: awaits `IExecutionErrorSink.OnErrorAsync` at `ExecutionReportLevel.Error`. |
| `WarnAsync(string)` | `Task` | `Warn` plus the host's record at `ExecutionReportLevel.Warning`. |
| `Set(string, object?)` | `void` | Write a shared variable (ignored when the key is empty/whitespace). |
| `TryGet(string, out object?)` | `bool` | Read a shared variable. |
| `RegisterOutput(IWorkflowNodeViewModel, object?)` | `void` | Register a node's output for this pass, stamped with `Attempt`. |
| `ResetOutputs()` | `void` | Clear the output registry (once per `RunAsync`; redirect re-runs do **not** clear it). |
| `CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel>)` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?>` | Read-only per-source output dictionary for a join point. Unregistered sources are absent (`TryGetValue` returns `false`). |

> The members added on 2026-09-27 that are **not** on this interface — `MaxParallelBranches`, `MaxRetainedLogs`, `LogWriter`, `ExecutionGate`, `Observer`, `RetryPolicy`, `ErrorSink`, `Compensation`, `CheckpointStore`, `Outcome` — are documented under `RuntimeContext`. Keeping them off the contract is a deliberate decision, explained there.

---

## Node-side runtime contracts

| Type | Signature / notes |
|---|---|
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)`. The engine hands the node the current session before driving it, so the node can record sequence numbers, write logs and read/write shared variables. Injected inside the drive's failure discipline (see above). |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)`. Called when a drive reports an error or throws. A returned Order that is a **predecessor** (`target < current Order`) makes the engine re-run the whole graph toward it, possibly cross-chain; `null` (or an invalid target) leaves the failure on the engine's ordinary path. Only thrown exceptions reach a retry policy; an `Error()`/`Warn()` call is deliberate control flow the node asked for. |

---

## `RunOutcome`

**Signature:** `public enum RunOutcome { Unknown = 0, Completed, Cancelled, Failed }`

The precise reading of `Status` + `EndedWithError`, because `Status` has to share the one word `"Stopped"` between a failure and a cancellation.

| Member | Value | Mapping |
|---|---|---|
| `Unknown` | 0 | The run has not ended — it never started, or it is still going. |
| `Completed` | 1 | `Status == "Completed"` — every entry was walked. A branch that legitimately ends the run early (a terminal route key) is a completion, not a failure. |
| `Cancelled` | 2 | `Status == "Stopped"` and `EndedWithError == false` — the host's token ended it. |
| `Failed` | 3 | `Status == "Stopped"` and `EndedWithError == true` — a failure ended the flow early. |

**Notes:** there is deliberately **no** `Stopped` member — every path that produces that status string maps to one of the two members below it, so such a member would be unreachable. The outcome is written to `RuntimeContext.Outcome` in the engine's `finally` block; a session of any other implementation has nowhere to put it.

## Sub-pages

| Page | Contents |
|---|---|
| [The Session: RuntimeContext and GroupData](00_runtime-context/index.md) | The concrete session object `RuntimeContext` — every member, including the host-capability properties — and the join payload `IGroupData` / `GroupData` |
