# Complexity Analysis — WorkflowSystem

## Spatial Index (SpatialGridHashMap)

`SpatialGridHashMap<T>` divides the plane into cells of fixed edge length $s$ (the `cellSize`). Each item is hashed into the cells it overlaps; a viewport query enumerates only the cells the viewport touches.

Insert, remove and (property-changed) reindex touch a bounded number of cells per item — effectively constant:

$$T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)$$

A query over a viewport of width $W$ and height $H$ visits $k$ cells and filters the items inside them:

$$k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)$$

where $m$ is the number of items in those cells. Because the map deduplicates via `_queryScratch`, each distinct item is emitted once. Worst case: all items collapse into one cell, degrading to $O(n)$.

Expected case with cell size $s = 200$ and typical node sizes, a viewport covers $O(1)$ cells, so `WorkflowSpatialEx.QueryNodes` is expected $O(k)$ with $k = O(1)$ cells.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SpatialGridHashMap.cs`, `GetCells`/`CellEnumerator` lines 190-256.*

## Compilation (BFS / DFS)

The compiler builds adjacency lists from slot targets/sources once, then traverses. With $V$ nodes and $E$ edges (connections):

$$T_{\text{adjacency}} = O(V + E)$$

Each of BFS and DFS visits every node once (guarded by `globalVisited`):

$$T_{\text{compile}} = O(V + E)$$

Cycle detection (`DfsFindCycle`) is a single DFS over the whole graph, also $O(V + E)$, performed once regardless of the number of `Omni` entry points. Sorting same-depth neighbors by `CompilePriority` adds a factor of $O(\deg \log \deg)$ per node. Space is $O(V + E)$ for the adjacency lists and visited sets.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Compilation/Compiler.cs`, `BuildForwardAdjacency` lines 153-174, `TraverseBfsFrom` lines 252-296, `TraverseDfsFrom` lines 300-336, `DetectCycle` lines 353-389.*

## Sequential Execution

`CompilationResult.ExecuteAsync` iterates the ordered items exactly once, awaiting each node's `WorkCommand.Exited`. With $N$ compiled items:

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

in the number of nodes (wall-clock time is dominated by the node workloads, e.g. `Task.Delay(DelayMilliseconds)` in the demo). The executor skips unchosen router branches via a `HashSet<int>` of skipped item IDs, so the loop never re-executes a node.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Compilation/Models/CompilationResult.cs`, `ExecuteCoreAsync` lines 157-260.*

## Undo / Redo Stack

Each mutating operation pushes one `IWorkflowActionPair` onto the undo stack. With $n$ actions:

$$T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)$$

`UndoCommand` pops in $O(1)$ and runs a constant-work action, so undoing $k$ actions costs $O(k)$. Both stacks are `ConcurrentStack<IWorkflowActionPair>`. A batch operation such as `StandardRemoveConnections` aggregates many micro-actions into a single pair, keeping stack depth proportional to logical user actions.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `TreeCache` lines 643-654, `StandardRemoveConnections` lines 418-516.*

## Selector Lookup (SlotEnumerator.TrySelect)

`TrySelect` is a dictionary lookup over the condition map maintained incrementally when items are added/removed:

$$T_{\text{TrySelect}} = O(1) \text{ expected}$$

`SetSelector` rebuilds the item list and condition map, submitting an undoable `WorkflowActionPair`; rebuilding costs $O(\text{enum members})$ per selector switch. `ConditionalSlot` objects wrap each slot; deferred removals flush lazily so re-entrant collection changes stay $O(1)$ amortized.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`, `TrySelect` lines 132-135, `SetSelector` lines 137-226.*

## Summary

| Operation | Time | Space | Basis |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ expected | $O(n)$ total | bounded cells per item |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ scratch | $k$ = cells in viewport |
| Compile (BFS/DFS) | $O(V+E)$ | $O(V+E)$ | single traversal + adjacency |
| Execute chain | $O(N)$ | $O(N)$ | one pass over items |
| Undo / Redo | $O(1)$ per action | $O(n)$ | concurrent stacks |
| `SlotEnumerator.TrySelect` | $O(1)$ expected | $O(\text{members})$ | dictionary lookup |
