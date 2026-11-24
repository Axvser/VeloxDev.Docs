# MAUI Adapter

MAUI draws every visible link in a single `GraphicsView`. There is no per-link view: one drawable enumerates the visible set, rebuilds each curve into a reused point array, culls by bounding box, and strokes the body several times. Flow animation adds a second, much larger term: the comet samples the curve once per tail segment per pass.

## Cost model

| Symbol | Meaning |
|---|---|
| $v$ | visible links |
| $p$ | curve samples (128) |
| $k$ | comet tail segments (16) |
| $r$ | visible grid cells |
| $n$ | nodes |
| bytes | media/payload size |

## Single-pass link drawing

`LinkOverlayDrawable.Draw` enumerates only the Core `VisibleItems`, so the loop is over $v$, not all $m$ links (`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/AttachedBehaviors/WorkflowLinkOverlay.cs:1583-1654`).

```csharp
foreach (var link in EnumerateVisibleLinks(tree))
{
    // 这条线已经有自己的视图在画（视图发布曲线时把「画它的那个控件」一并交了上来）——
    // 这层只画没人画的：立即模式的主机，以及池化视图还没物化出来的那几帧
    if (link.HitTarget()?.Visual is not null)
    {
        continue;
    }

    if (!TryGetEndpoints(link, out var csx, out var csy, out var cex, out var cey))
    {
        continue;
    }

    var isVirtual = IsVirtualLink(link);
    var color = isVirtual ? owner.VirtualColorFor(link, virtualColor) : linkColor;
    if (color is null)
    {
        continue;
    }

    var curve = LinkCurve.BuildLinkCubic(
        link, csx, csy, cex, cey, PullMinimum, LinkCurve.DefaultSampleCount);
    link.PublishCurve(curve);

    owner.BuildViewportGeometry(
        curve,
        ToViewport(ruler, ox, scrollX, 0),
        ToViewport(ruler, oy, scrollY, 0));
```

`BuildViewportGeometry` copies all 128 points into a reused `PointF[]` and mutates a reused `PathF` (`:363-394`); `IntersectsViewport` scans the same 128 samples for a bounding box (`:402-419`). Both are $O(p)$ per visible link.

$$
T_{\text{frame}} = O(v \cdot p)
$$

The body is stroked two to four times, and the argument colours are cached per alpha level, so the per-link allocation is bounded to the curve object.

## Flow comet

With flow enabled, `DrawComet` runs two passes over the tail, and each segment scans the sample table to place itself (`WorkflowLinkOverlay.cs:505-535`).

```csharp
for (var pass = 0; pass < 2; pass++)
{
    var bloom = pass == 0;
    for (var k = 0; k < TailSegments; k++)
    {
        var f0 = k / (float)TailSegments;
        var f1 = (k + 1) / (float)TailSegments;
        var l0 = head - (tail * (1 - f0));
        var l1 = head - (tail * (1 - f1));
        ...
        var segmentColor = Mix(color, Colors.White, f0);
        canvas.StrokeColor = bloom ? Fade(segmentColor, alpha * 0.22) : Fade(segmentColor, alpha);
        canvas.StrokeSize = bloom ? thickness + 9 : thickness * (0.45f + (0.95f * f0));
        StrokeSegment(canvas, l0, l1);   // scans all 128 samples
    }
}
```

With $k = 16$ segments and 2 passes, one flowing link costs about 4096 sample operations per frame, $(2 \cdot 16 \cdot 128)$:

$$
T_{\text{flow}} = O(v \cdot k \cdot p)
$$

This is the dominant per-frame term when many links animate; the comet is the reason the adapter is not simply $O(v \cdot p)$.

```plot
{
  "title": "Comet sampling per flowing link",
  "grid": true,
  "xAxis": { "domain": [1, 32] },
  "yAxis": { "domain": [0, 9000] },
  "data": [
    { "fn": "2*128*x", "color": "#f472b6", "title": "2 passes x 128 samples" },
    { "fn": "128", "color": "#4a9eff", "title": "body only" }
  ]
}
```

## Invalidation

Every model or offset change calls `ScheduleInvalidate`, which coalesces to one flush on the next main-thread dispatch, plus one follow-up repaint for anchors written at the end of layout (`WorkflowLinkOverlay.cs:1473-1503`). A burst of changes costs $O(1)$ invalidations, not one per change.

## Minimap and grid

The minimap is immediate `ICanvas` drawing: one `FillRoundedRectangle` per mapped node per submit, $O(n)$, with no brush or pen allocation because colours are set directly on the canvas (`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:713-781`). The grid decorators use two `GraphicsView`s whose drawables loop visible cells, $O(r)$ per frame plus text per major tick.

## Arrangement

`ViewArranger` subscribes to each view's item and coalesces bounds writes to one per dispatcher turn (`Src/Adapters/VeloxDev.MAUI/WorkflowSystem/ViewHosting/ViewArranger.cs:168-189`). Subscriptions are $O(v)$; each change is $O(1)$ plus at most one hop.

## Caching summary

- Reused `PointF[128]` and `PathF`, mutated in place.
- Fade colours cached per source colour.
- Invalidations coalesced to roughly one per frame.
- Visible-set iteration avoids scanning all links.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [Razor Adapter](../30_razor-adapter/index.md) — the other single-layer link strategy, moved into JavaScript.
