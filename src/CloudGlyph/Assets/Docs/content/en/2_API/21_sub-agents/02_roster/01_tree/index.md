# Tree

`SubAgentTreeViewModel` projects several scopes' flat rosters into one bindable tree. It is live rather than snapshotted and is not a second source of truth: every value forwards to a row.

## Class: SubAgentTreeViewModel

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `SubAgentTreeViewModel(SubAgentScope scope)` | Builds a tree over a scope and renders it once. |
| `ScopeRoot` | `SubAgentTreeNodeViewModel` | The node standing for the scope itself; the single top of the tree. |
| `Roots` | `ObservableCollection<SubAgentTreeNodeViewModel>` | The children the scope dispatched, one node each. |
| `TotalCount` | `int` | Every child at every depth; the scope itself is not counted. |
| `RunningCount` | `int` | Still working. |
| `CompletedCount` | `int` | Finished with a result. |
| `FailedCount` | `int` | Failed. |
| `CancelledCount` | `int` | Cancelled. |
| `IsEmpty` | `bool` | Nothing dispatched yet. |
| `IsIdle` | `bool` | Nothing still running. |
| `HasFailed` | `bool` | At least one child failed. |
| `SubtreeTokens` | `long` | Tokens spent by every child at every depth. |
| `SubtreeTokensText` | `string` | The same total as display text. |
| `TickElapsed()` | `void TickElapsed()` | Refreshes elapsed time on every running node. The host drives it from its own timer. |
| `Rebuild()` | `void Rebuild()` | Rebuilds from the scopes as they stand, on the calling thread. Serialized against other rebuilds. |
| `Dispose()` | `void Dispose()` | Detaches from every scope it watched. **The children keep running.** |

Rebuilds are merged, so several children changing at once cost one pass. Node identity survives a rebuild: an existing node is re-parented rather than replaced, so an expanded node stays expanded.

Closing a panel is not a decision about the work the panel was showing; cancel through the scope or `CancelSubAgent` instead.

## Class: SubAgentTreeNodeViewModel

One node: a roster row and the nodes of the children that row spawned. The top node stands for the scope and has no `Row`.

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `SubAgentTreeNodeViewModel(SubAgentStatusViewModel row, SubAgentTreeNodeViewModel? parent)` | Builds the node for one dispatched child. |
| `Row` | `SubAgentStatusViewModel?` | The row this node shows, or `null` for the scope root. |
| `Parent` | `SubAgentTreeNodeViewModel?` | The spawning node, or `null` at the top. |
| `Children` | `ObservableCollection<SubAgentTreeNodeViewModel>` | The children this node dispatched, in spawn order. |
| `Id` | `string` | The handle, forwarded. |
| `Depth` | `int` | 0 for the scope, 1 for a direct child. |
| `IsScopeRoot` | `bool` | Whether this node is the scope itself. |
| `Title` | `string` | What the spawn named the task, or the scope's own name at the top. |
| `HasChildren` | `bool` | Whether there is anything to expand into. |
| `TokensUsed` | `long?` | This node's own spend, not its subtree's. |
| `SubtreeTokensText` | `string` | The subtree total, abbreviated. |
| `HasTokens` | `bool` | Whether there is a token figure, own or inherited. |
| `TokensText` | `string` | The figure the row shows: own spend, or subtree total when unmeasured. |
| `ShowSubtreeTokens` | `bool` | True only when the node has both a measured spend and descendants that spent more. |
| `Duration` | `TimeSpan?` | This node's own run time, or `null`. |
| `DurationText` | `string` | Elapsed time as text; empty when none. |
| `HasDuration` | `bool` | Whether there is elapsed time to show. |
| `StateText` | `string` | The row's state as text; empty for the scope. |
| `ShowStateText` | `bool` | Whether the state is worth printing beside the lamp. |
| `IsRunning` | `bool` | Whether this node's own run is going; always false for the scope. |
| `CallCount` | `int` | Calls by this node's own run, or its subtree's when it has none. |
| `HasDroppedRequests` | `bool` | Whether this node's spawn asked for something it did not get. |
| `DroppedRequestCount` | `int` | How many requests were refused. |
| `ToggleExpand()` | `void ToggleExpand()` | Shows or hides this node's children. |

## Example

```csharp
using VeloxDev.AI.SubAgents;

using var roster = new SubAgentTreeViewModel(subAgents);
Console.WriteLine($"idle: {roster.IsIdle}, total: {roster.TotalCount}");
```

## Related

- [Summary and row](../00_summary-and-row/index.md) — the rows this tree forwards to.
- [SubAgentScope](../../00_sub-agent-scope/index.md) — the rosters it watches.
