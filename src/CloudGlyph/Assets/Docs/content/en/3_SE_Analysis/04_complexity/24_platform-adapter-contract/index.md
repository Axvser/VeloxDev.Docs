# Platform Adapter Contract

The contract every GUI closes is a set of constant-time conversions wrapped around two indexed structures. Input routing is bounded by a hard-coded chain of at most three helpers. Virtualization is a spatial hash plus a view pool; viewport restore is a single deferred write. Nearly everything in this layer is $O(1)$; the exceptions are the spatial index and the pool's collection rescan. Bounds are read from the cited control flow; where a collection's hash or comparison cost depends on item-provided members, the bound is expected-case.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | nodes |
| $l$ | links |
| $v$ | visible items |
| $g$ | grid cells the query viewport overlaps |
| $c_i$ | cells covered by item $i$'s bounds |
| $s$ | cell size |
| $P$ | pairs/nodes reached by one query |
| $H$ | event subscribers |
| $d$ | input chain depth ($\le 3$) |

## Input routing

`WorkflowInput.Route` first synthesises exit/enter events when the pointer target changes, then bubbles through a fixed chain: slot helper, owning node helper, tree helper; node or link helper, then tree helper (`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:299-317`, `:358-378`).

```csharp
private IEnumerable<IWorkflowHelper> Chain(IWorkflowComponent? target)
{
    switch (target)
    {
        case ISlotComponent slot:
            yield return slot.GetHelper();
            if (slot.Parent is { } owner) yield return owner.GetHelper();
            break;

        case INodeComponent node:
            yield return node.GetHelper();
            break;

        case ILinkComponent link:
            yield return link.GetHelper();
            break;
    }

    // 空白画布（target 为 null）与树本身也落到这里：链上只剩树一级。
    yield return tree.GetHelper();
}
```

One event costs

$$
T_{\text{route}} = O(d \cdot (1 + H_d)), \qquad d \le 3
$$

so routing is independent of graph size. A target change adds two extra bubbles and allocates two event objects. Scroll, navigation and the grid/minimap contracts are single adapter calls or property bags.

## Spatial index

`SpatialGridHashMap` stores `Dictionary<CellKey, HashSet<T>>` plus a tracked-item map and an unindexed set (`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:14-25`). `CellKey` hashes two integers with `HashCode.Combine` (`CellKey.cs:4-16`). Insert indexes an item into every cell its bounds overlaps; items with empty bounds are parked until they are measured (`SpatialGridHashMap.cs:67-81`, `:147-151`, `:342-348`).

$$
c_i = \left(\left\lceil \frac{w_i}{s} \right\rceil + 1\right)\left(\left\lceil \frac{h_i}{s} \right\rceil + 1\right)
$$

$$
T_{\text{insert}} = O(c_i) \text{ expected}, \qquad S_{\text{grid}} = O\left(\sum_i c_i\right)
$$

A long link's bounds can cover a very large rectangle, and there is no per-item cell cap. Cell count grows with area divided by $s^2$; a small cell size is quadratic in extent.

```plot
{
  "title": "Grid cells covered by an item (cell size 1, 10, 50)",
  "grid": true,
  "xAxis": { "domain": [0, 100] },
  "yAxis": { "domain": [0, 12000] },
  "data": [
    { "fn": "(x/1+1)^2", "color": "#f472b6", "title": "s = 1" },
    { "fn": "(x/10+1)^2", "color": "#a78bfa", "title": "s = 10" },
    { "fn": "(x/50+1)^2", "color": "#4a9eff", "title": "s = 50" }
  ]
}
```

A query enumerates the cells of the query rectangle, dedupes through a shared scratch set, and tests point or intersection visibility (`SpatialGridHashMap.cs:111-125`).

$$
T_{\text{query}} = O(g + k + U \cdot c)
$$

where $U$ is the number of items still unindexed. Because `Query` is an iterator, `EnsureIndexed` runs on the first `MoveNext`: it may perform up to four full `ResyncGrid` passes and re-examine every unindexed item (`:250-256`). A full resync is $O(n \cdot c)$ and runs once after a re-entrant bounds cascade (`:158-237`).

`WorkflowSpatialManager` adds a reverse index from node to node-pairs and expands a query by a bounded BFS over it (`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs:80-125`).

$$
T_{\text{agent-query}} = O(P)
$$

independent of total graph size while the viewport is small. `RetryPendingLinks` scans the pending set on every node addition, potentially $O(n \cdot l)$ across an unlucky add order.

## View pool

`ViewPoolCore` keeps a per-runtime-type queue of free views, an identity map of active views, and a pending queue with a dedupe set (`Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:34-47`). `ProcessNextBatch` drains up to `BatchSize` items or a frame budget; `Materialize` reuses a queued view or calls the factory, and negative-caches unsupported types (`ViewPool.cs:274-317`, `:319-378`).

```csharp
if (pools.TryGetValue(itemType, out var pool) && pool.Count > 0)
{
    view = pool.Dequeue();
    reusedViewCount++;
}

if (view is null)
{
    view = host.Factory.CreateView(typedItem);
    if (view is null)
    {
        unsupportedTypes.Add(itemType);
```

Acquire and recycle are $O(1)$ expected; realising $v$ items is $O(v)$ spread over $\lceil v / \text{BatchSize} \rceil$ dispatcher turns. The default policy uses `BatchSize = 3`, no frame budget and unlimited recycling per type (`ViewHosting/ViewHostCore.cs:91-100`), so latency is favoured and the recycled set can grow to every item ever materialised.

`RenderLinks` is the exception: each collection notification rescans the whole source to collect link items, $O(i)$ per add/remove/replace/reset when a link layer is active (`ViewPool.cs:159-162`, `:238-250`). With the default null link layer this is skipped.

## Surface math and viewport restore

All conversion, clamp, centering and minimap helpers are $O(1)$ (`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:31-32`, `:58-67`, `:254-314`). `SurfaceMetrics.Create` derives corners from the surface size, ruler band and scrollbars in constant time (`GUI/Surface/SurfaceMetrics.cs:73-104`).

`SurfaceViewportRestoreCore.Capture` records a pending offset once per tree instance; `Schedule` defers exactly one callback, re-checks the flags, reads the platform maxima, clamps and applies (`GUI/Surface/SurfaceViewportRestoreCore.cs:39-95`).

$$
T_{\text{restore}} = O(1)
$$

One exception: `EnsureNegativeCover` scans every node on zoom to keep the negative canvas covered, $O(n)$ per zoom (`WorkflowSurfaceMath.cs:454-497`).

## Conformance kit

`TestGraph.Create` builds a fixed three-node, one-link graph through synchronous helpers and places one node far off-canvas so only a scrolled viewport sees it (`Src/Test/Headless/VeloxDev.AdapterTestKit/TestGraph.cs:56-87`). It is $O(1)$ and carries no pool or spatial behaviour of its own.

## Related

- [WPF Adapter](../25_wpf-adapter/index.md) — one concrete closure of this contract.
- [Headless CLI](../23_headless-cli/index.md) — the contract exercised without a window.
