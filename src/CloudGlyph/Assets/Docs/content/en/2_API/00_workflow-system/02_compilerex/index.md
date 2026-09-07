# Workflow System — Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`

Compilation pipeline: `CompilerViewModel` decomposes the subgraph reachable from a node into acyclic compiled graphs (`CompiledGraph` of `ChainSegment` / `BranchSegment` / `ParallelSegment`), assigns each `ICompileTimeAware` node a compile identity (`CompileContext`), then `RuntimeEngine.RunAsync` drives the graph at runtime through the node's single execution entry, `IWorkflowNodeViewModelHelper.ReceiveAsync`. All types below live in `VeloxDev.Core.WorkflowSystem.CompilerEx`.

> For how the engine-driven (Compiler) path and the node-driven broadcast path reach the *same* `ReceiveAsync` — entry points, parameters, and timing — see [Execution Mechanism](../05_execution-mechanism).

Evidence: **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, `EnumSelectorNodeViewModel.cs`) + **Test** (`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/*`).

---

## Compile entry point

### `CompilerViewModel`

`sealed partial class`. Kept on a node (a controller) so UI can bind the compile results, e.g. `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, line 18 (`public CompilerViewModel Compiler { get; } = new();`).

| Member | Signature | Notes |
|---|---|---|
| `CompileAsync<T>` | `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)` where `T : IWorkflowViewModel` | The single compile entry point. Clears `Graphs`, then stores the produced graph(s) on it. One compiled graph per role request. |
| `Graphs` | `ObservableCollection<CompiledGraph>` | Latest compile output (`[VeloxProperty]`); UI-bound. |

`CompileAsync` throws:

| Exception | Condition |
|---|---|
| `ArgumentException` | `component` is not an `IWorkflowNodeViewModel` |
| `ArgumentOutOfRangeException` | Unknown `role` |
| `InvalidOperationException` | A `CompileRole.Terminal` ancestor cone whose independent producers do not funnel into one common join ("series-parallel cone" only), or a router with more than one branch reaching the terminal |

**Role** — `enum CompileRole { Root, Terminal }` (delegates to `CompilerViewModel.CompileGraphAsync` / `CompilerViewModel.CompileConeAsync`):

| Member | Meaning |
|---|---|
| `Root` | The node is the starter: decompose the sub-graph reachable from it downstream along `Targets`. |
| `Terminal` | The node is the result terminal: walk its ancestor cone backward along `Sources` (over `AccessAsync`-accepted edges), derive the cone's entry frontier, and compile only the cone needed to compute that node — no explicit start node. Reverse implementation in `CompilerViewModel.Reverse.cs`. |

**Usage (demo)** — `ControllerViewModel.cs`, lines 30-35: a node command compiles itself as `Root`, then the Run command drives the stored graph:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// ControllerViewModel.cs (lines 30-35)
[VeloxCommand]
private async Task Compile(object? parameters, CancellationToken ct)
{
    await Compiler.CompileAsync(this, CompileRole.Root);
    OnPropertyChanged(nameof(HasCompiledGraphs));
}
```

---

## Compiled model and compile-time contracts

### `CompiledGraph`

`sealed partial class`. An ordered collection of compiled segments treated as one graph; nestable — a `BranchSegment` / `ParallelSegment` holds child `CompiledGraph`s. The compiled artifact is a description of possible executions; the actual path is chosen by runtime state.

| Member | Signature | Notes |
|---|---|---|
| `Entries` | `ObservableCollection<CompileSegment>` | The top-level segments in drive order |

### `CompileSegment` (abstract base)

| Member | Type | Notes |
|---|---|---|
| `Id` | `Guid` | Segment UID (UI tree-node identifier) |
| `Depth` | `int` | Nesting depth (UI indent) |

Concrete segments:

| Segment | `: CompileSegment` | Members |
|---|---|---|
| `ChainSegment` | `sealed partial` | `ObservableCollection<IWorkflowNodeViewModel> Nodes` — a linear segment (single-in/single-out run of nodes) |
| `BranchSegment` | `sealed partial` | `IWorkflowNodeViewModel? Router`, `ObservableCollection<BranchOption> Options`, `bool IsDynamic`, `object? CompileKey` — one router node plus its branch options |
| `ParallelSegment` | `sealed partial` | `ObservableCollection<CompiledGraph> Branches` — a fan-out group; branches run sequentially (order carries the "wait for all upstreams" merge semantics) |

### `BranchOption`

| Member | Type | Notes |
|---|---|---|
| `Key` | `object?` | Route key this branch answers to |
| `Label` | `string?` | Display label (key string form, `"?"` when the key is null) |
| `Graph` | `CompiledGraph?` | Downstream sub-graph; `null` when the branch registers a key with no downstream (terminal) |
| `IsTerminal` | `bool` | No downstream node — selecting this branch at runtime ends the whole run (the join tail is not propagated) |

### Compile identity — `ICompileContext` / `CompileContext`

