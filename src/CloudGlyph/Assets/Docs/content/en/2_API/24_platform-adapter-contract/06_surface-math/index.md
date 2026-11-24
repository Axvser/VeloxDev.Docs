# Surface math

`WorkflowSurfaceMath` is the coordinate and clamping arithmetic every adapter shares. Scroll offsets, canvas content offsets, canvas-local positions and viewport rectangles are converted here rather than once per platform.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## WorkflowSurfaceMath

**Signature:** `static class WorkflowSurfaceMath`

| Member | Signature | Description |
| --- | --- | --- |
| `DefaultPanExtendRatio` | `const double` (`0.15`) | Fraction of the viewport a pan grows the canvas when it overshoots. |
| `ToCanvasLocal` | `static double ToCanvasLocal(double scroll, double actualOffset)` | `local = scroll − contentOffset`. |
| `ToCanvasLocalAnchor` | `static Anchor ToCanvasLocalAnchor(double scrollX, double scrollY, int layer, CanvasLayout layout)` | Converts a scroll position to a canvas-local anchor. |
| `ToScroll` | `static Offset ToScroll(double localX, double localY, CanvasLayout layout)` | Converts a canvas-local point to a scroll offset. |
| `HasViewportRestore` | `static bool HasViewportRestore(CanvasLayout layout)` | Whether the layout carries a saved, non-zero viewport position. |
| `ViewportRestoreScroll` | `static Offset ViewportRestoreScroll(CanvasLayout layout)` | The saved scroll position to restore. |
| `ViewportOffsetFromScroll` | `static Offset ViewportOffsetFromScroll(double scrollX, double scrollY, CanvasLayout layout)` | Converts scroll offsets to the value persisted in `Layout.ViewportOffset`. |
| `ClampScrollOffset` | `static double ClampScrollOffset(double desired, double max, CanvasLayout layout, bool horizontal, double threshold = 0d, double extendRatio = 0d)` | Clamps an offset, growing the canvas on overshoot when the ratio allows. |
| `ScrollMax` | `static double ScrollMax(double extent, double viewport)` | The maximum offset for an extent and viewport. |
| `ClampValue` | `static double ClampValue(double value, double min, double max)` | Ordinary clamp. |
| `GridCanvasLeft` / `GridCanvasTop` | `static double GridCanvasLeft(double scrollOffset, double contentOffset)` / `static double GridCanvasTop(double scrollOffset, double contentOffset)` | Canvas origin for a grid layer. |
| `GridX` / `GridY` | `static double GridX(double localValue, double localLeft, double contentRectX)` / `static double GridY(double localValue, double localTop, double contentRectY)` | Grid line position. |
| `GridFirstLine` | `static double GridFirstLine(double localLeft, double spacing)` | First grid line at or after the visible edge. |
| `SlotAnchorFromVisualCenter` | `static Anchor SlotAnchorFromVisualCenter(double centerX, double centerY, int layer, CanvasLayout layout)` | Anchor from a visual centre. |
| `SlotAnchorFromNode` | `static Anchor SlotAnchorFromNode(double nodeX, double nodeY, double localX, double localY, int layer)` | Anchor from a node-local point. |
| `SlotAnchorFromCanvasLocal` | `static Anchor SlotAnchorFromCanvasLocal(double centerX, double centerY, int layer)` | Anchor from a canvas-local centre (no offset subtraction). |
| `MinimapFit` | `static (double OriginX, double OriginY, double Scale) MinimapFit(double contentWidth, double contentHeight, double drawWidth, double drawHeight, double padding)` | Fits the world bounds into the minimap. |
| `MinimapLocal` | `static (double LocalX, double LocalY) MinimapLocal(double contentX, double contentY, double contentLeft, double contentTop, double originX, double originY, double scale)` | World point → minimap-local point. |
| `MinimapViewportRect` | `static (double X, double Y, double Width, double Height) MinimapViewportRect(double originX, double originY, double scale, double vpLeft, double vpTop, double vpWidth, double vpHeight, double contentLeft, double contentTop, double mmWidth, double mmHeight, double minRectSize)` | The viewport frame in minimap pixels. |
| `MinimapToCanvasLocal` | `static (double LocalX, double LocalY) MinimapToCanvasLocal(double mmX, double mmY, double originX, double originY, double scale, double contentLeft, double contentTop)` | Minimap point → canvas-local point. |
| `MinimapToScroll` | `static (double ScrollX, double ScrollY) MinimapToScroll(double localX, double localY, double viewportWidth, double viewportHeight, double contentOffsetX, double contentOffsetY)` | Minimap point → scroll offsets. |
| `CenterScroll` | `static (double ScrollX, double ScrollY) CenterScroll(double localX, double localY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | Scroll offsets that centre a canvas-local point. |
| `ScrollCenter` | `static (double X, double Y) ScrollCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight)` | Canvas-local centre for a scroll position. |
| `WorldAtViewportCenter` | `static (double WorldX, double WorldY) WorldAtViewportCenter(double scrollX, double scrollY, double viewportWidth, double viewportHeight, CanvasLayout layout)` | World point under the viewport centre. |
| `PivotCenterScroll` | `static (double X, double Y) PivotCenterScroll(double pivotX, double pivotY, CanvasLayout layout, double viewportWidth, double viewportHeight)` | Scroll position that keeps the zoom pivot fixed. |
| `LayoutPivot` | `static Anchor LayoutPivot(CanvasLayout layout)` | The layout's zoom pivot. |
| `MinThumbSize` | `static double MinThumbSize(double size, double scale, double min)` | Clamps a minimap thumbnail dimension. |
| `ScaleCollapse` | `static (double ScaleX, double ScaleY, double CenterX, double CenterY) ScaleCollapse(double anchorX, double anchorY, double scaleX, double scaleY)` | Collapses world scale for a view. |
| `ScaleVisualBounds` | `static (double Left, double Top, double Width, double Height) ScaleVisualBounds(double anchorX, double anchorY, double width, double height, double scaleX, double scaleY)` | Scale-collapsed visual bounds. |
| `EnsureNegativeCover` | `static bool EnsureNegativeCover(ITreeComponent? tree)` | Grows the negative canvas cover so panned content stays addressable. |

```csharp
var localX = WorkflowSurfaceMath.ToCanvasLocal(scrollOffsetX, layout.ActualOffset.Horizontal);
var (centerX, centerY) = WorkflowSurfaceMath.CenterScroll(
    localX: 400, localY: 300, viewportWidth: 800, viewportHeight: 600, layout);
```

**Expected result:** a surface that scrolls to `scrollOffsetX` reports the same canvas-local position on every adapter because the subtraction happens once here.
