# Complexity Analysis — Workflow System

KaTeX is used for the asymptotic bounds. Every figure is grounded in the cited source.

## Spatial Index (`SpatialGridHashMap<T>`)

`SpatialGridHashMap<T>` divides the plane into cells of fixed edge length $s$ (the `cellSize`). Each item is hashed into the cells it overlaps; a viewport query enumerates only the cells the viewport touches (`GetCells` / `CellEnumerator`, lines 190-256).

Insert, remove and (property-changed) reindex touch a bounded number of cells per item — effectively constant for typical node sizes:

$$T_{\text{insert}}(n) = O\left(\left\lceil \frac{w}{s} \right\rceil \cdot \left\lceil \frac{h}{s} \right\rceil\right) \approx O(1)$$

A query over a viewport of width $W$ and height $H$ visits $k$ cells and filters the items inside them:

$$k = \left\lceil \frac{W}{s} \right\rceil \cdot \left\lceil \frac{H}{s} \right\rceil, \qquad T_{\text{query}} = O(k + m)$$

where $m$ is the number of items in those cells. Because the map deduplicates via `_queryScratch`, each distinct item is emitted once (`SpatialGridHashMap.Query`, lines 80-104). Worst case: all items collapse into one cell, degrading to $O(n)$.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SpatialGridHashMap.cs`.*

## Spatial Virtualization (`WorkflowSpatialEx.Virtualize`)

`Virtualize` performs two spatial queries — `QueryAgentBounds(viewport, expansionDepth: 1)` (node-pair providers) and `QueryNodes(viewport)` — then reconciles the `VisibleItems` collection in place (`VirtualizeCore`, lines 113-169). With $k_{\text{pair}}$ / $k_{\text{node}}$ cells visited and $m$ items in those cells:

$$T_{\text{virtualize}} = O\left(k_{\text{pair}} + m_{\text{pair}} + k_{\text{node}} + m_{\text{node}} + v\right)$$

where $v$ is the number of items added/removed from the observable (bounded by the visible set). The depth-1 expansion walks, per directly-visible pair, the connected pairs of its two endpoint nodes via the reverse index (`WorkflowSpatialManager.QueryAgentBounds`, lines 75-116), adding $O(\text{degree})$ work per visible node. Expected case: a typical viewport covers $O(1)$ cells, so the whole pass is expected $O(m + v)$. Re-entrancy is guarded by the `Virtualizing` per-tree flag, so nested calls bail in $O(1)$.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`, `Src/Core/VeloxDev.Core/WorkflowSystem/WorkflowSpatialManager.cs`.*

## Compilation (`CompilerViewModel.CompileAsync`)

`CompileAsync` does a single remembered decomposition from the start node: `CompileState.Visited` guarantees each node is processed once; each node enumerates its output slots' `Targets` (edges). With $V$ nodes and $E$ edges (connections):

$$T_{\text{compile}} = O(V + E)$$

The decomposition is linear (single-in/single-out nodes fold into the current chain) plus router expansion (each key of an `ICompileTimeRouter` recursively compiles one subgraph); every node is visited once, so the total stays $O(V + E)$. In static mode, pruned branches walk the topology from their start to emit the reset signal (`Order = -1`), also guarded by `Visited` and run at most once. Space is $O(V + E)$ for the compiled-graph entries and the visited set.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompileGraphAsync` lines 36-157, `FlushChain` lines 160-169, `MarkStoppedBranch` lines 186-200.*

## Sequential Execution (`CompilerEngine.RunAsync`)

`RunAsync` iterates a graph's entries; the per-entry cost is the sum of its driven nodes:

| Entry | Cost |
|---|---|
| `ExecuteEntry` | $O(N_{\text{chain}})$ — one pass over the linear segment, awaiting each `ReceiveAsync` and writing `context.Data` |
| `BranchEntry` | $O(N_{\text{branch}} + B)$ — $B$ = options scanned to find the chosen key, then the chosen subgraph runs |
| `ParallelEntry` | $\sum_{\text{branches}} O(N_{\text{branch}})$ — branches run **in order** (the shared `RuntimeContext` blackboard is not thread-safe, so no true parallelism) |

Over the whole graph with $N$ driven nodes:

$$T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)$$

in the number of nodes (wall-clock time is dominated by the node workloads, e.g. `Task.Delay(DelayMilliseconds)` in the demo). Unchosen static branches are not driven (`BranchEntry` picks by `CompileKey`; nodes with `Order < redirect target` are skipped). Cross-chain rollback re-runs the whole graph from a target Order, at most 50 times (`MaxRedirects`), so worst case $T_{\text{redirect}} = O(50 \cdot N)$.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs`, `RunGraphAsync` lines 63-89, `RunExecuteAsync` lines 96-148, `RunParallelAsync` lines 189-196.*

