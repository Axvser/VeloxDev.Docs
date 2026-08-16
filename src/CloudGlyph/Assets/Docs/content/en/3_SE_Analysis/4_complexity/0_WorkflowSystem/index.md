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

## Compilation (CompilerViewModel)

`CompilerViewModel.CompileAsync` does a single remembered decomposition from the start node: `CompileState.Visited` guarantees each node is processed once; each node enumerates its output slots' `Targets` (edges). With $V$ nodes and $E$ edges (connections):

$$T_{\text{compile}} = O(V + E)$$

The decomposition is linear (single-in/single-out nodes fold into the current chain) plus router expansion (each key of an `ICompileTimeRouter` recursively compiles one subgraph); every node is visited once, so the total stays $O(V + E)$. In static mode, pruned branches walk the topology from their start to emit the reset signal (`Order = -1`), also guarded by `Visited` and run at most once. Space is $O(V + E)$ for the compiled-graph entries and visited set.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompileGraphAsync` lines 36-157, `FlushChain` lines 160-169, `MarkStoppedBranch` lines 186-200.*

## Sequential Execution

`CompilerEngine.RunAsync` iterates a graph's entries exactly once; `ExecuteEntry` awaits each node's `ReceiveAsync` result and writes it back to `RuntimeContext.Data` to chain downstream. With $N$ nodes in the graph:

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

in the number of nodes (wall-clock time is dominated by the node workloads, e.g. `Task.Delay(DelayMilliseconds)` in the demo). Unchosen static branches are not driven (`BranchEntry` picks by `CompileKey`; nodes with `Order < redirect target` are skipped). `ParallelEntry` fan-outs run in order (the shared `RuntimeContext` blackboard is not thread-safe, so no true parallelism). Cross-chain rollback re-runs the whole graph from a target Order, at most 50 times (`MaxRedirects`), so worst case $T_{\text{redirect}} = O(50 \cdot N)$.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`, `RunGraphAsync` lines 63-89, `RunExecuteAsync` lines 96-148, `RunParallelAsync` lines 189-196.*

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
| Compile (CompilerViewModel) | $O(V+E)$ | $O(V+E)$ | remembered decomposition + visited set |
| Execute chain (CompilerEngine) | $O(N)$ | $O(N)$ | one pass over entries; rollback worst $O(50N)$ |
| Undo / Redo | $O(1)$ per action | $O(n)$ | concurrent stacks |
| `SlotEnumerator.TrySelect` | $O(1)$ expected | $O(\text{members})$ | dictionary lookup |
