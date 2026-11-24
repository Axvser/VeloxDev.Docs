# Minimap overlay

`WorkflowMinimapOverlay` is an Avalonia `Control` implementing `IWorkflowMinimapOverlay` and `ICustomHitTest`. It draws thumbnails and the viewport frame, and turns a press into navigation through the surface's `ScrollViewerName`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (overlay) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.Avalonia`.

## WorkflowMinimapOverlay

**Signature:** `class WorkflowMinimapOverlay : Control, IWorkflowMinimapOverlay, ICustomHitTest`

### Data and layout properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Canvas content offsets. |
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree to render. |
| `ViewportWidth` / `ViewportHeight` | `double` | `0` | Viewport size in scroll space. |
| `IsMinimapVisible` | `bool` | `true` | Whether the minimap draws. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | Thumbnail size. |
| `MinimapMargin` | `double` | `12` | Gap from the available corner. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | Usable corner edges. |
| `RulerThickness` | `double` | `28` | Ruler band avoided by the overlay. |
| `LinkStrokeThickness` | `double` | `2` | Thumbnail link stroke. |
| `ScrollViewerName` | `string` | `""` | Scroll container to navigate; non-null on this adapter. |
| `RulerBand` | `double` | read-only `0` | No ruler band is drawn. |

### Appearance properties

| Property | Type | Default |
| --- | --- | --- |
| `MinimapBackground` | `IBrush?` | translucent dark (`#331E1E1E`) |
| `MinimapBorderBrush` | `IBrush?` | `#DC94A3B8` |
| `NodeBrush` | `IBrush?` | `#DC38BDF8` |
| `LinkBrush` | `IBrush?` | `#B4B4C8DC` |
| `ViewportStroke` | `IBrush?` | `#F0FFFFFF` |
| `ViewportFill` | `IBrush?` | `#28FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `MinimapCornerRadius` | `double` | `4` |
| `MinimapBorderThickness` | `double` | `1` |
| `NodeCornerRadius` | `double` | `1` |
| `ContentPadding` | `double` | `2` |
| `MinimapMinSize` | `double` | `20` |

Navigation follows the always-centre rule: a press anywhere in the thumbnail recentres the viewport on that point.

```xml
<behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                  HorizontalAlignment="Stretch"
                                  VerticalAlignment="Stretch"
                                  ScrollViewerName="PART_ScrollViewer" />
```

**Expected result:** the minimap follows scrolling, and a click recentres the surface.

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
| `MinimapViewportHost(ScrollViewer scrollViewer)` | constructor | Drives a `ScrollViewer` directly; the overlay uses an internal overlay-backed form. |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | Current state. |
| `ViewportWidth` / `ViewportHeight` | `double` | Viewport size. |
| `ScrollableWidth` / `ScrollableHeight` | `double` | Scrollable extents. |
| `ApplyScroll(double x, double y)` | `void` | Applies a scroll position. |

## MinimapInputHost

**Signature:** `sealed class MinimapInputHost : IMinimapInputHost`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapInputHost()` | constructor | Creates a pointer-state host. |
| `Capture()` | `bool` | Captures for a drag. |
| `Release()` | `void` | Releases capture. |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | properties | Pointer state and clamp rectangle. |
