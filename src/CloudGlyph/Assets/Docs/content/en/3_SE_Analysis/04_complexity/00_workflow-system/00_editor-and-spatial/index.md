# Workflow System — Complexity of the Editor and Spatial Side

KaTeX for the asymptotic bounds; every figure is grounded in the cited source.

## Spatial Index (`SpatialGridHashMap<T>`)

`SpatialGridHashMap<T>` divides the plane into cells of fixed edge length $s$. Each item is hashed into every cell it overlaps (`IndexItem` iterates `GetCells(bounds)`); a viewport query enumerates only the cells the viewport touches (`Query` lines 94-125, `CellEnumerator` lines 317-367).

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

`Virtualize` (lines 97-115) is a re-entrancy-guarded wrapper around `VirtualizeCore` (lines 117-190), which performs `manager.QueryAgentBounds(query, expansionDepth: 1)` (node-pair providers) plus `manager.QueryNodes(query)`, builds the desired item set and reconciles `VisibleItems` in place. With $k_{\text{pair}}$ / $k_{\text{node}}$ cells visited and $m$ items in those cells:

$$
T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)
$$

where $v$ is the number of items added/removed from the observable (bounded by the visible set). The depth-1 expansion walks, per directly-visible pair, the connected pairs of its two endpoint nodes via the reverse index (`WorkflowSpatialManager.QueryAgentBounds` lines 79-124), adding $O(\text{degree})$ work per visible node. Expected case: a typical viewport covers $O(1)$ cells, so the whole pass is expected $O(m + v)$. Nested `Virtualize` calls bail in $O(1)$ via the per-tree `Virtualizing` flag.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`, `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`.*

## Undo / Redo Stack

Each mutating operation pushes one `IWorkflowActionPair` onto the undo stack. With $n$ actions:

$$
T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)
$$

`StandardUndo`/`StandardRedo` pop in $O(1)$ and run a constant-work action. Both stacks are `ConcurrentStack<IWorkflowActionPair>` in the per-tree `TreeCache`. A batch operation such as `StandardRemoveConnections` aggregates many micro-actions into a single pair, keeping stack depth proportional to logical user actions.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSubmit` lines 208-220, `StandardRemoveConnections` lines 428-526, `TreeCache` lines 653-658.*

## Selector Lookup (`SlotEnumerator.TrySelect` / `SetSelector`)

`TrySelect` is a dictionary lookup over the condition map maintained incrementally when items are added/removed:

$$
T_{\text{TrySelect}} = O(1) \text{ expected}
$$

`SetSelector` (lines 260-382) rebuilds the item list and condition map for the new enum/bool/`ISlotProvider` type, and submits an undoable `WorkflowActionPair`; rebuilding costs $O(\text{enum members})$ per selector switch. Deferred removals flush lazily so re-entrant collection changes stay $O(1)$ amortized.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`, `TrySelect` lines 255-258.*

## Serialization (`ViewModelSerializer.Serialize` / `Deserialize`)

The writer walks the object graph through **generated** readers and writers — there is no reflection, and therefore no runtime contract cache to warm. Each object is visited once: `VeloxJsonWriter.WriteStartObject` gives it an object id, and a second encounter writes a reference marker instead of the object again, which is what keeps a graph with `Parent` back-references from expanding. Traversal is linear in the number of written members. With $P$ = written members (bounded by $O(V + E + \text{custom members})$, $V$ nodes, $E$ links):

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

Three constant factors worth noting:

- **The member set is decided at compile time**, not filtered at run time: the generator collects public properties with a public setter, in declaration order, then the `[VeloxProperty]` fields. A read-only member like `Helper` is never a candidate and never costs a branch (`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:912-1025`).
- **Interface-keyed maps** (`LinksMap` keys by `IWorkflowSlotViewModel`) are written as the key's reference id — $O(1)$ per entry — and resolved through the reader's reference table on the way back (`Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:540,625`).
- **A compiled-graph snapshot is smaller by design.** `CompiledGraphEx.SerializeCompiledGraph(graph, includeTree: false)` excludes `IWorkflowTreeViewModel` and `ObservableCollection<IWorkflowSlotViewModel>` properties, so the writer never follows `Parent` into the tree or a slot's `Targets`/`Sources` into the whole connected component. The cost drops from "the tree plus its connected component" to the segment structure plus each node's own state — at the price that the restored nodes are not re-mountable.

Registry lookups are lock-free (an immutable snapshot behind a `volatile` field), and member names are compared in place rather than interned, so neither side allocates a string per member (`Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:83-96`). Deserialization re-resolves a `SlotEnumerator`'s selector type from the serialized `SelectorTypeName` before consumers re-raise derived values. The async overloads still materialize the full JSON string / byte array in memory, so memory usage is:

$$
S_{\text{json}} = O(P \cdot \text{avg bytes per value})
$$

*Source: `Src/Core/VeloxDev.Core/Serialization/`, `Src/Core/VeloxDev.Core.Extension/CompiledGraphEx.cs`.*

## Summary Table

| Operation | Time | Space | Basis |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ expected | $O(n \cdot c)$ total | bounded cells per item |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ scratch | $k$ = cells in viewport |
| `WorkflowSpatialEx.Virtualize` | expected $O(m + v)$ | $O(1)$ scratch | two spatial queries + visible reconcile |
| Undo / Redo | $O(1)$ per action | $O(n)$ | concurrent stacks |
| `SlotEnumerator.TrySelect` | $O(1)$ expected | $O(\text{members})$ | dictionary lookup |
| `ViewModelSerializer.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | generated traversal, one visit per object (id / reference marker) |
| `CompiledGraphEx.SerializeCompiledGraph` (snapshot) | $O(P_{\text{graph}})$ | $O(P_{\text{graph}})$ | writer stops at the graph boundary |
