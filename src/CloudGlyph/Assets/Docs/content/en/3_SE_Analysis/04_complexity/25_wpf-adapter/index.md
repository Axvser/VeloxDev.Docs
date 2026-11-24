# WPF Adapter

WPF draws one view per link and an immediate-mode minimap. The recurring cost is the link view's `OnRender`, which rebuilds the sampled curve, the geometry, the brush and the pen on every invalidated frame. The dominant input cost is not drawing but forced layout: a pan or zoom that crosses the scroll limit flushes layout three times.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | nodes |
| $m$ | links |
| $v$ | realized link views (visible links) |
| $p$ | curve samples per link (128) |
| $r$ | visible grid lines and ruler ticks |
| $L$ | layout-tree size |

## Per-frame link drawing

The generated link view publishes a hit-test curve and then builds a `PathGeometry`, a `SolidColorBrush` and a `Pen` for every render (`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:85-104`).

```csharp
protected override void OnRender(DrawingContext ctx)
{
    base.OnRender(ctx);
    if (!CanRender) return;
    if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

    // Publish the curve the surface hit-tests against: same control points as BuildCurve, same
    // canvas-local space. Replace this together with BuildCurve if you change the shape.
    PublishCurve(LinkCurve.BuildLinkCubic(DataContext as ILinkComponent, StartLeft, StartTop, EndLeft, EndTop, MinimumPull));

    var thickness = LineThickness;
    var geometry = BuildCurve(DataContext as ILinkComponent);

    var brush = new SolidColorBrush(LineColor);
    var pen = IsVirtualLink
        ? new Pen(brush, thickness) { DashStyle = new DashStyle(new double[] { 4, 2 }, 0) }
        : new Pen(brush, thickness);

    ctx.DrawGeometry(null, pen, geometry);
}
```

`LinkCurve` samples 128 points by default (`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:26`), so a frame with $v$ invalidated links costs

$$
T_{\text{frame}} = O(v \cdot p) + O(v) \text{ allocations}
$$

and the geometry is discarded on the next render despite being frozen. This is the most expensive per-frame path in the adapter; the pool itself is not the issue.

## Minimap

`WorkflowMinimapOverlay.OnRender` maps all nodes, not only visible ones, and submits one rounded rectangle per mapped node (`Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:398-425`).

```csharp
protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context)
{
    var bounds = context.GetMinimapRect(MinimapMinSize);
    var mmRect = new Rect(bounds.Left, bounds.Top, bounds.Width, bounds.Height);
    var offsetX = mmRect.Left;
    var offsetY = mmRect.Top;
    var cr = Math.Max(0, context.MinimapCornerRadius);

    // 缩略图背景
    if (MinimapBackground is not null)
        dc.DrawRoundedRectangle(MinimapBackground, null, mmRect, cr, cr);
    if (MinimapBorderBrush is not null)
        dc.DrawRoundedRectangle(null, GetPen(ref _borderPen, MinimapBorderBrush, MinimapBorderThickness), mmRect, cr, cr);

    if (_clipGeometry is null || _clipGeometry.Rect != mmRect)
        _clipGeometry = new RectangleGeometry(mmRect);
    dc.PushClip(_clipGeometry);
    try
    {
        // 节点
        if (NodeBrush is not null)
        {
            var ncr = Math.Max(0, context.NodeCornerRadius);
            foreach (var node in context.MappedNodes)
            {
                dc.DrawRoundedRectangle(NodeBrush, null,
                    new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr, ncr);
            }
        }
```

Submit is $O(n)$ per paint; the mapping is recomputed only when the pipeline is dirty. Pen and clip geometry are cached (`:372-383`), so the allocation cost is bounded.

## Surface transform

Zoom and pan apply a world transform, then, when the offset meets the scroll limit, flush layout before reading the new maxima (`Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:1260-1269`).

```csharp
if (layoutChanged)
{
    ApplyLayout(host, state);
    state.Canvas?.UpdateLayout();
    state.ScrollViewer.UpdateLayout();
    host.UpdateLayout();
    maxH = GetHorizontalScrollMaximum(state.ScrollViewer);
    maxV = GetVerticalScrollMaximum(state.ScrollViewer);
```

$$
T_{\text{pan}} = \begin{cases} O(1) & \text{clamped} \\ O(L) & \text{layout flushed} \end{cases}
$$

The file contains sixteen `UpdateLayout`/`Measure`/`Arrange` call sites; the three-pass flush is the input path that users feel on an overscroll.

## Hit testing and drag

`ResolveTarget` walks the visual ancestor chain, then delegates to the Core link hit test over `VisibleItems` (`WorkflowSurfaceBehavior.cs:1035-1055`; `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:76-93`). Each link's `Contains` rejects by bounding box first and then walks segments (`LinkCurve.cs:318-336`).

$$
T_{\text{hit}} = O(d + v(1 + p))
$$

with the bounding-box rejection making the common case $O(d + v)$. Node drag resolves the node by ancestor walk per move, $O(d)$.

## Pool and grid

The view pool batches materialization under an 8-16 ms frame budget, and the template lookup is cached by runtime type (`Src/Adapters/VeloxDev.WPF/WorkflowSystem/ViewHosting/ViewFactory.cs:42-78`). The arranger is a no-op. The generated grid decorator redraws every visible line and ruler tick per render, $O(r)$, with one `FormattedText` allocation per major label.

## Caching

- Minimap pen and clip geometry are reused.
- Static grid pens are frozen (`TemplateClass.cs` in the grid template).
- Templates are cached per runtime type.
- The link geometry is frozen, but only after being rebuilt; nothing carries it across frames.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [Avalonia Adapter](../26_avalonia-adapter/index.md) — the same role set with a cached hit-test curve.
