# Workflow System — Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`

V7 compilation pipeline: compile time decomposes the subgraph reachable from a start node into acyclic compiled graphs (multi-graph semantics); the execution engine drives the graph at runtime.

| Type | Signature / members |
|---|---|
| `CompilerViewModel` | `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CancellationToken ct = default)` (`T : IWorkflowViewModel`, start must be an `IWorkflowNodeViewModel`); `ObservableCollection<CompiledGraph> Graphs`. Decomposition: linear segments → `ExecuteEntry`; `ICompileTimeRouter` nodes → `BranchEntry` (static prunes to the current key, dynamic keeps all); a route key pointing to multiple downstreams → `ParallelEntry` (fan-out/join); no downstream → terminal branch (`IsTerminal`); the node all branch exits share is the merge point, continued as the next chain of the parent graph (Order offset, not reset). After compiling, every `ICompileTimeAware` node receives its `CompileContext`; linear chain-continuation validates each output edge via `AccessAsync` (compile phase, `IsCompilePhase = true`) — edges that fail are skipped as if unconnected. |
| `CompiledGraph` | `ObservableCollection<ActionEntry> Entries` — one compiled graph; nestable |
| `ActionEntry` | Abstract base (`Guid Id`, `int Depth`, `bool IsSkipped`); concrete: `ExecuteEntry`, `BranchEntry`, `ParallelEntry` |
| `ExecuteEntry` | `ObservableCollection<IWorkflowNodeViewModel> Nodes` — linear segment |
| `BranchEntry` | `IWorkflowNodeViewModel? Router`, `ObservableCollection<BranchOption> Options`, `bool IsDynamic`, `object? CompileKey` (statically locked key) |
| `BranchOption` | `object? Key`, `string? Label`, `CompiledGraph? Graph`, `bool IsSkipped`, `bool IsTerminal` |
| `ParallelEntry` | `ObservableCollection<CompiledGraph> Branches` — fan-out group; branches run in order (the order IS the "wait for all upstreams" join semantics) |
| `CompilerEngine` | `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct)` — drives all entries of a graph; re-runs the whole graph with a target Order on redirect |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()`, `Task<object?> ResolveRouteKey(object? payload)` |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` — returns the compile-state Order to roll back to |
| `ICompileTimeAware` | `void AttachCompileTimeContext(ICompileContext context)`, `ICompileContext? CompileContext` |
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)` |
| `ICompileContext : IAccessContext` | Inherits `Data`/`IsCompilePhase`/`Sender`/`Receiver`; adds `int Order`, `int ChainIndex`, `int Offset` (`Order = -1` = absolute stop) |
| `IRuntimeContext : ITaskContext` | `Uid`, `Sequence`, `Logs`, `CurrentEntry`, `NodeIndex`, `BranchKey`, `Attempt`, `IsRunning`, `Status`, `CurrentOrder`, `RedirectRequested`, `EndedWithError`, `PendingRedirectTarget`; `new Data { get; set; }` (writable chain result); `Log()`, `Error()`, `Warn()`, `Set()`, `TryGet()` |
| `RuntimeContext` | Default `IRuntimeContext` implementation (`[VeloxProperty]` members + shared-variable dictionary; `IsCompilePhase = false`) |
| `CompileContext` | Default `ICompileContext` implementation (`Order`, `ChainIndex`, `Offset`; `IsCompilePhase = true`, `Data = null`, `Sender`/`Receiver` filled per-edge by the compiler) |
| `RouterCompileMode` | `Static` (key locked at compile time, static pruning) / `Dynamic` (runtime re-resolution) |

Execution semantics (`CompilerEngine`): `ExecuteEntry` drives nodes one by one — on cross-chain rollback it skips nodes with `Order < target`; a node calling `RuntimeContext.Error()/Warn()` or throwing during `ReceiveAsync` requests a redirect — if it implements `IRedirectable`, the engine **re-runs the whole graph** from the returned Order (skipping earlier nodes, possibly cross-chain; if the target is a Router it re-routes only, without recomputing), otherwise the flow ends with status `-1`. `BranchEntry` uses the statically locked `CompileKey` in static mode and re-resolves via `ResolveRouteKey` in dynamic mode; selecting a terminal branch (`IsTerminal`) ends the run. `ParallelEntry` runs all branch graphs in order. Redirects are abandoned after 50 attempts (`MaxRedirects`).

**Example** — `CompileAsync` + `RunAsync` used from a controller node: `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, lines 29-58.

*Sources: `WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompilerEngine.cs`, `CompiledGraph.cs`, `CompileContext.cs`, `RuntimeContext.cs`, `IRedirectable.cs`, `ActionEntry/*.cs`, `Interfaces/*.cs`.*
