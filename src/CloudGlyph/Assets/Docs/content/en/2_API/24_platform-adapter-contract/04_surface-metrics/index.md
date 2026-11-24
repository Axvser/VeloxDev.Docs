# Surface metrics

A surface computes one immutable snapshot per pass and pushes the same numbers into the grid decorator, the minimap and the tree's viewport. Keeping the arithmetic in Core is what makes the seven adapters shrink the overlay area for rulers and scrollbars identically.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## SurfaceViewport

**Signature:** `sealed record SurfaceViewport(ITreeComponent Tree, double ScrollLeft, double ScrollTop, double ViewportWidth, double ViewportHeight, double ContentOffsetX, double ContentOffsetY)`

An immutable snapshot of the surface state, passed to viewport-driven overlays so they can re-render without rebuilding the whole surface.

## SurfaceCanvas

**Signature:** `sealed record SurfaceCanvas(double Width, double Height)`

The computed canvas size, passed to a content fragment (for example an SVG link layer) so children size themselves to the same canvas.

## SurfaceMetrics

**Signature:** `readonly struct SurfaceMetrics`

| Member | Type | Description |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` (init) | Scroll container offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` (init) | Canvas content offsets (`CanvasLayout.ActualOffset`). |
| `ViewportWidth` / `ViewportHeight` | `double` (init) | Visible viewport size. |
| `RulerBand` | `double` (init) | Thickness of the ruler band overlapping the top and left edges. |
| `VerticalScrollBarThickness` / `HorizontalScrollBarThickness` | `double` (init) | Scrollbar thickness when visible, otherwise zero. |
| `Available` | `SurfaceAvailableArea` (init) | The free corner overlays may use. |
| `Create(double scrollOffsetX, double scrollOffsetY, double contentOffsetX, double contentOffsetY, double viewportWidth, double viewportHeight, double surfaceWidth, double surfaceHeight, double rulerBand, double verticalScrollBarThickness, double horizontalScrollBarThickness, double margin)` | `static SurfaceMetrics` | Derives `Available` from the surface size, ruler band and scrollbars. |

`Create` computes `Available.Right = max(0, surfaceWidth − verticalScrollBarThickness)`, `Available.Top = max(0, rulerBand)` and `Available.Bottom = max(0, surfaceHeight − horizontalScrollBarThickness)`.

## SurfaceAvailableArea

**Signature:** `readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>`

| Member | Type | Description |
| --- | --- | --- |
| `Right` | `double` (init) | Usable right edge. |
| `Top` | `double` (init) | Usable top edge, below the horizontal ruler band. |
| `Bottom` | `double` (init) | Usable bottom edge, above the horizontal scrollbar. |
| `Margin` | `double` (init) | Gap an overlay keeps from the corner. |
| `IsUsable` | `bool` | `Right > 0 && Bottom > Top`. |
| `GetRect(double desiredWidth, double desiredHeight, double minimumSize)` | `WorkflowBounds` | Places a box at the top-right corner, clamped to the free area and minimum size; falls back to the origin when unusable. |

`GetRect` returns the `WorkflowBounds` value type from the graph geometry API.

## ISurfaceMetricsSource

**Signature:** `interface ISurfaceMetricsSource`

| Member | Signature | Description |
| --- | --- | --- |
| `ReadMetrics` | `SurfaceMetrics ReadMetrics()` | Reads the current measurements. Called on every pass, so it must be allocation-free and current. |

## SurfaceMetricsPush

**Signature:** `static class SurfaceMetricsPush`

| Member | Signature | Description |
| --- | --- | --- |
| `PushGrid` | `static void PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree)` | Writes the four offsets and forwards `RulerBand` to the tree's virtualization inset. Throws `ArgumentNullException` for a null decorator. |
| `PushMinimap` | `static void PushMinimap(SurfaceMetrics metrics, IWorkflowMinimapOverlay minimap, ITreeComponent? tree)` | Writes offsets, viewport size, tree and available edges. Throws `ArgumentNullException` for a null minimap. |
| `PushViewport` | `static void PushViewport(SurfaceMetrics metrics, ITreeComponent tree)` | Writes `tree.GetHelper().Viewport` from `scroll − contentOffset` and persists `Layout.ViewportOffset`. Throws `ArgumentNullException` for a null tree. |

```csharp
var metrics = SurfaceMetrics.Create(
    scrollOffsetX: 120, scrollOffsetY: 80,
    contentOffsetX: 0, contentOffsetY: 0,
    viewportWidth: 800, viewportHeight: 600,
    surfaceWidth: 800, surfaceHeight: 600,
    rulerBand: 28, verticalScrollBarThickness: 12,
    horizontalScrollBarThickness: 12, margin: 12);

SurfaceMetricsPush.PushGrid(metrics, decorator, tree);
SurfaceMetricsPush.PushMinimap(metrics, minimap, tree);
SurfaceMetricsPush.PushViewport(metrics, tree);
```

**Expected result:** after `PushViewport`, `tree.GetHelper().Viewport.Horizontal` equals `120` and `tree.Layout.ViewportOffset.Horizontal` equals `120`.

## SurfaceViewportFeed

**Signature:** `sealed class SurfaceViewportFeed`

| Member | Type | Description |
| --- | --- | --- |
| `Current` | `SurfaceViewport?` | The last published snapshot; `null` before the first publish. |
| `Changed` | `event Action<SurfaceViewport>` | Raised on every publish. |
| `Publish(SurfaceViewport viewport)` | `void` | Stores the snapshot and raises `Changed`. |

A feed lets cheap overlays follow the viewport without forcing the node/link content to re-render.
