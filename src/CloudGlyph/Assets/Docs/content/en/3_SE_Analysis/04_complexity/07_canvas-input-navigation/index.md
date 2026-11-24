# Canvas input and navigation

Input routing is constant-time: a pointer event bubbles through at most three helpers (slot, node, tree). The cost sits in hit-testing. Link hit-testing has no spatial index — it walks the realized visible items, tests each link against a 128-segment polyline, and for a hit rescans the visible items to check node occlusion. Slot hit-testing walks the whole model.

Notation: $L$ realized links, $S$ curve samples (128 by default), $N$ visible nodes, $P$ total slots in the tree.

## Cost model

| Operation | Time | Source |
|---|---|---|
| Route a pointer event | $O(1)$ — chain length at most 3 | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:267` |
| Bubble to handlers | $O(1)$ helpers, subscriber cost | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:324` |
| Build a link curve | $O(S)$ time and memory | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:286` |
| Curve containment | $O(1)$ box reject, then $O(S)$ worst | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:318` |
| Point at arc length | $O(\log S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:342` |
| Link hit-test, all visible | $O(L S + L N)$ worst | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:76` |
| Slot hit-test | $O(P)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/SlotHitTestEx.cs:29` |
| Wheel scroll / center-on | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Surface/SurfaceScrollerCore.cs:49` |
| Negative-cover sweep | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:454` |

## Routing is a three-step chain

`Chain` yields the slot helper, then the owning node helper, then the tree helper; `Bubble` stops when a handler sets `StopPropagation`:

```csharp
foreach (var helper in Chain(e.Target))
{
    if (helper is not IInputEvents events) continue;
    events.Input.Raise(e);
    if (e.Handle.StopPropagation) break;
}
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:324-331`

The chain is fixed at no more than three entries, so routing is $O(1)$ regardless of graph size.

## Link hit-testing is the expensive path

The hit-test scans visible links from the topmost down, samples each curve, and then checks whether a node covers the hit point:

```csharp
for (var i = items.Count - 1; i >= 0; i--)
{
    if (items[i] is not ILinkComponent link) continue;
    if (!link.HitTest(x, y, radius)) continue;
    if (IsCoveredByANode(items, link, x, y, radius)) continue;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:83-88`

`HitTest` itself does a bounding-box reject first, then walks the samples:

```csharp
for (var i = 1; i < _xs.Length; i++)
    if (DistanceToSegment(x, y, _xs[i - 1], _ys[i - 1], _xs[i], _ys[i]) <= radius)
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:327-329`

The occlusion check is a second linear scan of the same visible list, so the worst case per pointer move is:

$$
T_{\text{hit}} = O(L\,S + L\,N)
$$

```plot
{
  "title": "Link hit-test per pointer move",
  "grid": true,
  "xAxis": { "domain": [0, 40] },
  "yAxis": { "domain": [0, 5200] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(L), one comparison per link" },
    { "fn": "128*x", "color": "#f472b6", "title": "O(L*S), 128 samples per link" }
  ]
}
```

Because $L$ is the *realized* link count from virtualization, the practical cost scales with the viewport, not the document. On a dense viewport, though, it is still a per-move linear sweep with a 128-sample constant.

## Curves, scrolling and the rest

`PointAtLength` uses a precomputed cumulative-length array and binary search, so sampling a position along a curve is $O(\log S)$ — the only logarithmic operation in the input path. Wheel scrolling and center-on are arithmetic on the current layout, $O(1)$, with at most one canvas expansion. The negative-cover sweep walks every node to extend the canvas for negative coordinates, $O(n)$, but only when the layout asks for it.

## Memory

`WorkflowInput` holds a fixed set of fields per tree, created lazily via a `ConditionalWeakTable`. A curve owns three `double[]` arrays of length $S$ plus its length and bounds — $O(S)$ per curve, published by reference, so the hit-test path allocates nothing per move. Adapter-side drag handlers issue one `MoveCommand` per mouse move; the downstream reindex and virtualization cost belongs to view hosting, not to input.
