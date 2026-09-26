# Workflow Agent — Sub-Agents: Tree View-Models

The roster a scope keeps is **flat and per scope** — it holds only its own direct children, which is what keeps one agent from seeing another's. `SubAgentTreeNodeViewModel` and `SubAgentTreeViewModel` project several such rosters into one bindable tree, hung off one another by the child scope each row stands for. Both live in `VeloxDev.AI.SubAgents` (`Agent/SubAgents/SubAgentTreeViewModel.cs`).

## Class: `SubAgentTreeNodeViewModel`

`public sealed partial class SubAgentTreeNodeViewModel` — one node: a row, and the nodes of the sub-agents that row spawned. MVVM source-generated (`[VeloxProperty]`).

| Member | Signature | Notes |
|---|---|---|
| Constructor | `SubAgentTreeNodeViewModel(SubAgentStatusViewModel row, SubAgentTreeNodeViewModel? parent)` | The node for one dispatched sub-agent. The row's own properties **are** the node's — nothing is copied. Throws `ArgumentNullException` when `row` is null. |
| `Row` | `SubAgentStatusViewModel? { get; }` | `null` for the scope root. |
| `Parent` | `SubAgentTreeNodeViewModel? { get; internal set; }` | The node that spawned this one, or `null` at the top of the tree. |
| `Children` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | The sub-agents this one dispatched, in spawn order. |
| `Id` | `string` | The handle, forwarded so a template can bind it without reaching through `Row`; the scope root's id is the fixed `__scope__`. |
| `Depth` | `int` | 0 for the scope, 1 for a direct child of it. |
| `IsScopeRoot` | `bool` | Whether this node stands for the scope rather than for a dispatched sub-agent. |
| `Title` | `string` | `Row?.Name ?? ScopeTitle`. |
| `HasChildren` | `bool` | Whether there is anything to expand into. |
| `TokensUsed` | `long?` | This node's **own** run's spend, or `ScopeTokens` for the scope root. Not its subtree's — see `SubtreeTokens`. |
| `SubtreeTokens` / `SubtreeCallCount` | `long` / `int` | The subtree totals, recomputed bottom-up. |
| `TokensText` | `string` | The figure the row shows: this node's own spend, or the subtree total when nothing measured it. |
| `SubtreeTokensText` | `string` | The subtree total, abbreviated. |
| `HasTokens` | `bool` | There is a token figure to show, own or inherited from the subtree. |
| `ShowSubtreeTokens` | `bool` | `TokensUsed is not null && subtreeTokens > TokensUsed` — true only for a node that has both a measured spend of its own and descendants that spent more. |
| `Duration` / `DurationText` / `HasDuration` | `TimeSpan?` / `string` / `bool` | Forwarded from the row; the scope has none. |
| `StateText` / `ShowStateText` | `string` / `bool` | `ShowStateText` is false for `Completed` — the grey lamp already says "finished", and it is the state most rows are in. Queued vs. running, and cancelled vs. failed, are what the words are for. |
| `IsRunning` | `bool` | Always false for the scope. |
| `CallCount` | `int` | This node's own run's calls, or the subtree's when it has none of its own. |
| `HasDroppedRequests` / `DroppedRequestCount` | `bool` / `int` | Forwarded from the row. |
| `IsExpanded` / `ExpandGlyph` | `bool` / `string` | Defaults to expanded, with glyphs `▾` / `▸`; the glyph follows the state rather than being set beside it. |
| `ScopeTitle` / `ScopeTokens` | `string` / `long?` | The scope root only: the host's name for the session, and what the host's **own** agent spent. `ScopeTokens` may be set after the tree is built, which is why its change hook recomputes the aggregates rather than only notifying. |
| `ToggleExpand()` | `void ToggleExpand()` | Flips `IsExpanded`. |

`NotifyRow()` announces that this node's row moved, for the members that forward to it. A template should bind these members rather than reaching through `Row`: the scope root has no row, and every member here forwards to it, so a path that starts at the row would point at nothing for exactly the node the panel is built around — and compiled bindings do not catch it, since the path is still type-legal.

`RecomputeAggregates()` is called after the children have been filled, so the recursion is bottom-up by construction: a child's total is final before its parent reads it.

Two source-read details on this type and the one below are *inferred* rather than test-pinned: the constructors' `ArgumentNullException` guards (no test constructs either type with a null argument), and the exact predicate behind `ShowStateText` — `SubAgentTreeViewModelTests` asserts the counts, the glyph and the node identity, not this flag.

