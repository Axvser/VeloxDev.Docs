# Jalium Adapter

Jalium culls a child by its layout box before drawing, so a link view must move and size its own box onto the curve before it can render. That extra relocation is the adapter's distinctive cost: every refresh computes the curve bounds, writes four layout properties, and invalidates layout, on top of the usual sampled curve.

## Cost model

| Symbol | Meaning |
|---|---|
| $v$ | realized link views |
| $p$ | curve samples (128) |
| $q$ | control points of one link (4) |
| $n$ | nodes |
| $r$ | visible grid lines |
| $L$ | layout-tree size |

## Layout-box relocation

`WorkflowLinkBounds.Apply` scans the point list for min/max, expands by a padding, and writes `Canvas.Left`, `Canvas.Top`, `Width` and `Height` (`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowLinkBounds.cs:58-101`).

```csharp
foreach (var point in canvasLocalPoints)
{
    if (point.X < minX) minX = point.X;
    if (point.Y < minY) minY = point.Y;
    if (point.X > maxX) maxX = point.X;
    if (point.Y > maxY) maxY = point.Y;
}
var left = minX - BoxPad; var top = minY - BoxPad;
var right = maxX + BoxPad; var bottom = maxY + BoxPad;
originX = left; originY = top;
Canvas.SetLeft(view, left); Canvas.SetTop(view, top);
view.Width = Math.Max(1d, right - left);
view.Height = Math.Max(1d, bottom - top);
```

$$
T_{\text{relocate}} = O(q) + O(1) \text{ layout writes}
$$

The scan itself is trivial for four control points; the cost is that a box change invalidates layout for that view. The platform culls by box, so this step cannot be skipped even though the drawing already knows the curve.

## Link refresh

`Refresh` clears the point list, rebuilds it, applies the box and invalidates the visual; `ScheduleRefresh` coalesces at render dispatcher priority (`Src/Templates/VeloxDev.Jalium.Templates/working/content/workflow-link-view/TemplateClass.jalxaml.cs:230-260`).

```csharp
private void Refresh()
{
    _curve.Clear();
    _hasBounds = false;

    if (!CanRender || _link is not { } link || !link.IsVisible || !link.IsRenderReady())
    {
        InvalidateVisual();
        return;
    }

    // Bound values may be NaN before the slots are measured.
    if (double.IsNaN(StartLeft) || double.IsNaN(StartTop) || double.IsNaN(EndLeft) || double.IsNaN(EndTop))
    {
        InvalidateVisual();
        return;
    }

    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, MinimumPull);
    if (points.Length < 4)
    {
        InvalidateVisual();
        return;
    }

    // Size the box to all four control points; the endpoints alone clip the curve's bulge.
    foreach (var (x, y) in points)
    {
        _curve.Add(new Point(x, y));
    }

    _hasBounds = WorkflowLinkBounds.Apply(this, _curve, out _originX, out _originY);
    InvalidateVisual();
}
```

`OnRender` then builds a `PathGeometry`, a brush and a pen and publishes a 128-sample curve, so the per-frame cost is $O(p)$ per invalidated link plus allocations.

## Minimap

The minimap draws one rounded rectangle per mapped node and allocates a new `Pen` for the border and for the viewport on each pass, unlike WPF and Avalonia which cache them (`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:465-490`).

```csharp
dc.DrawRoundedRectangle(MinimapBackground, null, mmRect, cr, cr);
dc.DrawRoundedRectangle(MinimapBorderThickness > 0 ? new Pen(MinimapBorderBrush, MinimapBorderThickness) : null, ...);
foreach (var node in context.MappedNodes)
{
    dc.DrawRoundedRectangle(NodeBrush, null, new Rect(...), ncr, ncr);
}
...
if (ViewportStrokeThickness > 0)
    dc.DrawRectangle(ViewportFill, new Pen(ViewportStroke, ViewportStrokeThickness), ...);
```

Submit is $O(n)$ per paint with two extra pen allocations. Mapping is computed only when the pipeline is dirty.

## Surface transform

World displacement is published on the host as a `TranslateTransform` attached property; node and link templates bind it to their own `RenderTransform` (`Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:841-845`). Overscroll and zoom call `EnsureNegativeCover` and flush layout at thirteen call sites (`:658-702`, `:1414-1419`).

$$
T_{\text{pan}} = O(1) + \begin{cases} 0 & \text{no layout change} \\ O(L) & \text{layout flushed} \end{cases}
$$

## Caching summary

- `_refreshPending` coalesces refreshes at render priority.
- `_hasBounds` skips drawing until the box is known.
- Surface transform is a single attached-property write per frame.
- The 128-sample curve and the drawn geometry are rebuilt per refresh.
- Minimap pens are allocated per pass.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [WPF Adapter](../25_wpf-adapter/index.md) — a similar per-link view without box relocation.
