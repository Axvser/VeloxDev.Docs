# Surface math

`WorkflowSurfaceMath` is the one place scroll, zoom, and viewport arithmetic is written. `SurfaceMetrics` is the snapshot an adapter takes once per layout pass and pushes into the grid decorator, minimap, and tree.

## WorkflowSurfaceMath

```csharp
public static class WorkflowSurfaceMath
```

This page lists the navigation and viewport members. The same class also carries the grid functions ([Grid math](../../10_grid-decorators-rulers/01_grid-math/index.md)) and the minimap mapping functions ([Minimap math](../../09_minimap/02_minimap-math/index.md)).

### Constants

| Constant | Value | Meaning |
|---|---:|---|
| `DefaultPanExtendRatio` | `0.15` | Fraction the canvas grows by on overscroll. |

### Scroll and canvas conversion

| Signature | Returns | Description |
|---|---|---|
| `ToCanvasLocal(double scroll, double actualOffset)` | `double` | `scroll − actualOffset`. |
| `ToCanvasLocalAnchor(double scrollX, double scrollY, int layer, CanvasLayout layout)` | `Anchor` | Canvas-local anchor for a scroll position. |
| `ToScroll(double localX, double localY, CanvasLayout layout)` | `Offset` | Scroll position for a canvas-local point. |
| `ScrollMax(double extent, double viewport)` | `double` | Largest scrollable offset; floors at 0. |
| `ClampValue(double value, double min, double max)` | `double` | Inclusive clamp. |
| `ClampScrollOffset(double desired, double max, CanvasLayout layout, bool horizontal, double threshold = 0d, double extendRatio = 0d)` | `double` | Clamps to `[0, max]`; writes the overshoot into the layout's negative/positive offset and optionally grows the canvas. |
| `EnsureNegativeCover(ITreeComponent? tree)` | `bool` | Grows the negative offset when content crosses the origin; returns whether it grew. |

### Centring and zoom pivots

| Signature | Returns | Description |
|---|---|---|
| `CenterScroll(double localX, double localY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | `(double ScrollX, double ScrollY)` | Scroll that puts a canvas-local point at the viewport centre. |
| `ScrollCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight)` | `(double X, double Y)` | Canvas-local point currently at the viewport centre. |
| `WorldAtViewportCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | `(double WorldX, double WorldY)` | World point under the viewport centre. |
| `PivotCenterScroll(double pivotX, double pivotY, CanvasLayout layout, double viewportWidth, double viewportHeight)` | `(double X, double Y)` | Scroll that keeps a pivot under the viewport centre after a scale change. |
| `LayoutPivot(CanvasLayout layout)` | `Anchor` | The collapse pivot, or `(0,0,0)` in viewport-centre mode. |
| `ScaleCollapse(double anchorX, double anchorY, double scaleX, double scaleY)` | `(double ScaleX, double ScaleY, double CenterX, double CenterY)` | Collapse transform for an anchor. |
| `ScaleVisualBounds(double anchorX, double anchorY, double width, double height, double scaleX, double scaleY)` | `(double Left, double Top, double Width, double Height)` | Bounds after scaling around an anchor. |

### Slot anchor construction

| Signature | Returns | Description |
|---|---|---|
| `SlotAnchorFromVisualCenter(double centerX, double centerY, int layer, CanvasLayout layout)` | `Anchor` | Anchor from a visual centre in scroll space. |
| `SlotAnchorFromNode(double nodeX, double nodeY, double localX, double localY, int layer)` | `Anchor` | Anchor from a node origin plus a local offset. |
| `SlotAnchorFromCanvasLocal(double centerX, double centerY, int layer)` | `Anchor` | Anchor from a canvas-local centre. |

### Viewport restore

| Signature | Returns | Description |
|---|---|---|
| `HasViewportRestore(CanvasLayout layout)` | `bool` | Whether either `ViewportOffset` axis exceeds 0.5. |
| `ViewportRestoreScroll(CanvasLayout layout)` | `Offset` | The scroll to restore to. |
| `ViewportOffsetFromScroll(double scrollX, double scrollY, CanvasLayout layout)` | `Offset` | The `ViewportOffset` that reproduces a scroll. |

