# Complexity Analysis — Workflow Agent

## `WithAutoDiscovery` assembly scan

`WithAutoDiscovery` runs in two passes. Pass 1 enumerates every type in the target assembly ($T$ types) and does constant-time work per type (abstract/interface checks, `IWorkflow*ViewModel` assignability, attribute presence). Pass 2 deep-scans every *registered* component: for a component with $P$ properties, $F$ fields and $M$ methods, each member is resolved into the enum/interface/data buckets with `HashSet`-guarded dedup (`_globallyDiscoveredTypes`), so re-visits are constant-time.

$$
T_{\text{discovery}} = O\!\left(T + \sum_{C \in \text{registered}} (P_C + F_C + M_C) \cdot k\right)
$$

where $k$ is the generic-argument recursion factor (bounded by the maximum generic nesting depth). Registration buckets are `HashSet`s, so `TryRegister*` is $O(1)$ expected. Space is the registered type sets:

$$
S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})
$$

*Source: `WorkflowAgentScope.cs` `WithAutoDiscovery`.*

## `WorkflowStateTracker.TakeSnapshot` / diff

`BuildSnapshot` walks the whole graph: $V$ nodes and $E$ visible links. For each node it reflects over public instance properties (`AppendScalarProps`, $P$ per node) and emits the JSON tree:

$$
T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)
$$

`ComputeDiff` builds `RuntimeId → JObject` dictionaries for nodes and links in $O(V + E)$, then for each node compares scalar/enum properties via `JToken.DeepEquals`:

$$
T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)
$$

where $P' \le P$ is the scalar-prop count in the JSON. Only scalar and enum-typed properties are captured, so the diff never materializes full subtree comparisons.

*Source: `WorkflowStateTracker.cs` `BuildSnapshot`, `ComputeDiff`, `IndexById`.*

## Toolkit dispatch

Each tool is wrapped by `TrackedAIFunction`, whose overhead is $O(1)$ per call (interlocked counters + event raise + optional `MarkDirty`). The pre-flight gate `CheckBudget` is $O(1)$: an `IsToolEnabled` hash-set probe, an optional walk to the root ledger, and three integer comparisons. The tool bodies dominate:

$$
T_{\text{tool}} = O(\text{per-tool work}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)
$$

### Per-tool complexity

