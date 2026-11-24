# Sub-Agents

A sub-agent is a nested `WorkflowAgentScope` with a narrowed tool surface and a smaller ledger. Spawn cost is configuration work — set intersections and version bumps — while the recurring costs are a depth walk per tool call and a full roster copy per status change.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | direct children in one scope |
| $N$ | nodes in the whole sub-agent forest |
| $w$ | width of one tree level |
| $d$ | spawn depth |
| $T$ | tools available to the parent |
| $g$ | tools granted to the child |
| $S$ | skills or MCP servers considered |

## Spawn

`TrySpawn` first descends the budget: it takes the parent ledger's remaining allowance and grants at most one less (`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs:459-470`).

```csharp
// ── the allowance: a share of what the parent has left, and never the whole of it ──
var parentLedger = parent.CreateToolkit().Ledger;
var remaining = RemainingAllowance(parent, parentLedger);
var granted = Math.Min(request.MaxToolCalls ?? remaining, remaining - 1);
if (granted < 1)
{
    refusal = "No tool-call allowance remains for a sub-agent. The session's budget is spent, or this "
            + "agent's own share is; report what you have done rather than delegating further.";
    return null;
}
```

The `remaining - 1` clamp is the termination argument:

$$
\text{granted} = \min(\text{requested}, \text{remaining} - 1) < \text{remaining}
$$

so grants strictly decrease along every root-to-leaf path and $d$ is bounded by the root cap.

Tool and skill selection then intersects the request with what the parent offers, using `List.Contains(..., OrdinalIgnoreCase)` per name (`SubAgentScope.cs:510-522`, `:684-699`), and switches off every ungranted tool in a loop that scans the grant list (`SubAgentScope.cs:562-564`).

$$
T_{\text{spawn}} = O(d + w \cdot T + T \cdot g + S)
$$

Every real switch-off also bumps the child scope's `Version`, so the spawn's cost includes one render invalidation.

## Ledger accounting

`ToolCallLedger.Spend` increments three counters and recurses to `Outer` (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ToolCallLedger.cs:57-68`), and `RemainingAllowance` reads `Root` and the three counters (`SubAgentScope.cs:757-778`).

$$
T_{\text{spend}} = O(d), \qquad T_{\text{remaining}} = O(d)
$$

This is the price of a cap that a child cannot quietly exceed: every call pays for the whole ancestor chain.

## Roster updates

`Republish` re-projects every entry into a fresh `SubAgentSummary[]` and copies each row's dropped-request list (`SubAgentScope.cs:385-412`). It is wired to every row's `PropertyChanged`, so one row write copies the whole roster.

$$
T_{\text{publish}} = O(n + D)
$$

where $D$ is the total dropped-line count. `RefreshCallCounts` reads each child's toolkit usage in $O(n)$ because the toolkit is cached (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:1555`). `List`, `GetResult` and `RowsFor` each force a republish, and `Find` is a linear scan under the lock (`SubAgentScope.cs:915-919`, `:942-986`). A caller that lists after every change is therefore $O(n^2)$.

## Wait, result and cancel

`WaitAsync` materialises the selected rows and races `Task.WhenAll` against a delay; the timeout is detected by reference (`SubAgentScope.cs:965-978`). Setup is $O(n)$, and wall time is bounded by `timeoutMs`. `Cancel` performs a linear `Find`, then `GetResult`, so it is $O(n)$ including the republish.

## Tree view

`SubAgentTreeViewModel.Rebuild` reconciles in place: existing nodes are looked up by id in a dictionary, departures are removed backwards, and arrivals use `IndexOf` plus `Move` (`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentTreeViewModel.cs:425-447`). Because `IndexOf` and `SubAgentsOf` are both linear scans, one level of width $w$ costs $w^2$.

$$
T_{\text{tree}} = O\left(N + \sum_{\text{levels}} w^2\right)
$$

```plot
{
  "title": "Tree rebuild: balanced vs. one wide level",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "N nodes" },
    { "fn": "x^2", "color": "#f472b6", "title": "flat fan-out" }
  ]
}
```

`RecomputeAggregates` sums child subtotals bottom-up once per visited node, $O(N)$ for the rebuild, and raises seven notifications per node (`SubAgentTreeViewModel.cs:225-245`). `QueueRebuild` coalesces only when a UI `SynchronizationContext` is present and not current (`:493-510`); without one, every `Changed` runs a synchronous full rebuild.

## Cached renders

`SubAgentAgentContextProvider` caches instructions and tools on the scope `Version` and hands back the same instances otherwise (`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentAgentContextProvider.cs:77-96`). The roster block is rebuilt only on a version change, but it copies each child's result before truncating to 200 characters (`SubAgentAgentToolkit.cs:296-334`), so the render is $O(n + \sum \text{result length})$ rather than $O(n)$.

## Dispose

`DisposeAsync` snapshots running entries, cancels all, awaits every run and unsubscribes every row (`SubAgentScope.cs:1019-1054`). Bookkeeping is $O(n)$; wall time is the slowest child.

## Related

- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — the ledger and policy a child inherits.
- [Agent Dashboard and Transcript](../22_agent-dashboard-transcript/index.md) — the other consumer of the status rows.
