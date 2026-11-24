# Workflow auto-layout

Layout is a two-stage pipeline: a hierarchy-alignment stage that orders nodes topologically and places fan-out groups, and a tile-separation stage that sweeps a spatial index until overlaps fall below a tolerance. The alignment stage is near-linear; separation is quadratic in the worst case because nodes packed into one tile are compared pairwise.

Notation: $n$ nodes, $e$ edges, $d$ maximum degree, $s$ sweeps (at most 8), $k_i$ halo candidates for node $i$.

## Cost model

| Operation | Time | Source |
|---|---|---|
| Snapshot the problem | $O(n + e)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutProblemBuilder.cs:25` |
| Scoped traversal (downstream / upstream / both) | $O(n + e)$ BFS | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutProblemBuilder.cs:156` |
| Hierarchy alignment | $O((n + e)\log n + e d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/HierarchyAlignmentStage.cs:28` |
| Tile separation, one sweep | $O(n) + O(\sum m^2)$ per band | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:35` |
| Global overlap repair | $O(\text{passes} \cdot n^2 \log n)$ worst | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:331` |
| Cost measurement | $O(n + e + \sum k_i)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/DefaultWorkflowLayoutCost.cs:19` |
| Apply | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/WorkflowLayoutApplier.cs:28` |

## Alignment sorts, separation sweeps

The topological pass uses a `SortedSet<int>` as the ready queue, which is the source of the $\log n$ factor:

```csharp
var ready = new SortedSet<int>();
...
while (ready.Count > 0)
{
    var node = ready.Min;
    ...
    foreach (var next in outgoing[node])
        if (--indegree[next] == 0) ready.Add(next);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/HierarchyAlignmentStage.cs:240-257`

Separation rebuilds a tile index twice per sweep — once for vertical and once for horizontal pass — and then compares each node only with the candidates its tile halo returns:

```csharp
for (var sweep = 0; sweep < maxSweeps; sweep++)
{
    ...
    var verticalIndex = BuildTileIndex(state, tileSize, originX, originY);
    var verticalBands = BuildBands(state, verticalIndex, vertical: true);
    ...
    if (MaxDelta(state, previousX, previousY) <= Epsilon) break;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:59-74`

Inside a band the neighbour check is a nested loop over placed items:

```csharp
foreach (var p in placed)
    if (!HorizontalOverlap(state, i, p)) continue;
    var required = state.Y[p] + problem.Nodes[p].Height + rowGap;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:120-123`

With the default `TileSize` of 256 world units, a well-spread graph gives small bands and near-linear sweeps. A dense cluster in one tile degenerates to pairwise comparison. The overall bound is:

$$
T_{\text{arrange}}(n,e) = O((n+e)\log n + s\,n^2)
$$

where $s \le \texttt{MaxSweeps} = 8$. The loop exits early when the maximum displacement falls below $\epsilon$.

```plot
{
  "title": "Layout: alignment vs separation",
  "grid": true,
  "xAxis": { "domain": [0, 80] },
  "yAxis": { "domain": [0, 6400] },
  "data": [
    { "fn": "x*log(x+1)", "color": "#4a9eff", "title": "alignment, O(n log n)" },
    { "fn": "x*x", "color": "#f472b6", "title": "separation, O(n^2) dense band" }
  ]
}
```

## Determinism caps parallelism

The global repair pass is deliberately single-threaded; only band processing fans out, and only when the band count reaches `ParallelThreshold` (default 64):

```csharp
if (!context.EnableParallelism || bands.Count < Math.Max(1, parallelThreshold))
    ...
Parallel.ForEach(bands, new ParallelOptions { CancellationToken = context.CancellationToken }, body);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Layout/TileSeparationStage.cs:510-520`

Parallelism changes wall-clock time for large graphs but not the total work. It is skipped for small ones precisely because the scheduling overhead would exceed the pairwise work.

## Dry run and memory

`Arrange` with `DryRun` still builds, solves and measures; only the applier returns without writing positions. The result is a list of placements and a cost report. Working memory is $O(n + e)$ for the state arrays and $O(\sum \text{cells touched})$ for the tile index, which is rebuilt per sweep — so peak allocation, not just peak live memory, grows with the sweep count.