| Contract | Notes |
|---|---|
| `interface ICompileContext : IAccessContext` | Compile-time identity: `int Order` (fixed execution order, `-1` = absolute stop), `int ChainIndex` (index within its linear segment), `int Offset` (sub-graph entry offset, `> 0` for router downstreams), `IReadOnlyList<IWorkflowNodeViewModel>? InputNodes` (join-point input sources; `Count > 1` → runtime injects a `GroupData`, otherwise `null` keeps bare chaining) |
| `class CompileContext : ICompileContext` | Default impl. `IsCompilePhase => true`, `Data => null`; `Sender`/`Receiver` null on the identity instance a node holds, filled only on the per-edge instances the compiler builds for `AccessAsync` validation; `Order`/`ChainIndex`/`Offset` are `[VeloxProperty]` (defaults `-1` / `-1` / `0`) |

### Aware + router contracts

| Type | Signature / members |
|---|---|
| `ICompileTimeAware` | `void AttachCompileTimeContext(ICompileContext context)`; `ICompileContext? CompileContext { get; }` — a node implements it to receive its compile identity when compilation finishes (`Order = -1` = absolute stop state) |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()` — branch table (one key can fan out to several targets); `Task<object?> ResolveRouteKey(object? payload)` — given the current payload (an `IRuntimeContext` at runtime, `null` at compile time), returns the route key |
| `RouterCompileMode` | `enum { Static, Dynamic }` — the router's compile mode. `Static`: `GetRouteTable()` returns only the currently selected branch; order is fixed at compile time. `Dynamic`: returns all branches; the key is re-resolved at runtime |

`CompileKey` on a `BranchSegment` is the value `ResolveRouteKey(null)` returned at compile time: a non-null key means **Static** (`IsDynamic = false`) and runtime uses the locked key; a `null` result means **Dynamic** (`IsDynamic = true`) and runtime re-resolves via `ResolveRouteKey(context)`. Static pruning (only under `CompileRole.Root`, no cone): downstream nodes that are reachable in the full topology but not on any live branch get a "reset signal" — `CompileContext.Order = -1`, absolute stop — and never enter a compiled segment.

**Demo router** — `EnumSelectorNodeViewModel.cs` (`: ICompileTimeRouter, ICompileTimeAware`): its `GetRouteTable()` returns one branch under `RouterCompileMode.Static` or all branches under `Dynamic`; `ResolveRouteKey` returns `null` for a `null` compile-time payload only in `Dynamic` mode, then reads the runtime payload ("selector.value" shared variable or per-member 0/1 flags) or falls back to the currently selected enum value.

---

## Runtime

### `RuntimeEngine`

`sealed class` with no constructor. Drives node execution along a compiled graph; the engine owns downstream dispatch — nodes never broadcast during a compiled run.

| Member | Signature | Notes |
|---|---|---|
| `RunAsync` | `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct)` | Runs one graph to completion (redirect re-runs included). `MaxRedirects = 50`; exceeding it calls `context.Error` and throws `InvalidOperationException`. Final `Status` is `"Completed"` unless it ended early (`"Stopped"`) or was cancelled. |

Segment handling inside a run:

| Segment | Behavior |
|---|---|
| `ChainSegment` | Drives `Nodes` one by one. On a cross-chain redirect, nodes with `Order < target` are skipped (not driven). A node that calls `Error()`/`Warn()` or throws requests a redirect: if it implements `IRedirectable`, `ResolveRedirectAsync` supplies a target Order (only a predecessor, `target < current Order`, is honored) and the engine re-runs the whole graph toward it; otherwise the flow ends with `CurrentOrder = -1`, `EndedWithError = true`. |
| `BranchSegment` | Drives the router itself, picks the key (static `CompileKey` / dynamic `ResolveRouteKey(context)`), records it on `context.BranchKey`, then drives the chosen option's sub-graph. A terminal option (or no match) ends the run. When a redirect target equals the router's own Order, it **re-routes only** without re-driving the router. |
| `ParallelSegment` | Restores `Data = sourceData` (the fan-out source output) before each branch, then runs every branch graph sequentially; a terminal hit in any branch ends the whole run. |

Per-node drive (engine-internal, one node before the next): if the node matches `context.Target` → `TargetReached = true`; injects the session into `IRuntimeAware` nodes; sets `CurrentOrder` from the compile identity; logs the node type; when the identity has plural `InputNodes` it replaces `Data` with `GroupData(context.CollectGroupedInputs(inputs))`; finally calls `Helper.ReceiveAsync(context, ct)`, registers the output (`RegisterOutput(node, result)`) and writes `context.Data = result` for downstream chaining.

### `IRuntimeContext : ITaskContext` — runtime session contract

Inherits `Data` (re-declared `new object? Data { get; set; }` — writable chain result), `Sender`, `Receiver`, `IsCompilePhase`.

| Member | Signature / notes |
|---|---|
| `Uid` | `Guid` — run-session identity |
| `Sequence` | `int` — next execution sequence number (auto-incremented) |
| `Logs` | `ObservableCollection<string>` — sequence-prefixed log lines |
| `CurrentEntry` | `CompileSegment?` — segment currently executing |
| `NodeIndex` | `int` — current node index within its chain |
| `BranchKey` | `object?` — current branch key |
| `Attempt` | `int` — graph re-run count (1 + redirect count) |
| `IsRunning` / `Status` | `bool` / `string` (`Idle`/`Running`/`Completed`/`Stopped`) |
| `CurrentOrder` | `int` — execution status code = the current node's compile-time Order |
| `Target` / `TargetReached` | `IWorkflowNodeViewModel?` / `bool` — optional result node a run tracks; the engine sets `TargetReached` once the matching node is actually driven (false = branch not taken / condition not met) |
| `RedirectRequested` | `bool` — set when the node called `Error`/`Warn` during this drive; cleared before each drive |
| `EndedWithError` | `bool` — flow ended early with status `-1` (non-`IRedirectable` error) |
| `PendingRedirectTarget` | `int?` — engine-requested redirect Order; `RunAsync` re-runs the whole graph with it |
| `ActiveRedirectTarget` | `int?` — current re-run target Order (null on first pass); the output collector uses it to tell the contract-preserved prefix from stale branches |
| `Log` / `Error` / `Warn` | `void (string)` — push a log line; `Error`/`Warn` add `[Error]`/`[Warning]` markers and request a redirect |
| `Set` / `TryGet` | `void Set(string key, object?)` / `bool TryGet(string key, out object?)` — shared-variable (blackboard) access |
| `RegisterOutput` | `void RegisterOutput(IWorkflowNodeViewModel node, object? value)` — engine records a node's output for this pass |
| `ResetOutputs` | `void ResetOutputs()` — clears the output registry once per `RunAsync` |
| `CollectGroupedInputs` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?> CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel> inputNodes)` — read-only per-source output dict for join aggregation; unregistered sources are absent |

