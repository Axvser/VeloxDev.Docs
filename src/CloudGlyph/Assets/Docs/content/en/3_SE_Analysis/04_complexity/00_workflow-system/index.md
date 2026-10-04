# Complexity Analysis — Workflow System

KaTeX is used for the asymptotic bounds. Every figure is grounded in the cited source.

## Sub-pages

| Page | Contents |
|---|---|
| [Complexity of the Editor and Spatial Side](00_editor-and-spatial/index.md) | The editor side: spatial hash insert/query, virtualization, undo/redo stacks, selector lookup, JSON serialization |
| [Complexity of Compilation and Execution](01_compile-and-execute/index.md) | The execution side: compilation (forward and reverse), segment driving, fan-out with a concurrency cap, checkpoint snapshot/restore/re-key, the host-capability seams, `CompiledOutline` |

## The two bounding shapes

Almost every cost in this feature is one of two shapes, and knowing which one an operation is tells you most of what you need:

- **`O(1)` in the item count, `O(cells)` in geometry.** The spatial index and the virtualization pass depend on how much *space* is in view, not on how many nodes exist. A graph ten times larger with the same viewport costs the same per frame.
- **`O(V + E)` or `O(N)` in the graph.** Compilation, execution, checkpoint snapshotting and the outline all touch each node (and each edge, at compile time) a bounded number of times. Nothing here is super-linear in the graph, and the two things that could be — a fan-out group and a redirect — are each capped (`MaxParallelBranches`, `MaxRedirects = 50`).
