# Minimap math

The fit, local mapping, viewport rectangle, and drag conversion are static functions on `WorkflowSurfaceMath`. They are shared by every adapter's renderer and by the pipeline, so a custom overlay computes the same geometry as the default one.

`WorkflowBounds`, the rectangle type these functions return, is documented with [Surface math](../../07_canvas-input-navigation/03_surface-math/index.md).

## WorkflowSurfaceMath (minimap members)

```csharp
public static class WorkflowSurfaceMath
```

### Fit

| Signature | Returns | Description |
|---|---|---|
| `MinimapFit(double contentWidth, double contentHeight, double drawWidth, double drawHeight, double padding)` | `(double OriginX, double OriginY, double Scale)` | Computes the uniform scale that fits the content into the padded draw area, and the origin that centres it. |

### Content to minimap

| Signature | Returns | Description |
|---|---|---|
| `MinimapLocal(double contentX, double contentY, double contentLeft, double contentTop, double originX, double originY, double scale)` | `(double LocalX, double LocalY)` | Maps a canvas-local point into minimap-local pixels. |
| `MinThumbSize(double size, double scale, double min)` | `double` | Raises a scaled thumbnail edge to at least `min`. |
| `MinimapViewportRect(double originX, double originY, double scale, double vpLeft, double vpTop, double vpWidth, double vpHeight, double contentLeft, double contentTop, double mmWidth, double mmHeight, double minRectSize)` | `(double X, double Y, double Width, double Height)` | Maps the viewport into the minimap and clamps the indicator inside the frame; its smallest edge is `minRectSize`. |

### Minimap to scroll

| Signature | Returns | Description |
|---|---|---|
| `MinimapToCanvasLocal(double mmX, double mmY, double originX, double originY, double scale, double contentLeft, double contentTop)` | `(double LocalX, double LocalY)` | The inverse of `MinimapLocal`. |
| `MinimapToScroll(double localX, double localY, double viewportWidth, double viewportHeight, double contentOffsetX, double contentOffsetY)` | `(double ScrollX, double ScrollY)` | Converts a canvas-local point into the scroll offset that centres it. |

## Pipeline use

| Step | Function |
|---|---|
| Fit the mapped content | `MinimapFit` with the draw area reduced by `Metrics.Padding`. |
| Node rectangles | `MinimapLocal`, then `MinThumbSize` with `Metrics.MinimumThumbSize`. |
| Viewport indicator | `MinimapViewportRect` with a minimum edge of 2 px. |
| Drag | `MinimapToCanvasLocal`, then `MinimapToScroll`, then the pipeline's scroll clamp and `IMinimapViewportHost.ApplyScroll`. |

## Notes

- The scale is uniform; a non-square draw area leaves margins rather than stretching the map.
- `MinimapViewportRect` clamps the indicator inside the frame, so a viewport larger than the content still shows a meaningful rectangle.
- `MinThumbSize` is what keeps a distant node from vanishing; it affects rendering, not hit testing.
