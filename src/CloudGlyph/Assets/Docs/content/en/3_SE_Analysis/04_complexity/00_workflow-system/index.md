# Complexity Analysis — Workflow System

KaTeX is used for the asymptotic bounds. Every figure is grounded in the cited source.

## Spatial Index (`SpatialGridHashMap<T>`)

`SpatialGridHashMap<T>` divides the plane into cells of fixed edge length $s$. Each item is hashed into every cell it overlaps (`IndexItem` iterates `GetCells(bounds)`); a viewport query enumerates only the cells the viewport touches (`Query` lines 82-106, `CellEnumerator` lines 253-303).

Insert, remove and (property-changed) reindex touch a bounded number of cells per item — effectively constant for typical node sizes:

$$
T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)
$$

A query over a viewport of width $W$ and height $H$ visits $k$ cells and filters the items inside them:

$$
k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)
$$

where $m$ is the number of items in those cells. `_queryScratch` deduplicates so each distinct item is emitted once, and each item's bounds are tested against the viewport (`IntersectsWith`/`Contains`). Worst case: all items collapse into one cell, degrading to $O(n)$. A re-entrancy guard defers grid mutations fired mid-reindex and re-syncs once (`_rerunPending` + `ResyncGrid`), keeping nested zoom cascades amortized $O(1)$ per change.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs`.*

## Spatial Virtualization (`WorkflowSpatialEx.Virtualize`)

`Virtualize` (lines 99-117) is a re-entrancy-guarded wrapper around `VirtualizeCore` (lines 119-192), which performs `manager.QueryAgentBounds(query, expansionDepth: 1)` (node-pair providers) plus `manager.QueryNodes(query)`, builds the desired item set and reconciles `VisibleItems` in place. With $k_{\text{pair}}$ / $k_{\text{node}}$ cells visited and $m$ items in those cells:

$$
T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)
$$

where $v$ is the number of items added/removed from the observable (bounded by the visible set). The depth-1 expansion walks, per directly-visible pair, the connected pairs of its two endpoint nodes via the reverse index (`WorkflowSpatialManager.QueryAgentBounds` lines 79-120), adding $O(\text{degree})$ work per visible node. Expected case: a typical viewport covers $O(1)$ cells, so the whole pass is expected $O(m + v)$. Nested `Virtualize` calls bail in $O(1)$ via the per-tree `Virtualizing` flag.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`, `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`.*

## Compilation (`CompilerViewModel.CompileAsync`)

Compilation is a remembered decomposition. With $V$ nodes and $E$ edges (connections):

$$
T_{\text{compile}} = O(V + E)
$$

- **Root** (`CompileGraphAsync`, lines 59-232): walks downstream from the controller. `CompileState.Visited` guarantees each node is processed once; each node enumerates its output slots' `Targets`, and every edge runs the sender's `AccessAsync` static gate (`GetValidTargetsAsync` lines 397-430) — rejected edges are dropped, so invalid edges only cost one `AccessAsync` call each. Linear runs fold into a `ChainSegment`; routers expand each route key recursively (`BranchSegment`, each option a child `CompiledGraph`); plain-node fan-out and multi-key fan-outs become `ParallelSegment`s whose branches are each a sub-graph. Order is a monotonically continuous counter (`Offset` is carried into downstream graphs, not reset to zero), and join registration is $O(\text{inputs})$ per join point. Static pruning (`MarkStoppedBranch` lines 264-278) walks a skipped branch's topology once to stamp `Order = -1`; it too is `Visited`-guarded.
- **Terminal** (`CompilerViewModel.Reverse.cs`): `BuildAncestorConeAsync` (lines 33-74) is a reverse BFS over `Sources` with the same per-edge `AccessAsync` gate — $O(V + E)$ over the cone. `CompileConeAsync` (lines 82-134) derives the entry frontier, then delegates to the same forward walk restricted to the cone; routers keep real `BranchSegment` semantics with only the in-cone branch compiled (`RestrictRouteToCone`).

Space is $O(V + E)$ for the segment trees plus the visited set and cone.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs`, `CompilerViewModel.Reverse.cs`.*

## Sequential Execution (`RuntimeEngine.RunAsync`)

`RunAsync` (lines 19-68) iterates a graph's segments one pass at a time; the per-segment cost is the sum of its driven nodes:

| Segment | Cost |
|---|---|
| `ChainSegment` | $O(N_{\text{chain}})$ — one pass over the linear segment, awaiting each `ReceiveAsync` and writing `context.Data` |
| `BranchSegment` | $O(N_{\text{branch}})$ — a static branch is chosen by the compile-time locked `CompileKey` in $O(1)$ (option scan); a dynamic branch pays one `ResolveRouteKey` |
| `ParallelSegment` | $\sum_{\text{branches}} O(N_{\text{branch}})$ — branches run **in order** with the shared `RuntimeContext` blackboard restored per branch (`RunParallelAsync` lines 205-214), so no true parallelism |

