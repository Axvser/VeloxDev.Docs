# 08 · Platform Adapters — Complexity

Time and space complexity of the platform-adapter core operations. Bounds are derived from the WPF adapter source and the WPF tree-view template; detail not exercised by a demo is `*inferred*` from source. Let $N$ = total model nodes, $V$ = visible (materialized) views, $C$ = spatial-grid cells overlapping the viewport, $P$ = pooled views, and $b$ = batch size.

## View pooling & virtualization

`WorkflowSurfaceBehavior` keeps `Helper.Viewport` current on every scroll/pan; the spatial index (`WorkflowSpatialManager` + `SpatialGridHashMap`) turns that viewport into the `VisibleItems` collection the canvas panel is bound to. `ViewManager` (created per `Panel` by `ViewPool`) only ever renders the items in that collection.

| Operation | Cost | Notes |
|---|---|---|
| Spatial visible-set pass (`WorkflowSpatialEx.Virtualize`) | $O(V + C)$ | Region query over the node/node-pair grid maps plus a 1-hop connection expansion; the result is diffed into the in-place `VisibleItems` collection (stale removed, missing added), each item $O(1)$ by reference identity |
| Materialize a visible item | amortized $O(1)$ | pool hit (dequeue + re-bind), else one `template.LoadContent()` per concrete type |
| Hide an item (removed from `VisibleItems`) | $O(1)$ | collapse + clear `DataContext` + enqueue into the per-type pool |
| Batched flush | $O(b)$ per dispatcher `Background` tick | $b = 3$ (verified in WPF source); the whole batch drains in $\lceil V/b \rceil$ ticks, so a frame never materializes more than a small constant |
| Reset / detach all | $O(V)$ | collapse + re-pool each active view |
| Template lookup | amortized $O(1)$ | per-concrete-type `_templateMap` cache; a miss walks `TemplateSelector` → panel/visual-ancestor resources → `Application.Current.Resources` |

Reuse instead of destroy keeps the steady-state allocation amortized $O(1)$ per add/remove, so pan/zoom over large graphs does not create GC pressure proportional to $N$.

## Zoom: scale-aware anchor collapse

Zoom is not a single render transform. The surface writes a smaller `CanvasLayout.Scale` (a *collapse* factor — wheel-up divides by $1/1.1$); each `NodeDefaultViewModel`'s `Anchor`/`Size` getters collapse toward the world origin by that scale, and a per-node `WorkflowNodeScaleTracker` re-raises them when `Scale` changes.

| Operation | Cost | Notes |
|---|---|---|
| One zoom notch (wheel tick) | $O(N)$ model notify + $O(V)$ rebind | every model node's scale tracker fires (`Anchor`/`Size` re-raised), but only the $V$ materialized views re-bind and re-lay out |
| `CanvasLayout.Update` auto-extend | $O(1)$ | recomputes `ActualSize`/`ActualOffset`; no per-node work |
| `EnsureNegativeCover` (deep-zoom reachability) | $O(N)$ | scans every node anchor once to grow `NegativeOffset` so negative-world content stays scrollable; monotonic, no-op when positive-only |
| Viewport-center pivot keep | $O(1)$ | `WorldAtViewportCenter`/`PivotCenterScroll` capture the world point under the viewport center; the canvas is never translated, only the scroll moves |
| Slot-anchor re-sync after collapse | $O(V_s)$ | `WorkflowSlotLayoutBehavior` re-reads each visible slot center (`LayoutUpdated`/`SizeChanged`) so link endpoints track the collapsed node in the same frame |

The zoom cost therefore scales with the model ($O(N)$ notifications) but the per-frame visual work stays bounded to what is on screen; the deep-zoom cover pass is a dirty-style, per-gesture $O(N)$.

## Pan & overscroll growth

| Operation | Cost |
|---|---|
| Per pan tick (mouse move) | $O(1)$ — compute candidate offset, clamp, two `ScrollTo*` calls, one `UpdateVisibleRegion` |
| Visible-region update on scroll | $O(V + C)$ — the viewport write triggers a re-virtualize pass |
| Overscroll growth at an edge | $O(1)$ per event; `ClampScrollOffset` grows `NegativeOffset`/`PositiveOffset` discretely (`DefaultPanExtendRatio = 0.15`), then the `ScrollViewer` re-measures the enlarged canvas only when layout is invalidated |

## Minimap projection

`WorkflowMinimapOverlay` marks itself dirty from collection/property changes (never polls) and caches the union bounds plus one rect per node.

| Operation | Cost |
|---|---|
| Global-bounds refresh (on dirty) | $O(N)$ — union over all cached node rects (`WorkflowBounds.FromNodes`) |
| Full redraw | $O(N)$ — one rounded-rect thumb per cached node, each $O(1)$ after the $O(1)$ fit/scale projection; plus one viewport-indicator rect |
| Fit transform | $O(1)$ — `MinimapFit` = uniform `min(drawW/cw, drawH/ch)` |
| Viewport-indicator drag → scroll | $O(1)$ — `MinimapToWorld` + `MinimapToScroll`, then clamped scroll |

The minimap intentionally thumbnails the *whole* graph ($O(N)$), not just the visible region — that is what makes it a navigational overview.

## Summary

The adapter keeps interactive cost proportional to what is on screen: virtualization limits rendered views to $V$, the view pool bounds allocation to a small batch per frame, and panning is $O(1)$ per input event. The two model-wide costs are zoom ($O(N)$ collapse notifications + an $O(N)$ cover check per gesture) and the minimap ($O(N)$ redraw), both constant-factor per node and only triggered by the operations that actually change every node or the whole-graph overview.
