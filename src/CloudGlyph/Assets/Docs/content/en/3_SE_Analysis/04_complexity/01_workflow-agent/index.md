# Complexity Analysis — Workflow Agent

## `WithAutoDiscovery` assembly scan

`WithAutoDiscovery` runs in two passes. Pass 1 enumerates every type in the target assembly ($T$ types) and does constant-time work per type (abstract/interface checks, `IWorkflow*ViewModel` assignability, attribute presence). Pass 2 deep-scans every *registered* component: for a component with $P$ properties, $F$ fields and $M$ methods, each member is resolved into the enum/interface/data buckets with `HashSet`-guarded dedup (`_globallyDiscoveredTypes`), so re-visits are constant-time.

Per call over one assembly:

$$T_{\text{discovery}} = O\!\left(T + \sum_{C \in \text{registered}} (P_C + F_C + M_C) \cdot k\right)$$

where $k$ is the generic-argument recursion factor (bounded by the maximum generic nesting depth). Registration buckets are `HashSet`s, so `TryRegister*` is $O(1)$ expected.

Space is the registered type sets:

$$S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})$$

Repeated calls over multiple assemblies accumulate components; the global `_globallyDiscoveredTypes` set guarantees a type is deep-scanned only once across all languages.

*Source: `WorkflowAgentScope.cs` `WithAutoDiscovery` lines 600-662, `ScanComponentMembers` lines 678-738.*

## `WorkflowStateTracker.TakeSnapshot` / diff

`BuildSnapshot` walks the whole graph: $V$ nodes and $E$ visible links. For each node it reflects over public instance properties (`AppendScalarProps`, $P$ per node) and emits the JSON tree:

$$T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)$$

`ComputeDiff` builds `RuntimeId → JObject` dictionaries for nodes and links in $O(V + E)$, then for each node compares scalar/enum properties via `JToken.DeepEquals`:

$$T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)$$

where $P' \le P$ is the scalar-prop count in the JSON. Only scalar and enum-typed properties are captured, so the diff never materializes full subtree comparisons.

*Source: `WorkflowStateTracker.cs` `BuildSnapshot` lines 73-124, `ComputeDiff` lines 126-192.*

## `WorkflowAgentToolkit` tool dispatch

Each tool is wrapped by `TrackedAIFunction` whose overhead is $O(1)$ per call (interlocked counters + event raise + optional `MarkDirty`). The tool bodies dominate:

$$T_{\text{tool}} = O(\text{per-tool work}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)$$

### Per-tool complexity