## Class: `SubAgentTreeViewModel`

`public sealed partial class SubAgentTreeViewModel : IDisposable` — the sub-agent relationship graph as a bindable tree, built over one subsystem.

| Member | Signature | Notes |
|---|---|---|
| Constructor | `SubAgentTreeViewModel(SubAgentScope scope)` | Builds a tree over `scope` and renders it once. Throws `ArgumentNullException` when `scope` is null. The rebuild is queued on the thread this was created on. |
| `ScopeRoot` | `SubAgentTreeNodeViewModel { get; }` | The node standing for the scope itself: the single top of `Tree`, and the parent of every node in `Roots`. Has no `Row`. |
| `Tree` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | Exactly one element — `ScopeRoot` — for a hierarchy control that renders only the first level. |
| `Roots` | `ObservableCollection<SubAgentTreeNodeViewModel> { get; }` | The sub-agents the scope dispatched, one node each — the same collection as `ScopeRoot.Children`, not a copy. |
| `TotalCount` | `int` | Every sub-agent in the tree, at every depth. The scope itself is not counted. |
| `RunningCount` / `CompletedCount` / `FailedCount` / `CancelledCount` | `int` | Per-outcome tallies, so a stop is never folded into a failure. |
| `IsEmpty` / `IsIdle` / `HasFailed` | `bool` | Nothing dispatched / nothing still running / at least one failed. |
| `SubtreeTokens` / `SubtreeTokensText` | `long` / `string` | Tokens spent by every sub-agent in the tree, at every depth — delegated to `ScopeRoot.SubtreeTokens`. |
| `TickElapsed()` | `void TickElapsed()` | Refreshes the elapsed time on every running node and its row, for a panel that shows a clock. **The library owns no timer** — the host drives this from whatever it already has, at whatever rate it finds readable. |
| `Rebuild()` | `void Rebuild()` | Rebuilds from the scopes as they stand, serialized against every other rebuild so a caller does not have to be the thread the tree was created on. A no-op once disposed. |
| `Dispose()` | `void Dispose()` | Detaches from every scope it was watching. **Cancels nothing** and is idempotent. |

### Rebuild semantics

Live rather than snapshotted: every scope in the tree raises `SubAgentScope.Changed` when its roster or any of its rows moves, and a rebuild is **queued** on the thread the tree was created on. Rebuilds are **merged**, so a child starting, a child finishing and a grandchild appearing in the same instant cost one pass rather than three. `Fill` reconciles a level **in place** — departures first, then insertions and moves — rather than clearing it, because the roster republishes on every property write of every row, and a clear would tear down and rebuild every container in the panel several times per child and throw away expansion and selection with them. `SubAgentMetricsTests.ARebuild_ReconcilesTheLevelInPlace` asserts zero resets, exactly one add, and that the nodes that were there are the nodes still there.

Rebuilds are also serialized by an internal gate. The class-wide assumption is that they happen on one thread, and the queue only *delivers* on that thread — but with no `SynchronizationContext` to post to (a headless host, and every test) the rebuild runs **inline on whichever scope raised the change**, so two children finishing in the same instant are two threads inside `Fill`. That is not a rare interleaving: it is what a fan-out does by construction.

`Dispose` also takes that gate, because it is the only third place that mutates the roots, the flat list and the watch set at once. It clears `Roots` **and** the counts together: the counts are derived from the last rebuild, `Rebuild` returns early once disposed, so a total left standing could never be refreshed into agreement — it would describe children the panel no longer holds, for good. `AfterDispose_NothingRebuilds` asserts the counts agree with the nodes.

Subscription is reconciled **during** the walk rather than up front, because children that do not exist yet cannot be named — and `Dispose` unsubscribes from every scope it visited, or a handler would leak per grandchild. `Dispose_DetachesFromEveryScopeItVisited` asserts on what was posted rather than what was drained.

> Source: `SubAgentTreeViewModel.cs`. Tests: `SubAgentTreeViewModelTests`, `SubAgentMetricsTests` under `Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/`. Demo binding (Avalonia): `Examples/Workflow/Avalonia/Demo/Views/Workflow/WorkflowView.axaml` lines 264-299 and `WorkflowView.axaml.cs` lines 87-105.