## Undo / Redo Stack

Each mutating operation pushes one `IWorkflowActionPair` onto the undo stack. With $n$ actions:

$$T_{\text{undo}}(k) = O(k), \qquad S_{\text{stack}} = O(n)$$

`UndoCommand` pops in $O(1)$ and runs a constant-work action, so undoing $k$ actions costs $O(k)$. Both stacks are `ConcurrentStack<IWorkflowActionPair>`. A batch operation such as `StandardRemoveConnections` aggregates many micro-actions into a single pair, keeping stack depth proportional to logical user actions.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `TreeCache` lines 655-660, `StandardRemoveConnections` lines 430-528.*

## Selector Lookup (`SlotEnumerator.TrySelect`)

`TrySelect` is a dictionary lookup over the condition map maintained incrementally when items are added/removed:

$$T_{\text{TrySelect}} = O(1) \text{ expected}$$

`SetSelector` rebuilds the item list and condition map, submitting an undoable `WorkflowActionPair`; rebuilding costs $O(\text{enum members})$ per selector switch. `ConditionalSlot` objects wrap each slot; deferred removals flush lazily so re-entrant collection changes stay $O(1)$ amortized.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`, `TrySelect` lines 255-258, `SetSelector` lines 260-382.*

## Serialization (`ComponentModelEx.Serialize` / `Deserialize`)

`JsonConvert.SerializeObject` performs a graph traversal. With `PreserveReferencesHandling.Objects`, every object is visited once and assigned a reference id, so the traversal is linear in the number of serialized objects/properties. With $P$ = total serialized objects + properties (bounded by $O(V + E + \text{custom properties})$, $V$ nodes, $E$ links):

$$T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)$$

Two constant factors worth noting:

- `WritablePropertiesOnlyResolver` filters to writable properties, reducing $P$ (reads-only members like `Helper` are skipped) (`ComponentModelEx.cs`, lines 440-486).
- `DictionaryKeyConverter` writes interface-keyed dictionaries (`LinksMap` uses `IWorkflowSlotViewModel` keys) by reference id, adding $O(1)$ per dictionary entry; on read it resolves each key via the `ReferenceResolver` (`ComponentModelEx.cs`, lines 381-438).

Settings (and their resolver's Newtonsoft contract cache) are cached statically, so repeated calls do not re-reflect the type system (`ComponentModelEx.cs`, lines 56-102). The async overloads still materialize the full JSON string / byte array in memory, so memory usage is:

$$S_{\text{json}} = O(P \cdot \text{avg bytes per value})$$

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`.*

## Memory Usage Summary

| Structure | Space | Basis |
|---|---|---|
| `SpatialGridHashMap<T>` | $O(n \cdot c)$ — $n$ items, each in $c$ covered cells | cells hash sets |
| `WorkflowSpatialManager` | $O(V + E)$ — node providers + node-pair providers + reverse index | dictionaries |
| Undo / Redo stacks | $O(n)$ — $n$ submitted pairs | `ConcurrentStack` |
| `CompiledGraph` + entries | $O(V + E)$ | entries + visited set |
| Serialized JSON | $O(P)$ — total serialized size | Newtonsoft string |

## Summary Table

| Operation | Time | Space | Basis |
|---|---|---|---|
| `SpatialGridHashMap.Insert` | $O(1)$ expected | $O(n \cdot c)$ total | bounded cells per item |
| `SpatialGridHashMap.Query` | $O(k + m)$ | $O(1)$ scratch | $k$ = cells in viewport |
| `WorkflowSpatialEx.Virtualize` | expected $O(m + v)$ | $O(1)$ scratch | two spatial queries + visible reconcile |
| Compile (`CompilerViewModel`) | $O(V+E)$ | $O(V+E)$ | remembered decomposition + visited set |
| Execute chain (`CompilerEngine`) | $O(N)$ | $O(N)$ | one pass over entries; rollback worst $O(50N)$ |
| Undo / Redo | $O(1)$ per action | $O(n)$ | concurrent stacks |
| `SlotEnumerator.TrySelect` | $O(1)$ expected | $O(\text{members})$ | dictionary lookup |
| `ComponentModelEx.Serialize` / `Deserialize` | $O(P)$ | $O(P)$ | Newtonsoft graph traversal (PreserveReferences) |