Each `DriveAsync` (lines 227-261) is $O(1)$ bookkeeping plus the node's own work: it injects the session into `IRuntimeAware` nodes, sets `CurrentOrder`, and when the node is a multi-input join point it boxes the grouped inputs into an `IGroupData` by calling `CollectGroupedInputs` — a dictionary build over the registered input sources, $O(\text{inputs})$, pre-sized to avoid reallocations.

Over the whole graph with $N$ driven nodes:

$$
T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)
$$

in the number of nodes (wall-clock time is dominated by node workloads, e.g. `Task.Delay` in demos). Redirects re-run the whole graph toward a target Order, skipping the contract-preserved prefix (`Order < target`); with at most 50 redirects (`MaxRedirects`), worst case $T_{\text{redirect}} = O(50 \cdot N)$.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`, `CompilerEx/Runtime/Model/RuntimeContext.cs` (`CollectGroupedInputs` lines 127-140).*

## Undo / Redo Stack

Each mutating operation pushes one `IWorkflowActionPair` onto the undo stack. With $n$ actions:

$$
T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)
$$

`StandardUndo`/`StandardRedo` pop in $O(1)$ and run a constant-work action. Both stacks are `ConcurrentStack<IWorkflowActionPair>` in the per-tree `TreeCache`. A batch operation such as `StandardRemoveConnections` aggregates many micro-actions into a single pair, keeping stack depth proportional to logical user actions.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSubmit` lines 210-222, `StandardRemoveConnections` lines 430-528, `TreeCache` lines 655-660.*

## Selector Lookup (`SlotEnumerator.TrySelect` / `SetSelector`)

`TrySelect` is a dictionary lookup over the condition map maintained incrementally when items are added/removed:

$$
T_{\text{TrySelect}} = O(1) \text{ expected}
$$

`SetSelector` (lines 260-382) rebuilds the item list and condition map for the new enum/bool/`ISlotProvider` type, and submits an undoable `WorkflowActionPair`; rebuilding costs $O(\text{enum members})$ per selector switch. Deferred removals flush lazily so re-entrant collection changes stay $O(1)$ amortized.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`, `TrySelect` lines 255-258.*

## Serialization (`ComponentModelEx.Serialize` / `Deserialize`)

`JsonConvert.SerializeObject` performs a graph traversal. With `PreserveReferencesHandling.Objects`, every object is visited once and assigned a reference id, so the traversal is linear in the number of serialized objects/properties. With $P$ = total serialized objects + properties (bounded by $O(V + E + \text{custom properties})$, $V$ nodes, $E$ links):

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

Two constant factors worth noting:

- `WritablePropertiesOnlyResolver` filters to writable properties, reducing $P$ (read-only members like `Helper` are skipped) (`ComponentModelEx.cs`, lines 440-486).
- `DictionaryKeyConverter` writes interface-keyed dictionaries (`LinksMap` uses `IWorkflowSlotViewModel` keys) by reference id, adding $O(1)$ per dictionary entry; on read it resolves each key via the `ReferenceResolver` (`ComponentModelEx.cs`, lines 381-438).

Settings (and their resolver's Newtonsoft contract cache) are cached statically, so repeated calls do not re-reflect the type system (`ComponentModelEx.cs`, lines 52-102). Deserialization re-resolves a `SlotEnumerator`'s selector type from the serialized `SelectorTypeName` before consumers re-raise derived values. The async overloads still materialize the full JSON string / byte array in memory, so memory usage is:

$$
S_{\text{json}} = O(P \cdot \text{avg bytes per value})
$$

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`.*

## Memory Usage Summary

| Structure | Space | Basis |
|---|---|---|
| `SpatialGridHashMap<T>` | $O(n \cdot c)$ — $n$ items, each in $c$ covered cells | cells hash sets |
| `WorkflowSpatialManager` | $O(V + E)$ — node providers + node-pair providers + reverse index | dictionaries |
| Undo / Redo stacks | $O(n)$ — $n$ submitted pairs | `ConcurrentStack` |
| `CompiledGraph` + segments | $O(V + E)$ | segment trees + visited set + cone |
| Runtime output registry | $O(\text{driven nodes})$ | pass-stamped `RegisterOutput` table |
| Serialized JSON | $O(P)$ — total serialized size | Newtonsoft string |

## Summary Table

| Operation | Time | Space | Basis |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ expected | $O(n \cdot c)$ total | bounded cells per item |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ scratch | $k$ = cells in viewport |
| `WorkflowSpatialEx.Virtualize` | expected $O(m + v)$ | $O(1)$ scratch | two spatial queries + visible reconcile |
| Compile (`CompilerViewModel`, Root / Terminal) | $O(V+E)$ | $O(V+E)$ | remembered decomposition + reverse cone + visited set |
| Execute segments (`RuntimeEngine`) | $O(N)$ | $O(N)$ | one pass over segments; join aggregation $O(\text{inputs})$; redirect worst $O(50N)$ |
| Undo / Redo | $O(1)$ per action | $O(n)$ | concurrent stacks |
| `SlotEnumerator.TrySelect` | $O(1)$ expected | $O(\text{members})$ | dictionary lookup |
| `ComponentModelEx.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | Newtonsoft graph traversal (PreserveReferences) |
