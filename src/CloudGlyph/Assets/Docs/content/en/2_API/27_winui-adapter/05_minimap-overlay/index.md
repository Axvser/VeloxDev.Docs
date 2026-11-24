# Minimap overlay

`WorkflowMinimapOverlay` is a WinUI `Canvas` implementing `IWorkflowMinimapOverlay`. It draws thumbnails and the viewport frame, and navigates through the surface's `ScrollViewerName`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (overlay) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.WinUI`.

## WorkflowMinimapOverlay

**Signature:** `class WorkflowMinimapOverlay : Canvas, IWorkflowMinimapOverlay`

### Data and layout properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Canvas content offsets. |
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree to render. |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | Viewport size in scroll space. |
| `IsMinimapVisible` | `bool` | `true` | Whether the minimap draws. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | Thumbnail size. |
| `MinimapMargin` | `double` | `12` | Gap from the available corner. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | Usable corner edges. |
| `RulerThickness` | `double` | `28` | Ruler band avoided by the overlay. |
| `LinkStrokeThickness` | `double` | `2` | Thumbnail link stroke. |
| `ScrollViewerName` | `string?` | `null` | Scroll container to navigate. |
| `RulerBand` | `double` | read-only `0` | No ruler band is drawn. |

### Appearance properties

The brush properties mirror WPF: `MinimapBackground`, `MinimapBorderBrush`, `NodeBrush`, `LinkBrush`, `ViewportStroke`, `ViewportFill` (`Brush?`), plus `ViewportStrokeThickness`, `MinimapCornerRadius`, `MinimapBorderThickness`, `NodeCornerRadius`, `ContentPadding`, `MinimapMinSize` (`double`).

Navigation follows the always-centre rule: a press anywhere in the thumbnail recentres the viewport.

**Expected result:** the minimap follows scrolling; a click recentres the surface through the same single write entry the wheel uses.

## MinimapPipeline

**Signature:** `sealed class MinimapPipeline : MinimapPipelineCore<WorkflowMinimapOverlay, IMinimapRenderer<WorkflowMinimapOverlay>, IMinimapViewportHost, IMinimapInputHost>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<WorkflowMinimapOverlay> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | constructor | Composes the three layers. |

## MinimapRenderer

**Signature:** `sealed class MinimapRenderer : IMinimapRenderer<WorkflowMinimapOverlay>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | constructor | Throws `ArgumentNullException` for null. |
| `Render(WorkflowMinimapOverlay surface, MinimapDrawContext context)` | `void` | Delegates to the owner's protected `DrawMinimapSurface`. |

## MinimapViewportHost

**Signature:** `sealed class MinimapViewportHost : IMinimapViewportHost`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapViewportHost(WorkflowMinimapOverlay owner)` | constructor | Reads the pushed offsets and applies scroll through the surface. |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | Current state from the overlay. |
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
