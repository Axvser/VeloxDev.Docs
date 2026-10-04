# Workflow System — Key Member Contracts

Entry-template form for the headline top-level APIs.

## `WorkflowBuilder.TreeAttribute<T>`

**Signature:** `[WorkflowBuilder.Tree<T>(Type? virtualLinkType = default, Type? virtualSlotType = default)]` where `T : IWorkflowTreeViewModelHelper, new()` — declared in `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs` (the generic parameter is the tree's Helper).

**Real usage** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, line 17:

```csharp
[WorkflowBuilder.Tree<AgentHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `virtualLinkType` | `Type?` | Optional override for the virtual-link type (default `LinkDefaultViewModel`) |
| `virtualSlotType` | `Type?` | Optional override for the slot type used inside the virtual link |

**Returns:** nothing (attribute applied to the `partial` class; the generator emits the members).

**Exceptions:** compilation error if `T` is not `IWorkflowTreeViewModelHelper, new()`.

**Notes:** the attribute's generic parameter is the tree's Helper (`AgentHelper : TreeHelper<TreeViewModel>(200)` in the demo); `InitializeWorkflow()` is generator-emitted.

## `IWorkflowTreeViewModelHelper.SendConnection` / `ReceiveConnection`

**Signature:**

```csharp
void SendConnection(IWorkflowSlotViewModel slot);
void ReceiveConnection(IWorkflowSlotViewModel slot);
```

**Parameters:** `slot` — the sender (or receiver) slot, attached to a node in the tree.

**Returns:** `void`.

**Exceptions:** none directly; a detached slot triggers `WorkflowGuard.Fail` in DEBUG builds.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, lines 514-518 — `Connect(tree, sender, receiver)` calls `tree.GetHelper().SendConnection(sender)` then `ReceiveConnection(receiver)`:

```csharp
private static void Connect(IWorkflowTreeViewModel tree, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)
{
    tree.GetHelper().SendConnection(sender);
    tree.GetHelper().ReceiveConnection(receiver);
}
```

**Notes:** two-phase protocol; the link is created and the whole connection is submitted as one undoable `WorkflowActionPair`.

## `CompilerViewModel.CompileAsync`

**Signature:**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)
    where T : IWorkflowViewModel;
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | Must be an `IWorkflowNodeViewModel` — the controller / entry (`Root`) or result terminal (`Terminal`) node |
| `role` | `CompileRole` | `Root` (forward compile of the reachable sub-graph) or `Terminal` (reverse-compile the node's ancestor cone; no explicit start required) |
| `ct` | `CancellationToken` | Optional cancellation |

**Returns:** `IReadOnlyList<CompiledGraph>` — one compiled graph for the request; also stored on `Graphs`.

**Exceptions:** `ArgumentException` if `component` is not an `IWorkflowNodeViewModel`; `ArgumentOutOfRangeException` for an unknown `role`; `InvalidOperationException` when a `Terminal` cone cannot be expressed (producers not funneling into one common join, or a router with several cone-reaching branches).

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, line 52 (`await Compiler.CompileAsync(this, CompileRole.Root);`).

**Notes:** linear segments → `ChainSegment`; `ICompileTimeRouter` nodes → `BranchSegment` (static branches pruned by the compile-time key, dynamic kept all); multi-target routes or plain-node fan-out → `ParallelSegment`; no downstream → terminal branch. Execution is then driven by `RuntimeEngine.RunAsync(graph, context, ct)`.

## `ComponentModelEx.Serialize` / `Deserialize`

**Signature:**

```csharp
string Serialize<T>(this T workflow) where T : INotifyPropertyChanged;
T Deserialize<T>(this string json) where T : INotifyPropertyChanged;
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `workflow` | `T : INotifyPropertyChanged` | Any workflow tree ViewModel |
| `json` | `string` | JSON produced by `Serialize` (or an options variant) |

**Returns:** `Serialize` → JSON string; `Deserialize` → a new `T` instance.

**Exceptions:** `Serialize` → `ArgumentNullException` on null workflow; `Deserialize` → `ArgumentException` on null/empty JSON, `JsonSerializationException` when the result is null. `TryDeserialize` returns `false` instead of throwing.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, line 291 (`var json = this.Serialize();` in `SaveCommand`); `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 71 and 73 (`json.Deserialize<TreeViewModel>()` + `result.Layout.UpdateCommand.Execute(null)`).

**Notes:** settings include `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `WritablePropertiesOnlyResolver`.

## `RuntimeEngine.RunAsync`

**Signature:**

```csharp
Task RunAsync(
    CompiledGraph graph,
    IRuntimeContext context,
    CancellationToken ct,
    ExecutionCheckpoint? resumeFrom = null);
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `graph` | `CompiledGraph` | The compiled graph to drive. A `null` graph returns immediately. |
| `context` | `IRuntimeContext` | The run session. A `null` context returns immediately. |
| `ct` | `CancellationToken` | Cancelling stops the run at the next node boundary; the `OperationCanceledException` is absorbed into `Status = "Stopped"`. |
| `resumeFrom` | `ExecutionCheckpoint?` | Optional checkpoint to carry on from — usually the one `RuntimeContext.CheckpointStore` holds. Omit it (or pass `null`) for a fresh run. |

**Returns:** `Task` — completes when the run ends. Read `Status`, `Outcome`, `Data`, `TargetReached` and `Attempt` afterwards.

**Exceptions:** `InvalidOperationException` when `resumeFrom` was taken over a different graph (refused before the session is touched; `Status` stays `"Idle"`) or when the run redirected more than 50 times.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` — the Run/Resume drive:

```csharp
var context = new RuntimeContext { IsRunning = true, Data = SeedPayload };
ConfigureSessionWith(context);              // host policy: gate, observer, retry, sink, compensation, store, log writer
ExecutionCheckpoint? place = resume ? await CheckpointSource(ct) : null;
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**Notes:** the engine owns downstream dispatch — during a compiled run the node never broadcasts. `Attempt` counts graph passes (`1 + redirect count`); a retry does not move it.

## `RuntimeContext` host-capability properties

**Signature:** `public sealed partial class RuntimeContext : IRuntimeContext`

Nine optional properties, all defaulting to "off" so that with none set a run behaves exactly as it did before they existed. Full descriptions: `RuntimeContext`.

| Property | Type | Effect |
|---|---|---|
| `ExecutionGate` | `IExecutionGate?` | Awaited before each node; `Status` becomes `"Paused"` while it holds. |
| `Observer` | `IExecutionObserver?` | Receives the run's timeline. |
| `RetryPolicy` | `INodeRetryPolicy?` | Decides whether a node that threw gets another go. |
| `ErrorSink` | `IExecutionErrorSink?` | Receives failures as records. |
| `Compensation` | `IExecutionCompensation?` | Told about a failed/cancelled run's successes, most recent first. |
| `CheckpointStore` | `IExecutionCheckpointStore?` | Where the run's place is written after each success. |
| `LogWriter` | `ILogWriter?` | Where the run's lines go, in addition to `Logs`. |
| `MaxRetainedLogs` | `int?` | Caps the in-memory `Logs`. `0` keeps none. |
| `MaxParallelBranches` | `int?` | Caps how many fan-out branches run at once. `null` = uncapped; `1` = serialised. |

**Example (Demo):** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, `ConfigureRun(RuntimeContext context)` — sets all seven capability objects on one session.

**Notes:** these are deliberately **not** members of `IRuntimeContext`: adding one would break every external implementation, and they are host policy rather than session state. The engine reads them by downcasting to `RuntimeContext` through a private helper, which also unwraps a fan-out's `BranchRuntimeContext` so they keep working inside a parallel group. A host that supplies its own `IRuntimeContext` gets the uncapped, unobserved behavior.

## `ExecutionCheckpoint` + resume

**Signature:**

```csharp
public sealed class ExecutionCheckpoint
{
    public int Attempt { get; set; }
    public int? ActiveRedirectTarget { get; set; }
    public object? Data { get; set; }
    public Dictionary<string, object?> Outputs { get; set; }
    public List<string> Shape { get; set; }
    public List<string> Types { get; set; }

    public static ExecutionCheckpoint Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target);
}
```

**Parameters (`Rekey`):** `checkpoint` — the place, as written; `target` — the graph to fit it to (same structure, different node identities, which is what a serialization round trip produces).

**Returns:** a new checkpoint filed under `target`'s identities; the input is untouched.

**Exceptions:** `ArgumentNullException` on a `null` checkpoint; `InvalidOperationException` when the two graphs are not the same structure (different node count, or a different node type at some position).

**Example (verified run):**

```csharp
var store = new InMemoryCheckpointStore();
var context = new RuntimeContext { CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, context, ct, null);      // stopped part-way
var saved = await store.LoadAsync(CancellationToken.None);

var resumed = new RuntimeContext();
await new RuntimeEngine().RunAsync(graph, resumed, CancellationToken.None, saved);
// resumed.Status == "Completed"; nodes the checkpoint recorded as done were not driven again.
```

**Notes:** a checkpoint is filed by `RuntimeId`, so a graph that went through serialization has all-new ids and a resume onto it is **refused** rather than guessed at — that is intended, and `Rekey` is the explicit opt-in that says the two graphs are the same structure. A checkpoint stores an `IGroupData` as a plain `Dictionary<string, object?>` keyed by node key, because a node reference cannot be written down (and would drag the tree in).
