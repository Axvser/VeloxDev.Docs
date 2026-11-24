# Grid math

A grid decorator draws two layers: the grid below the content and the rulers above it. Both must agree on where a canvas-local grid value lands in the decorator's pixels. The five functions below are the whole contract; use them instead of re-deriving the subtraction per decorator.

## WorkflowSurfaceMath (grid members)

```csharp
public static class WorkflowSurfaceMath
```

The class is shared with navigation and minimap code. Only the grid members are listed here; the rest are on [Surface math](../../07_canvas-input-navigation/03_surface-math/index.md) and [Minimap math](../../09_minimap/02_minimap-math/index.md).

### Formulas

| Signature | Returns | Formula | Use |
|---|---|---|---|
| `GridCanvasLeft(double scrollOffset, double contentOffset)` | `double` | `scroll − content` | Left edge of the visible canvas-local region. |
| `GridCanvasTop(double scrollOffset, double contentOffset)` | `double` | `scroll − content` | Top edge of the visible canvas-local region. |
| `GridFirstLine(double localLeft, double spacing)` | `double` | `⌊localLeft / spacing⌋ · spacing` | First grid line at or below the visible edge. |
| `GridX(double localValue, double localLeft, double contentRectX)` | `double` | `contentRectX + (localValue − localLeft)` | Canvas-local value to an x inside the decorator. |
| `GridY(double localValue, double localTop, double contentRectY)` | `double` | `contentRectY + (localValue − localTop)` | Canvas-local value to a y inside the decorator. |

`contentRectX` and `contentRectY` are the ruler thickness for the floating-band model: the grid starts after the band on the left and below it at the top.

### Parameters

| Parameter | Meaning |
|---|---|
| `scrollOffset` | The decorator's pushed scroll offset for the axis. |
| `contentOffset` | The pushed canvas content offset for the axis. |
| `localLeft` / `localTop` | The visible canvas-local edge returned by the first two functions. |
| `spacing` | Grid spacing in canvas units. |
| `localValue` | A canvas-local coordinate on the grid. |
| `contentRectX` / `contentRectY` | Origin of the content rectangle inside the decorator. |

## Drawing pass

The standard pass reads the offsets, computes the visible world rectangle, then walks from `GridFirstLine` upward by `spacing`:

```csharp
var worldLeft = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
var worldTop = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);

var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldLeft + bounds.Width + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    // draw at x
}
```

The horizontal pass mirrors this with `GridCanvasTop`, `GridFirstLine`, and `GridY`.

## Major-line test

`GridFirstLine` returns the first aligned value; deciding which lines are major is the decorator's job. Compare the remainder with an epsilon (0.001) rather than `== 0`:

```csharp
var remainder = value % majorStep;
var isMajor = Math.Abs(remainder) < 0.001
    || Math.Abs(remainder - majorStep) < 0.001
    || Math.Abs(remainder + majorStep) < 0.001;
```

Floating-point accumulation after the first line makes a direct zero comparison miss every later major line.

## Notes

- Core ships no numeric grid defaults; spacing, major interval, and band thickness belong to the decorator. The WPF template uses 40, 5, and 28.
- `GridFirstLine` does not clamp; the caller limits drawing to the visible rectangle.
- Panning changes `scrollOffset` and therefore the visible edges; zooming changes neither the grid spacing nor these formulas, which is why the grid keeps its pixel spacing while cards scale.
