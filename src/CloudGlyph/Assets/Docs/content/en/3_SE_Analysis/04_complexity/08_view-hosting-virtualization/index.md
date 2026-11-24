# View hosting and virtualization

Virtualization answers one question per viewport: which nodes and node-pairs intersect it? A spatial grid answers it in time proportional to the cells covered and the candidates in those cells, not to the document size. The pool then materializes one view per visible item and recycles by runtime type. The weak links are the collection sync after the query, which is quadratic in the visible set, and the grid's deferred reindex, which is linear in the tracked items.

Notation: $C$ grid cells overlapping the query, $k$ candidate items in those cells, $V$ visible items, $n$ tracked items, $T$ view types.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| Grid insert / remove | $O(\text{cells covered})$ | $O(\text{cells})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:61` |
| Grid query | $O(C + k)$ | $O(C + k)$ scratch | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:98` |
| Full reindex | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:224` |
| Bounds, dirty | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:28` |
| Pair query with depth | $O(C + k + \text{depth} \cdot \text{frontier} \cdot d)$ | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs:80` |
| Virtualize sync | $O(V^2)$ worst | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs:95` |
| Pool collection change | $O(\text{changed})$ | $O(\text{active} + \text{recycled})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:125` |
| Materialize / recycle | $O(1)$ each | — | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:319` |
| Adaptive policy feedback | $O(1)$ per batch | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/AdaptiveViewPoolPolicy.cs:80` |

## The grid query

Cell membership is a hash bucket, and each candidate is de-duplicated through a shared scratch set, then precision-filtered against the exact viewport:

```csharp
foreach (var cell in GetCells(viewport))
    if (_grid.TryGetValue(cell, out var set))
        ...
        if (!_queryScratch.Add(item)) continue;
        ...
            ? viewport.Contains(itemBounds.Horizontal, itemBounds.Vertical)
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:110-122`

The bound is $O(C + k)$, not $O(n)$. But $k$ has no distribution-independent guarantee: at low zoom many nodes share a cell, and a dense cell drives $k$ toward $n$. The default cell size in the template host is 200 canvas-local units, set in `TreeHelper.cs:63` and passed to `EnableMap` at `TreeHelper.cs:188`.

The query is an iterator over an instance-level scratch set, so two enumerations of the same map cannot overlap safely. That is an implementation property, not a documented contract.

## The sync back to the observable collection is quadratic

The visible list is an `ObservableCollection`, and the sync adds missing items only after a linear `Contains`, then removes duplicates in a `while` loop that also calls `Contains`:

```csharp
private static void AddIfMissing(Collection<IWorkflowComponent> observable, IWorkflowComponent item)
{
    if (!observable.Contains(item))
        observable.Add(item);
}

private static void RemoveAll(Collection<IWorkflowComponent> observable, IWorkflowComponent item)
{
    while (observable.Contains(item))
        observable.Remove(item);
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs:355-377`

Doing that once per desired item makes the reconcile step $O(V^2)$ in the worst case, which can dominate the $O(C + k)$ query it follows. The visible set is usually a few dozen items, so the constant is small — but it is the reason a virtualization pass is not asymptotically linear.

$$
T_{\text{virtualize}} = O(C + k) + O(V^2)
$$

```plot
{
  "title": "Virtualization: query vs collection sync",
  "grid": true,
  "xAxis": { "domain": [0, 120] },
  "yAxis": { "domain": [0, 14400] },
  "data": [
    { "fn": "2*x", "color": "#4a9eff", "title": "grid query, O(C + k)" },
    { "fn": "x*x", "color": "#f472b6", "title": "sync, O(V^2) worst" }
  ]
}
```

## The pool is proportional to visibility, not to the document

A collection change costs one hash operation per changed item. Materialization pops from a per-type queue or asks the factory; recycling pushes back up to the policy's per-type cap:

```csharp
while (processed < batchSize && pending.Count > 0)
{
    var item = pending.Dequeue();
    if (!pendingSet.Remove(item))
        continue;
    Materialize(item);
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:290-299`

```csharp
if (pools.TryGetValue(itemType, out var pool) && pool.Count > 0)
    view = pool.Dequeue();
...
active[item] = view;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:338-366`

Batches are bounded by `BatchSize` and a frame-time budget, so a large viewport is filled over several frames rather than one. The adaptive policy updates its batch size from measured throughput in constant time per completed batch.

## Memory

The grid holds one entry per item per covered cell plus a tracked-items dictionary, so $O(\text{items} \times \text{cell span})$. The pool holds $O(\text{active})$ views plus at most a per-type recycled cap; `MaxRecycledViewsPerType <= 0` means unlimited recycling, which trades memory for fewer factory calls. The visible list itself is $O(V)$.
