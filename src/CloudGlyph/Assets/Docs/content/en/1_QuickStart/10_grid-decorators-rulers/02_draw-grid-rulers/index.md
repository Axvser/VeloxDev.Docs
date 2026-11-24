# Draw grid and rulers

A decorator draws two layers. The bottom layer fills the surface and paints the full-viewport grid; the content (the scroll viewer and canvas) is a child between the layers; the top layer paints the translucent ruler bands and their ticks. Painting grid lines without the offsets looks correct only until the first pan.

## The four formulas

All grid arithmetic lives in `WorkflowSurfaceMath`. Use it rather than re-deriving the subtraction per decorator.

| Call | Formula | Use |
|---|---|---|
| `GridCanvasLeft(scrollOffset, contentOffset)` | `scroll − content` | Left edge of the visible canvas-local region. |
| `GridCanvasTop(scrollOffset, contentOffset)` | `scroll − content` | Top edge of the visible canvas-local region. |
| `GridFirstLine(localLeft, spacing)` | `⌊localLeft / spacing⌋ · spacing` | First grid line at or below the visible edge. |
| `GridX(localValue, localLeft, contentRectX)` | `contentRectX + (localValue − localLeft)` | Canvas-local value to an x in the decorator. |
| `GridY(localValue, localTop, contentRectY)` | `contentRectY + (localValue − localTop)` | Canvas-local value to a y in the decorator. |

`contentRectX` is the ruler thickness for the floating-band model: the grid starts after the band on the left, and after the band at the top.

## Draw the grid

```csharp
protected override void OnRender(DrawingContext context)
{
    var bounds = new Rect(RenderSize);
    if (bounds.Width <= 0 || bounds.Height <= 0) return;

    context.DrawRectangle(SurfaceBackgroundBrush, null, bounds);

    var ruler = Math.Max(0, owner.RulerThickness);
    var spacing = Math.Max(8, owner.GridSpacing);
    var majorStep = spacing * Math.Max(1, owner.MajorLineEvery);

    var worldLeft = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
    var worldTop = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);
    var worldRight = worldLeft + bounds.Width;
    var worldBottom = worldTop + bounds.Height;

    var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
    for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
    {
        var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
        var pen = IsNearZero(value) ? AxisPen
            : IsMajorLine(value, majorStep) ? MajorGridPen
            : MinorGridPen;
        context.DrawLine(pen, new Point(x, 0), new Point(x, bounds.Height));
    }

    var firstHorizontal = WorkflowSurfaceMath.GridFirstLine(worldTop, spacing);
    for (var value = firstHorizontal; value <= worldBottom + spacing; value += spacing)
    {
        var y = WorkflowSurfaceMath.GridY(value, worldTop, ruler);
        var pen = IsNearZero(value) ? AxisPen
            : IsMajorLine(value, majorStep) ? MajorGridPen
            : MinorGridPen;
        context.DrawLine(pen, new Point(0, y), new Point(bounds.Width, y));
    }
}
```

`IsMajorLine(value, majorStep)` compares `value % majorStep` against `0` and `±majorStep` with an epsilon (`0.001`). A direct `== 0` comparison misses every line after the first due to floating-point accumulation.

## Draw the rulers

The top layer paints two bands and, for every grid line that crosses the visible region, a tick. Major lines get a longer tick and a label.

```csharp
var ruler = Math.Max(0, owner.RulerThickness);
context.DrawRectangle(RulerBackgroundBrush, null, new Rect(0, 0, bounds.Width, ruler));
context.DrawRectangle(RulerBackgroundBrush, null, new Rect(0, 0, ruler, bounds.Height));

context.DrawLine(DividerPen, new Point(ruler, 0), new Point(ruler, bounds.Height));
context.DrawLine(DividerPen, new Point(0, ruler), new Point(bounds.Width, ruler));

var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    if (x < ruler) continue;                       // skip the corner where the bands overlap

    var isMajor = IsMajorLine(value, majorStep);
    var tickLength = isMajor ? ruler - 6 : Math.Max(6, ruler * 0.35);
    context.DrawLine(TickPen, new Point(x, ruler), new Point(x, ruler - tickLength));

    if (isMajor)
    {
        DrawLabel(context, value, new Point(x + 3, 2));
    }
}
```

The left ruler mirrors the same steps with `GridY` and `GridFirstLine(worldTop, spacing)`.

## Layers and invalidation

- The grid layer is below the content; its `IsHitTestVisible` is `false`.
- The ruler layer is above the content; it is also `IsHitTestVisible = false`, so clicks reach the canvas underneath.
- The decorator has no background of its own; the bottom layer paints the surface colour.
- Invalidate both layers when any offset, `RulerThickness`, `GridSpacing` or `MajorLineEvery` changes, and on `SizeChanged`. Without a `SizeChanged` invalidation the first layout paints nothing.

## Expected result

- Minor lines every `GridSpacing` (40 by default), major lines every `MajorLineEvery × GridSpacing` (200 by default).
- The origin lines are brighter than the rest.
- Ruler labels show the grid coordinate, not the screen coordinate.
- Panning moves the lines by exactly the scroll delta; zooming does not change the grid's pixel spacing.
- Clicking through a ruler hits the canvas, not the ruler.

## Next

[Verification](../03_verification/index.md) has a complete decorator and the host markup.