| Tool | Time | Basis |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | one pass over nodes, scalar props per node |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | one node, $S$ slots (by-id adds an $O(V)$ id scan) |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | whole graph |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | links / nodes+props |
| `GetWorkflowSummary` | $O(V)$ | distinct type-name pass |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` / `IsConnected` / `FindPath` | $O(V + E)$ | BFS with visited/parent maps |
| `CreateNode` | $O(V)$ expected, $O(1)$ with the spatial map | overlap scan |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | one command dispatch + wait |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | $O(1)$ amortized | slot resolve + Send/Receive commands + `VerifyConnection` |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | reflection patch, per-property rejection rules |
| `RunCompiledWorkflow` / `GetNodeResult` | compile + chain/cone work | see below |
| `ListCreatableTypes` | $O(A \cdot T)$ | assembly scan |
| `ValidateWorkflow` | $O(V + E)$ | node/link pass with duplicate-link dedup |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + handler | user wait dominates |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | see above |

*Source: `WorkflowAgentToolkit.cs` tool bodies; `TrackedAIFunction.cs`; `QueryToolNames`.*

## Compiled run / terminal result

Both chain entries share `RunCompiledRoleAsync` (`WorkflowAgentToolkit.cs`). The compile step builds the compiled graph from the tree; a Root run then drives the whole reachable chain, while a Terminal run drives only the queried node's ancestor cone (so its compile and run costs scale with the cone, not the whole tree):

$$
T_{\text{Root}} = O\big(V + E\big)_{\text{compile}} + O(\text{chain work}), \qquad
T_{\text{Terminal}} = O\big(V_{\text{cone}} + E_{\text{cone}}\big)_{\text{compile}} + O(\text{cone work})
$$

The engine maintains a runtime session (`RuntimeContext`): run bookkeeping (`Status`, `Attempt`, `Outcome`, `Logs`) is $O(1)$ per driven step, and the log is $O(\text{steps})$. The forward-consistent Terminal contract — a router selecting a sibling branch means `TargetReached = false` and an explicit `error` with **no** fabricated value — costs $O(1)$ to check after the run.

## Run-handle family

The handle registry is a `Dictionary<string, CompiledRun>` guarded by one lock; handle allocation is `Interlocked.Increment`. Per call:

- `StartCompiledWorkflow` / `ContinueCompiledWorkflow`: one compile (as above) + one `Dictionary` write — $O(V+E)$ dominated by the compile.
- `GetCompiledRunStatus`: `SnapshotLogs()` is $O(\log)$ under the log lock (a copy of the retained list), then the tail is taken as $\min(40, L)$ lines; the registry read/removal is $O(1)$ expected. Log tail memory is bounded by `RunStatusLogTail = 40`.

$$
T_{\text{status}} = O(\min(40, L)) + O(1), \qquad S_{\text{tail}} = O(40)
$$

- `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`: $O(1)$ — a gate flag flip or a `CancellationTokenSource.Cancel`.

`ContinueCompiledWorkflow` adds one checkpoint load, $O(\text{checkpoint size})$.

## `ToolCallLedger` chain

`Spend` recurses to `Outer`, so the cost of one call is the depth of the ledger chain:

$$
T_{\text{spend}} = O(d), \qquad S_{\text{ledger}} = O(d)
$$

where $d$ is the spawn depth (bounded by the sub-agent depth limit). `ResetChain` is likewise $O(d)$. `Usage` is three lock-free `Volatile.Read`s, $O(1)$.

## `WorkflowAgentContextProvider` render cache

`BuildContext` first reads `Scope.ContextKey` ($O(1)$: a `Version` read plus a budget-band computation) and compares it against the published key. On a hit it returns the previous `AIContext` with no lock and no allocation. On a miss it rebuilds instructions and (only if `Version` moved) the tool list:

$$
T_{\text{render}} = \begin{cases} O(1) & \text{cache hit} \\ O(\text{instructions} + |\text{tools}|) & \text{cache miss} \end{cases}
$$

The capability-envelope test measures the miss cost directly: the envelope stays an order of magnitude smaller than the static skeleton, and 1000 idle turns allocate **0 bytes**.

## `McpScope.LoadAsync`

`LoadAsync` iterates $N$ server configurations; per server the cost is install (local modes) + connect:

$$
T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)
$$

**npm/pip install idempotence.** `EnsureNpmPackageAsync` keys on `"node:{package}@{version}"` (pip: `"py:..."`) in a process-wide list guarded by a global `SemaphoreSlim(1,1)`. The memoized check is $O(1)$ after the first install:

$$
T_{\text{install}} = \begin{cases} O(\text{npm/pip work}) & \text{first time} \\ O(1) & \text{memoized} \end{cases}
$$

**transport + handshake.** `ConnectServerAsync` performs the JSON-RPC `initialize`/`tools/list` handshake; cost is dominated by process startup and the tool list, $O(\text{spawn} + \text{handshake} + \text{toolSchemaSize})$. Per-server failures cost $O(1)$ and do not abort the batch.

## Summary

| Operation | Time | Space | Basis |
|---|---|---|---|
| `WithAutoDiscovery(assembly)` | $O(T + R \cdot m \cdot k)$ | $O(R)$ sets | $T$ types, $R$ registered, $m$ members/component, $k$ generic recursion |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | graph walk + scalar reflection |
| `WorkflowStateTracker` diff | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` index + property `DeepEquals` |
| Toolkit dispatch overhead | $O(1)$ | $O(1)$ | tracked wrapper counters + event |
| `CheckBudget` gate | $O(1)$ (+ $O(d)$ to the root) | $O(1)$ | hash probe + integer compares |
| `ToolCallLedger.Spend` / `ResetChain` | $O(d)$ | $O(d)$ | walks the spawn chain |
| Provider render | $O(1)$ hit / $O(\text{text} + n_{\text{tools}})$ miss | $O(1)$ hit | `ContextKey` cache |
| `GetCompiledRunStatus` | $O(\min(40, L))$ | $O(40)$ | `SnapshotLogs()` + tail |
| `StartCompiledWorkflow` | $O(V + E)$ compile + $O(1)$ | $O(V + E)$ | compile dominates |
| `Pause` / `Resume` / `StopCompiledRun` | $O(1)$ | $O(1)$ | gate flag / token cancel |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{tools})$ | install memoized $O(1)$ after first load |
