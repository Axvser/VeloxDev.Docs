# Avalonia Adapter

Avalonia closes the same role set as WPF but caches the hit-test curve. The link view still builds a `StreamGeometry`, a brush and a pen per paint, yet the 128-sample curve is refreshed only when an endpoint or the data context changes. The surface transform also performs far fewer forced layout passes.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | nodes |
| $v$ | realized link views |
| $p$ | curve samples (128) |
| $r$ | visible grid lines and ticks |
| $L$ | layout-tree size |

## Link view: cached curve, rebuilt geometry

`RefreshGeometry` rebuilds `LinkCurve.BuildLinkCubic` only from `OnPropertyChanged`; `Render` then allocates the geometry, brush and pen (`Src/Templates/VeloxDev.Avalonia.Templates/working/content/workflow-link-view/TemplateClass.axaml.cs:125-169`).

```csharp
private void RefreshGeometry()
{
    var link = DataContext as ILinkComponent;
    _curve = LinkCurve.BuildLinkCubic(link, StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
    link?.PublishCurve(_curve, this);
}

public override void Render(DrawingContext context)
{
    ...
    var brush = new ImmutableSolidColorBrush(LineColor);
    var pen = IsVirtualLink ? new Pen(brush, LineThickness) { DashStyle = new DashStyle([4.0, 2.0], 0) } : new Pen(brush, LineThickness);
    var geometry = BuildCurve(DataContext as ILinkComponent);
    context.DrawGeometry(null, pen, geometry);
}
```

A paint therefore costs

$$
T_{\text{frame}} = O(v) + O(\text{geometry size})
$$

rather than $O(v \cdot p)$: the sample table is reused across frames. The difference matters when endpoints move every frame (a drag) and when they do not (a static zoom).

```plot
{
  "title": "Sampling work per frame",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 13000] },
  "data": [
    { "fn": "128*x", "color": "#f472b6", "title": "rebuild curve per link" },
    { "fn": "x", "color": "#4a9eff", "title": "cached curve" }
  ]
}
```

## Minimap

`DrawMinimap` fills one rectangle per mapped node and caches the viewport pen by brush reference (`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:424-492`).

```csharp
if (NodeBrush is not null)
{
    var ncr = (float)Math.Max(0, context.NodeCornerRadius);
    foreach (var node in context.MappedNodes)
    {
        drawingContext.FillRectangle(NodeBrush,
            new Rect(offsetX + node.Left, offsetY + node.Top, node.Width, node.Height), ncr);
    }
}
```

Submit is $O(n)$ per paint with no per-node allocation; mapping is dirty-gated. Pen lookup is $O(1)$ after the first use (`:483-491`).

## Surface transform

The pivot/overscroll math is the same as WPF, but the adapter forces layout at five call sites instead of sixteen (`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:110-147`). On the common pan path it writes the scroll offset and updates the region; layout is flushed only when the layout actually changed.

$$
T_{\text{pan}} = O(1) + \begin{cases} 0 & \text{no layout change} \\ O(L) & \text{layout flushed} \end{cases}
$$

## Pool and hit test

The pool policy uses a batch of 1024 with a 16 ms budget and unlimited recycling per type (`Src/Adapters/VeloxDev.Avalonia/WorkflowSystem/ViewHosting/ViewPoolPolicy.cs:10-19`). A burst of $v$ views is realized in $\lceil v/1024 \rceil$ dispatcher turns rather than $\lceil v/3 \rceil$; total work remains $O(v)$.

Hit testing is the Core path: $O(d + v(1+p))$ per pointer move, with the cached curve making the per-link walk allocation-free.

## Grid

The generated grid decorator redraws visible lines and tick labels per render, $O(r)$, sharing frozen static pens. As in WPF, the cost scales with the visible ruler window, not with graph size.

## Caching summary

- Hit-test curve cached across paints.
- Pen cached by brush reference and thickness.
- Minimap mapping dirty-gated.
- Pool batches large bursts.
- The drawn `StreamGeometry` is still rebuilt per paint.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [WPF Adapter](../25_wpf-adapter/index.md) — the same role set without a cached curve.
