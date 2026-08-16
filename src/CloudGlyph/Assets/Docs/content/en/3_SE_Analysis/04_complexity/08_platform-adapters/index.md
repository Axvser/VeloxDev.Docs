# 08 · Platform Adapters — Complexity

Time and space complexity of the platform-adapter core operations. Bounds are derived from the WPF adapter source and demo; anything not demo-exercised is `*inferred*` from source. Let $N$ = total nodes, $V$ = visible nodes, $P$ = pooled views, and $b$ = batch size.

## `ViewPool` / `ViewManager` reuse & virtualization

`ViewManager` keeps a per-type queue of pooled views. A visible item either hits the pool (dequeue + re-bind) or, once per type, runs `template.LoadContent()`.

| Operation | Cost | Notes |
|---|---|---|
| Materialize a visible item | amortized $O(1)$ | pool hit when available; otherwise template instantiation (paid once per type) |
| Hide an item (removed from `VisibleItems`) | $O(1)$ | collapse + clear `DataContext` + enqueue into the pool |
| Batched flush | $O(b)$ per dispatcher tick | $b = 3$ (WPF-verified); the render budget per frame stays bounded |
| Reset all | $O(A)$ | $A$ = active views; collapse + re-pool each |
| Template lookup | $O(1)$ amortized | `_templateMap` cache; first miss walks resources |

Because views are reused rather than destroyed, the steady-state allocation is amortized $O(1)$ per add/remove, and the GC pressure from scrolling/zooming large graphs is bounded.

## Minimap projection

`WorkflowMinimapOverlay.RefreshMinimapData` unions all node bounds only when marked dirty:

$$b_w = \max_i(n_{x,i} + n_{w,i}) - \min_i(n_{x,i}), \qquad O(N)\ \text{on dirty}$$

The per-render projection of each visible node rect is $O(1)$:

$$x_i = o_x + (n_{x,i} - b_l)\,s, \qquad y_i = o_y + (n_{y,i} - b_t)\,s$$

with scale

$$s = \min\!\left(\frac{d_w}{b_w},\ \frac{d_h}{b_h}\right)$$

Dragging the viewport indicator maps back to world coordinates in $O(1)$ and scrolls the viewer:

$$w_{cx} = \frac{a_x - o_x}{s} + b_l, \qquad scroll_x = w_{cx} - \frac{v_w}{2} + c_x$$

| Operation | Cost |
|---|---|
| Global bounds refresh (on dirty) | $O(N)$ |
| Per-frame render of node rects | $O(V)$ — each rect $O(1)$ |
| Viewport indicator drag → scroll | $O(1)$ |

## `WorkflowSurfaceBehavior` pan / zoom transforms

Every mouse-move during pan is $O(1)$: compute the candidate offset, clamp against the scroll maximum, grow `Layout.NegativeOffset`/`PositiveOffset` at the edges, then two `ScrollTo*` calls and one `UpdateVisibleRegion` that writes `Helper.Viewport`.

| Operation | Cost |
|---|---|
| Per pan tick (mouse move) | $O(1)$ |
| Scroll change → visible-region update | $O(1)$ |
| Layout growth at the edge | $O(1)$ per event; forces a `ScrollViewer` re-measure of the enlarged `Canvas` only when layout is invalidated |

The zoom/pan transform is a single `TranslateTransform` applied through `WorkflowCanvasTransformBehavior`; node/link views read it once per frame at render time, so the transform itself adds no per-node bookkeeping.

## Per-frame render: visible vs total

Without the pool, rendering is $O(N)$. With `ViewPool` bound to `Helper.VisibleItems`, only the visible subset is materialized:

$$R_{\text{frame}} = O(V), \qquad V \ll N \text{ for large graphs}$$

| Metric | Bound |
|---|---|
| Render per frame | $O(V)$ — visible items only |
| Active-view memory | $O(V)$ |
| Pooled-view memory | $O(P)$ (recycled views kept alive for reuse) |
| Per-frame allocation | amortized $O(b)$ ($b=3$) — bounded regardless of $N$ |
| Minimap per-frame render | $O(V)$ node rects, each $O(1)$ |

## Summary

The adapter layer keeps per-frame cost proportional to what is on screen, not what is in the graph: virtualization bounds rendering to $V$, the view pool bounds allocations to a small batch per frame, and the minimap projects each visible node in $O(1)$ after an $O(N)$ dirty-only bounds pass. The pan path is $O(1)$ per input event.
