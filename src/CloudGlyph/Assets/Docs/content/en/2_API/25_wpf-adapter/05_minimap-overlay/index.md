# Minimap overlay

`WorkflowMinimapOverlay` is a `FrameworkElement` implementing `IWorkflowMinimapOverlay`: it draws node/link thumbnails, a viewport frame, and turns a press into a scroll. It shares the surface's `ScrollViewerName` resolution, so the element must name the same scroll container as the surface.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (overlay) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.WPF`.

## WorkflowMinimapOverlay

**Signature:** `class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay`

### Data and layout properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offsets, pushed by the surface. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Canvas content offsets. |
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree to render. |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | Viewport size in scroll space. |
| `IsMinimapVisible` | `bool` | `true` | Whether the minimap draws. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | Thumbnail size. |
| `MinimapMargin` | `double` | `12` | Gap from the available corner. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | Usable corner edges pushed by the surface. |
| `RulerThickness` | `double` | `28` | Ruler band the overlay avoids. |
| `LinkStrokeThickness` | `double` | `2` | Thumbnail link stroke. |
| `ScrollViewerName` | `string?` | `null` | Scroll container to navigate. |
| `RulerBand` | `double` | read-only `0` | The overlay draws no ruler band. |

### Appearance properties

| Property | Type | Default |
| --- | --- | --- |
| `MinimapBackground` | `Brush?` | translucent dark (`#331E1E1E`) |
| `MinimapBorderBrush` | `Brush?` | `#DC94A3B8` |
| `NodeBrush` | `Brush?` | `#DC38BDF8` |
| `LinkBrush` | `Brush?` | `#B4B4C8DC` |
| `ViewportStroke` | `Brush?` | `#F0FFFFFF` |
| `ViewportFill` | `Brush?` | `#28FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `MinimapCornerRadius` | `double` | `4` |
| `MinimapBorderThickness` | `double` | `1` |
| `NodeCornerRadius` | `double` | `1` |
| `ContentPadding` | `double` | `2` |
| `MinimapMinSize` | `double` | `20` |

Navigation follows the always-centre rule: pressing anywhere in the thumbnail puts that world point at the viewport centre. The overlay does not decide the scroll itself; `MinimapViewportHost` resolves the drag into offsets.

```xml
<behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                  HorizontalAlignment="Stretch"
                                  VerticalAlignment="Stretch"
                                  ScrollViewerName="PART_ScrollViewer" />
```

**Expected result:** the thumbnail shows the graph, the viewport frame follows scrolling, and a click recentres the surface.

## MinimapPipeline

**Signature:** `sealed class MinimapPipeline : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>, IMinimapViewportHost, IMinimapInputHost>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<DrawingContext> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | constructor | Composes the three layers. |

## MinimapRenderer

**Signature:** `sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | constructor | Throws `ArgumentNullException` for null. |
| `Render(DrawingContext surface, MinimapDrawContext context)` | `void` | Delegates to the owner's protected `DrawMinimapSurface`. |

## MinimapViewportHost

**Signature:** `sealed class MinimapViewportHost : IMinimapViewportHost`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapViewportHost(ScrollViewer scrollViewer)` | constructor | Drives a `ScrollViewer` directly. |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | Current state; overlay-backed form wins when constructed by the overlay. |
| `ViewportWidth` / `ViewportHeight` | `double` | Viewport size. |
| `ScrollableWidth` / `ScrollableHeight` | `double` | Scrollable extents. |
| `ApplyScroll(double x, double y)` | `void` | Applies a scroll position. |

## MinimapInputHost

**Signature:** `sealed class MinimapInputHost : IMinimapInputHost`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapInputHost()` | constructor | Creates a pointer-state host. |
| `Capture()` | `bool` | Captures the pointer for a drag. |
| `Release()` | `void` | Releases it. |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | properties | Pointer state and the drag clamp rectangle. |