### `RuntimeContext`

`sealed partial class : IRuntimeContext`. The default runtime session object. `IsCompilePhase => false` always. Public `Target`/`TargetReached` plus the interface members (`Uid`, `Sequence`, `Logs`, … generated as `[VeloxProperty]`); convenience `int Next()` auto-increments `Sequence`. Construction is `new RuntimeContext { Data = seed, Target = target }`.

### Group data — `IGroupData` / `GroupData`

| Type | Notes |
|---|---|
| `interface IGroupData : IReadOnlyDictionary<IWorkflowNodeViewModel, object?>` | The join contract: key = the source node (reference identity), value = that node's output this run. Consumed via `context.Data is IGroupData g`, then `TryGetValue` / indexer / `Keys`. |
| `readonly struct GroupData : IGroupData` | Struct wrapper over the read-only dictionary the engine boxes into `IRuntimeContext.Data` before driving a join point. Indexer throws `KeyNotFoundException` for an unregistered source. |

**Demo join consumer** — `PythonHelper.BuildInputPayload` (`Helper/PythonHelper.cs`): when `ctx.Data is IGroupData`, it rebuilds the payload as `{ inputPortName: sourceOutput }` for the script.

### Runtime aware / redirect hooks

| Type | Signature / notes |
|---|---|
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)` — the engine hands the current session to the node before driving it (record sequence, write logs, read/write shared variables) |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` — after the node requests a redirect, decide an earlier compile state (`CompileContext.Order`) to fall back to; `null` = continue. In-chain redirect only; the compiled graph is acyclic. |

**Usage (demo)** — `ControllerViewModel.cs`, lines 39-59: the Run command takes the first compiled graph and drives it with a fresh session (the `RuntimeContext` node property and `_runCts` field are declared elsewhere in the same class):

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// ControllerViewModel.cs (lines 39-59)
private async Task Run(object? parameters, CancellationToken ct)
{
    var graph = Compiler.Graphs.FirstOrDefault();
    if (graph is null) return;

    var context = new RuntimeContext { IsRunning = true };
    RuntimeContext = context;
    OnPropertyChanged(nameof(RuntimeContext));

    _runCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
    try
    {
        await new RuntimeEngine().RunAsync(graph, context, _runCts.Token);
    }
    finally
    {
        _runCts.Dispose();
        _runCts = null;
    }
}
```

---

## Execution semantics summary

Linear segments chain node results through `IRuntimeContext.Data`; fan-out and joins (`IGroupData`) are aggregate semantics on the shared session; errors/warnings are redirect requests honored only by `IRedirectable` nodes; reverse (Terminal) runs track reachability through `RuntimeContext.Target` / `TargetReached` and never fabricate a result when the terminal's branch is not selected.

**Sources:** `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/` — `CompilerViewModel.cs`, `CompilerViewModel.Reverse.cs`, `CompileRole.cs`, `Compile/Contracts/*.cs` (`ICompileContext`, `ICompileTimeAware`, `ICompileTimeRouter`, `RouterCompileMode`), `Compile/Model/*.cs` (`CompiledGraph`, `CompileSegment`, `ChainSegment`, `BranchSegment`, `ParallelSegment`, `BranchOption`, `CompileContext`), `Runtime/Contracts/*.cs` (`IRuntimeContext`, `IRuntimeAware`, `IRedirectable`), `Runtime/RuntimeEngine.cs`, `Runtime/Model/*.cs` (`RuntimeContext`, `GroupData`).