| Tool | Time | Basis |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | one pass over nodes, scalar props per node |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | one node, $S$ slots (by-id adds an $O(V)$ id scan) |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | whole graph |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | links / nodes+props |
| `GetWorkflowSummary` | $O(V)$ | distinct type-name pass |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` | $O(V + E)$ | BFS with visited set |
| `IsConnected` | $O(V + E)$ | forward/reverse BFS |
| `FindPath` | $O(V + E)$ | BFS shortest path with parent map |
| `CreateNode` | $O(V)$ expected, $O(1)$ with spatial map | overlap scan; spatial `QueryNodes` is $O(k + m)$ cells |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | one command dispatch + wait |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | $O(1)$ amortized | slot resolve + Send/Receive commands + `VerifyConnection` |
| `DisconnectSlots` / `DisconnectSlotsById` | $O(1)$ | `LinksMap` lookup + link delete |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | reflection patch, per-property rejection rules |
| `SetEnumSlotCollection` / `GetEnumSlotByValue` | $O(\text{members})$ | selector switch rebuilds items |
| `ExecuteNode` / `ExecuteNodes` | $O(\text{node work})$ | awaits real completion |
| `CompileWorkflow` (Root) / `CompileNodeResult` (Terminal) | $O(V + E)$ | `CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` builds `CompiledGraph` entries |
| `RunCompiledWorkflow` | $O(V + E)$ compile + $O(\text{chain work})$ | `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` |
| `GetNodeResult` | $O(V_{\text{cone}} + E_{\text{cone}})$ compile + $O(\text{cone work})$ | Terminal reverse-compile of the ancestor cone only |
| `ListCreatableTypes` | $O(A \cdot T)$ | scans assemblies for creatable node/slot types |
| `ValidateWorkflow` | $O(V + E)$ | node/link pass with `HashSet` dedup of duplicate links |
| `GetNodeStatistics` | $O(S + \text{conns})$ | slot/target/source walk |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + handler | user wait dominates |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | see above |

*Source: `WorkflowAgentToolkit.cs` — tool bodies across the class; `TrackedAIFunction` lines 178-242; `QueryToolNames` lines 248-258.*

## Compiled run / terminal result

Both chain entries share `RunCompiledRoleAsync` (`WorkflowAgentToolkit.cs`, lines 1804-1861). The compile step builds the compiled graph from the tree; a Root run then drives the whole reachable chain, while a Terminal run drives only the queried node's ancestor cone (so its compile and run costs scale with the cone, not the whole tree):

$$T_{\text{Root}} = O\big(V + E\big)_{\text{compile}} + O(\text{chain work}), \qquad
T_{\text{Terminal}} = O\big(V_{\text{cone}} + E_{\text{cone}}\big)_{\text{compile}} + O(\text{cone work})$$

The engine maintains a runtime session (`RuntimeContext`): run bookkeeping (`Status`, `Attempt`, `Logs`) is $O(1)$ per driven step, and the log is $O(\text{steps})$. The forward-consistent Terminal contract — a router selecting a sibling branch means `TargetReached = false` and an explicit `error` with **no** fabricated value — costs $O(1)$ to check after the run.

## `McpScope.LoadAsync`

`LoadAsync` iterates $N$ server configurations; per server the cost is install (local modes) + connect:

$$T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)$$

**npm/pip install idempotence.** `EnsureNpmPackageAsync` keys on `"node:{package}@{version}"` (pip: `"py:..."`) in a process-wide list guarded by a global `SemaphoreSlim(1,1)`. The memoized check is $O(1)$ (contains) after the first install; the first install runs the CLI once and records the key, so repeated loads of the same package are $O(1)$ install-wise:

$$T_{\text{install}} = \begin{cases} O(\text{npm/pip work}) & \text{first time} \\ O(1) & \text{memoized} \end{cases}$$

**transport + handshake.** `ConnectServerAsync` builds a `StdioClientTransport` (or `HttpClientTransport` for `Http`), creates the MCP client, and performs the JSON-RPC `initialize`/`tools/list` handshake. Cost is dominated by the server process startup and the tool list:

$$T_{\text{connect}} = O(\text{spawn} + \text{handshake} + \text{toolSchemaSize})$$

Per-server failures cost $O(1)$ and do not abort the batch (the `ServerError` event fires; the server contributes zero tools). Aggregate status maintenance (`McpStatusViewModel`) is $O(1)$ per state change, marshalled to the UI thread when a `SynchronizationContext` is registered.

*Source: `McpScope.cs` `LoadAsync` lines 167-191, `EnsureNpmPackageAsync` lines 300-332, `ConnectServerAsync` lines 382-418.*

## Summary

| Operation | Time | Space | Basis |
|---|---|---|---|
| `WithAutoDiscovery(assembly)` | $O(T + R \cdot m \cdot k)$ | $O(R)$ sets | $T$ types, $R$ registered, $m$ members/component, $k$ generic recursion |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | graph walk + scalar reflection |
| `WorkflowStateTracker` diff | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` index + property `DeepEquals` |
| Toolkit dispatch overhead | $O(1)$ | $O(1)$ | tracked wrapper counters + event |
| Query tools (list/detail/topology) | $O(V \cdot P + E)$ | $O(\text{result})$ | node/slot/property walk |
| Traversal (`SearchForward`, `FindPath`, `IsConnected`) | $O(V + E)$ | $O(V)$ | BFS + visited/parent |
| `CreateNode` overlap avoidance | $O(V)$ linear, $O(1)$ spatial | $O(1)$ scratch | query cells $k = O(1)$ expected |
| `SetEnumSlotCollection` | $O(\text{members})$ | $O(\text{members})$ | selector switch rebuild |
| Compile (`CompileWorkflow`/`CompileNodeResult`) | $O(V + E)$ / $O(V_{\text{cone}} + E_{\text{cone}})$ | $O(V + E)$ | `CompilerViewModel.CompileAsync` builds entries |
| `RunCompiledWorkflow` | $O(V + E)$ compile + chain work | $O(V + E)$ | compile + `RuntimeEngine` drive |
| `GetNodeResult` | $O(V_{\text{cone}} + E_{\text{cone}})$ + cone work | $O(V_{\text{cone}} + E_{\text{cone}})$ | Terminal reverse-compile cone only |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{tools})$ | install memoized $O(1)$ after first load |