## WorkflowBounds

```csharp
public readonly struct WorkflowBounds
```

| Member | Type | Access | Description |
|---|---|---|---|
| `Left` / `Top` / `Width` / `Height` | `double` | get/init | Rectangle components. |
| `Right` | `double` | get | `Left + Width`. |
| `Bottom` | `double` | get | `Top + Height`. |
| `IsEmpty` | `bool` | get | `Width <= 0 || Height <= 0`. |

| Static method | Description |
|---|---|
| `FromNode(double x, double y, double w, double h)` | Builds a bounds from a node rectangle. |
| `FromNodes(IEnumerable<(double X, double Y, double W, double H)> rects)` | Union of many rectangles. |
| `Union(WorkflowBounds a, WorkflowBounds b)` | Union; an empty operand is ignored. |

`WorkflowBounds` declares no equality members and no operators. Compare its fields.

## SurfaceMetrics

```csharp
public readonly struct SurfaceMetrics
```

| Member | Type | Description |
|---|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Scroll-container offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Canvas `ActualOffset` components. |
| `ViewportWidth` / `ViewportHeight` | `double` | Visible viewport size. |
| `RulerBand` | `double` | Thickness of the ruler band overlapping the top/left edges. |
| `VerticalScrollBarThickness` / `HorizontalScrollBarThickness` | `double` | Scrollbar thickness; 0 when hidden. |
| `Available` | `SurfaceAvailableArea` | Free corner overlays may use. |

```csharp
public static SurfaceMetrics Create(
    double scrollOffsetX, double scrollOffsetY,
    double contentOffsetX, double contentOffsetY,
    double viewportWidth, double viewportHeight,
    double surfaceWidth, double surfaceHeight,
    double rulerBand,
    double verticalScrollBarThickness, double horizontalScrollBarThickness,
    double margin);
```

`Create` derives `Available` as `Right = max(0, surfaceWidth − verticalScrollBarThickness)`, `Top = max(0, rulerBand)`, `Bottom = max(0, surfaceHeight − horizontalScrollBarThickness)`, and `Margin = margin`.

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
```

| Member | Type | Description |
|---|---|---|
| `Right` / `Top` / `Bottom` / `Margin` | `double` | Edges and gap of the usable corner. |
| `IsUsable` | `bool` | `Right > 0 && Bottom > Top`. |

| Method | Description |
|---|---|
| `GetRect(double desiredWidth, double desiredHeight, double minimumSize)` | Places a box at the top-right of the corner, clamped to the free area and `max(1, minimumSize)`; falls back to `(0,0)` when unusable. |
| `Equals(SurfaceAvailableArea other)` | Value equality over the four doubles. |

## SurfaceMetricsPush

```csharp
public static class SurfaceMetricsPush
```

| Signature | Description |
|---|---|
| `PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree)` | Writes the four offsets, then sets the tree's virtualization inset to `decorator.RulerBand` on the left and top. Throws `ArgumentNullException` for a null decorator. |
| `PushMinimap(SurfaceMetrics metrics, IWorkflowMinimapOverlay minimap, ITreeComponent? tree)` | Writes offsets, viewport size, tree, corner edges, and margin. Throws `ArgumentNullException` for a null minimap. |
| `PushViewport(SurfaceMetrics metrics, ITreeComponent tree)` | Sets `tree.GetHelper().Viewport` and persists `tree.Layout.ViewportOffset`. Throws `ArgumentNullException` for a null tree. |

`PushViewport` is what turns a scroll into a virtualization pass. The grid and minimap pushes run after it in the same layout pass.

## ISurfaceMetricsSource

```csharp
public interface ISurfaceMetricsSource
{
    SurfaceMetrics ReadMetrics();
}
```

Implemented by an adapter that can produce the snapshot on demand. The surface behavior reads it once per layout/scroll pass.
