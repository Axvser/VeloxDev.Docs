# WinUI Adapter

WinUI pays for retained UI elements more than for drawing. The minimap keeps one `Rectangle` per node in the visual tree, and the view arranger subscribes a property handler per realized view. Both scale with item count; per-frame drawing itself is cheap because the link geometry is mutated in place.

## Cost model

| Symbol | Meaning |
|---|---|
| $n$ | nodes |
| $v$ | realized views (nodes and links) |
| $p$ | curve samples (128) |
| $L$ | layout-tree size |
| $h$ | dispatcher hops per layout burst |

## Per-item layout tracking

`ViewLayoutTracker` subscribes to each view's item property changes and re-arranges on `Anchor`, `Size`, sender/receiver or slot changes (`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/ViewHosting/ViewLayoutTracker.cs:28-53`).

```csharp
PropertyChangedEventHandler handler = (_, e) =>
{
    if (!IsLayoutProperty(e.PropertyName)) return;
    var dispatcher = view.DispatcherQueue;
    if (dispatcher is null || dispatcher.HasThreadAccess) { arrange(view, item); return; }
    dispatcher.TryEnqueue(DispatcherQueuePriority.Low, () =>
    {
        if (_entries.TryGetValue(view, out var current) && ReferenceEquals(current.Source, item))
            arrange(view, item);
    });
};
notify.PropertyChanged += handler;
_entries[view] = new Entry(notify, handler);
```

$$
T_{\text{track}} = O(1) \text{ per change} + O(h) \text{ dispatcher hops}, \qquad S = O(v)
$$

The entry dictionary is an index, so unsubscribe is $O(1)$; the cost is the retained handler and the hop, not a scan. A batch of layout writes can therefore cost one hop per changed view, though the rebinding check drops hops for views that have since been recycled.

## Link view: mutated geometry

The generated link view caches `Path`, `PathGeometry`, `PathFigure` and `BezierSegment` and mutates the segment points rather than allocating (`Src/Templates/VeloxDev.WinUI.Templates/working/content/workflow-link-view/TemplateClass.xaml.cs:295-311`).

```csharp
_path.Data = _pathGeometry;
...
private void BuildCurve(double ox, double oy)
{
    var link = DataContext as ILinkComponent;
    var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, 40);
    _pathFigure.StartPoint = new Point(points[0].X + ox, points[0].Y + oy);
    _segment.Point1 = new Point(points[1].X + ox, points[1].Y + oy);
    ...
    _curve = LinkCurve.BuildLinkCubic(link, StartLeft, StartTop, EndLeft, EndTop, 40);
    PublishCurve();
}
```

The curve is still rebuilt on each update, $O(p)$ per changed link, but no `PathGeometry` object is created. Endpoint property changes redraw synchronously so the link cannot lag one frame; layout-driven updates are coalesced at normal dispatcher priority.

## Minimap: one element per node

The minimap uses pooled `Rectangle` children instead of immediate drawing. It grows the pool to the node count and hides surplus rectangles (`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs:527-551`).

```csharp
while (_nodeRects.Count < context.MappedNodes.Count)
{
    var rect = new Rectangle();
    _nodeRects.Add(rect);
    Children.Add(rect);
}
for (int i = 0; i < _nodeRects.Count; i++)
{
    var rect = _nodeRects[i];
    if (i < context.MappedNodes.Count)
    {
        var node = context.MappedNodes[i];
        SetLeft(rect, offsetX + node.Left); SetTop(rect, offsetY + node.Top);
        rect.Width = node.Width; rect.Height = node.Height;
        rect.Fill = NodeBrush; rect.Visibility = Visibility.Visible;
```

Per paint the cost is $O(n)$ property writes; the retained tree also holds $O(n)$ elements even when hidden. That is a heavier per-node steady-state than an immediate-mode minimap, traded for cheaper invalidation.

## Surface transform

Overscroll and zoom use the same three-pass layout flush as WPF (`Src/Adapters/VeloxDev.WinUI/WorkflowSystem/AttachedBehaviors/WorkflowSurfaceBehavior.cs:772-793`, `:884-888`). The per-input cost is $O(L)$ when the flush runs and $O(1)$ otherwise.

## Caching

- Geometry objects are reused and mutated, not reallocated.
- Layout updates are coalesced through the dispatcher.
- Minimap rectangles are pooled and only hidden.
- `LayoutUpdated` is used for slot measurement rather than polling.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the shared structures this adapter consumes.
- [WinForms Adapter](../29_winforms-adapter/index.md) — the opposite choice: immediate-mode drawing with damage rectangles.
