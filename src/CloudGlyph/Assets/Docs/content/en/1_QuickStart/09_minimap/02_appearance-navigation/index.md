# Appearance and navigation

The overlay exposes plain dependency properties; a host styles it from XAML or subclasses it to change the drawing. Navigation needs no code: the pipeline turns a press and a drag into scroll offsets through the adapter's viewport layer.

## Size and placement

| Property | Default | Meaning |
|---|---:|---|
| `MinimapWidth` / `MinimapHeight` | 200 / 140 | Requested size before the free corner clamps it. |
| `MinimapMinSize` | 20 | Smallest width or height the minimap may shrink to. |
| `MinimapMargin` | 12 | Gap from the available corner. |
| `ContentPadding` | 2 | Inner padding around the mapped content. |
| `MinimapCornerRadius` | 4 | Frame corner radius. |
| `NodeCornerRadius` | 1 | Thumbnail corner radius. |
| `IsMinimapVisible` | `true` | When `false`, a render pass draws nothing. |

The position is not a property: the pipeline computes the rectangle from `AvailableRight` / `AvailableTop` / `AvailableBottom`, which the surface pushes. Setting `MinimapMargin` on the overlay therefore also changes the gap the surface reserves.

## Brushes

| Property | Default role |
|---|---|
| `MinimapBackground` | Semi-transparent panel behind the map. |
| `MinimapBorderBrush`, `MinimapBorderThickness` | Frame outline. |
| `NodeBrush` | Node thumbnails. |
| `ViewportFill`, `ViewportStroke`, `ViewportStrokeThickness` | The viewport indicator and its outline. |

`LinkBrush` and `LinkStrokeThickness` are declared on the overlay, but the default `DrawMinimap` does not paint links: `MinimapDrawContext` carries node and viewport rectangles only. A subclass that wants links computes them from `context.Tree` and draws them itself.

## Toggle visibility

```xml
<CheckBox Content="Show minimap"
          IsChecked="{Binding IsMinimapVisible, ElementName=PART_MinimapOverlay}" />
```

`IsMinimapVisible` is a normal dependency property, so element binding or a view-model property both work.

## Drag to navigate

A press inside the minimap rectangle:

1. refreshes the cached mapping,
2. converts the pressed point from minimap-local to canvas-local through `WorkflowSurfaceMath.MinimapToCanvasLocal`,
3. converts that to a scroll offset through `WorkflowSurfaceMath.MinimapToScroll`,
4. writes the offset through the adapter's `IMinimapViewportHost`.

While the button stays down, every move repeats steps 2–4, so the viewport follows the pointer. Releasing ends the drag. The press is hit-tested against the placed minimap rectangle, not against the viewport indicator, so clicking any point in the map jumps there.

The drag math is Core; the adapter supplies three methods — current scroll offsets, viewport size, and apply-offset.

## Custom drawing

```csharp
public sealed class BrandMinimap : WorkflowMinimapOverlay
{
    public BrandMinimap()
    {
        MinimapBackground = new SolidColorBrush(Color.FromArgb(0xD2, 0x1F, 0x1F, 0x1F));
        NodeBrush = new SolidColorBrush(Color.FromArgb(0xDC, 0x6E, 0x8B, 0xFF));
        ViewportStroke = Brushes.White;
    }

    protected override void DrawMinimap(DrawingContext dc, MinimapDrawContext context)
    {
        base.DrawMinimap(dc, context);
        // context.MappedNodes / context.MappedViewport are minimap-local and already padded.
    }
}
```

Override and call `base` to add to the default drawing; replace it entirely to draw your own. `MinimapDrawContext` is recomputed at most once per rendered pass; do not cache it across passes.

## Expected result

- Changing `MinimapWidth` resizes the map and the mapping scale.
- Toggling `IsMinimapVisible` hides the map on the next render; the surface keeps running.
- Dragging inside the map pans the canvas continuously; the viewport rectangle follows the pointer.
- A subclass that sets only brushes changes colours without touching the mapping.

## Next

[Verification](../03_verification/index.md) shows the overlay in a host and holds the complete code.
