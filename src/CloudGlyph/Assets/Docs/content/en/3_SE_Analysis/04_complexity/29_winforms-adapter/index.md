# WinForms Adapter

WinForms is the only adapter with no forced layout: scrolling is delegated to Easel's external scroll model, so a pan is a scroll request rather than a layout flush. Drawing is GDI+ and immediate per link, and the distinctive optimisation is that a link exposes its own damage rectangle, so a repaint is clipped to the old-and-new curve union instead of the whole surface.

## Cost model

| Symbol | Meaning |
|---|---|
| $v$ | realized link views |
| $p$ | curve samples (128) |
| $r$ | visible grid lines and ticks |
| $n$ | nodes |
| $A$ | damaged area |
| $L$ | layout-tree size |

## Link rendering

The generated link view computes control points, records its invalidation bounds, builds a 128-sample curve, publishes it, then allocates a `GraphicsPath` and a `Pen` per render (`Src/Templates/VeloxDev.WinForms.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:160-185`).

```csharp
protected override void OnRender(Graphics graphics)
{
    if (!CanRender || DataContext is not ILinkComponent link || !link.IsRenderReady())
    {
        return;
    }

    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, MinimumPull);
    var drawnMinX = points.Min(point => point.X);
    var drawnMinY = points.Min(point => point.Y);
    var drawnMaxX = points.Max(point => point.X);
    var drawnMaxY = points.Max(point => point.Y);
    _lastInvalidationBounds = RectangleF.FromLTRB((float)drawnMinX, (float)drawnMinY, (float)drawnMaxX, (float)drawnMaxY);
    _lastInvalidationBounds.Inflate(12f, 12f);

    var curve = LinkCurve.FromCubic(
        points[0].X, points[0].Y, points[1].X, points[1].Y,
        points[2].X, points[2].Y, points[3].X, points[3].Y);
    link.PublishCurve(curve, this);

    using var path = new GraphicsPath();
    path.AddBezier(
        (float)points[0].X, (float)points[0].Y,
        (float)points[1].X, (float)points[1].Y,
        (float)points[2].X, (float)points[2].Y,
        (float)points[3].X, (float)points[3].Y);
```

Per visible link the render is $O(p)$ plus two GDI+ objects. The curve is sampled twice — once for the invalidation box and once for hit testing — so the constant is larger than "one sample pass".

## Damage-based repaint

`GetInvalidationBounds` unions the previous damage rectangle with the new one, so a partial repaint cannot leave the old segment stale (`TemplateClass.xaml.cs:136-144`).

```csharp
// A partial repaint clipped to the NEW curve leaves the previous segment stale ...
if (_lastInvalidationBounds.Width > 0f && _lastInvalidationBounds.Height > 0f)
{
    bounds = RectangleF.Union(bounds, _lastInvalidationBounds);
}
return bounds;
```

The paint cost is therefore

$$
T_{\text{repaint}} = O(A)
$$

where $A$ is the damaged area, instead of $O(\text{surface})$. The link opts out of Easel's damage cull with `UnboundedHitTest = true`, so it is always considered for a paint even when its cached bounds look cold.

## Minimap

`DrawMinimap` allocates one `SolidBrush` for nodes and one `Pen` for the viewport, sets a clip, then fills one rectangle per mapped node (`Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:251-294`). Submit is $O(n)$ per paint with a constant number of GDI+ objects, not one per node.

## Grid

The generated grid decorator allocates three pens and a background brush per render, then draws $O(r)$ lines; the ruler pass adds tick pens and a `DrawString` per major label (`Src/Templates/VeloxDev.WinForms.Templates/working/content/workflow-grid-decorator/TemplateClass.cs:283-300`). Unlike the minimap, these pens are not cached across frames, so a continuous pan pays the allocation per paint.

## Surface and scroll

The surface behavior contains no `UpdateLayout` call; scroll is delegated to `VisualScrollViewer` through `IsExternalScroll` and `ScrollOffsetRequested` (`Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:495`, `:526-539`).

$$
T_{\text{pan}} = O(1)
$$

plus Easel's own invalidation. The one superlinear structural cost is z-order insertion: attaching a newly created view scans the existing children before inserting (`ViewContainer.cs:126-149`), so materialising a large first frame is $O(v^2)$ in the worst case.

## Caching summary

- Damage rectangle union keeps repaint proportional to the changed area.
- Minimap shares one node brush and one viewport pen.
- External scroll avoids layout passes entirely.
- Link geometry and pens are not cached across renders.
- Grid pens are reallocated per paint.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [WinUI Adapter](../27_winui-adapter/index.md) — the retained-element alternative.
