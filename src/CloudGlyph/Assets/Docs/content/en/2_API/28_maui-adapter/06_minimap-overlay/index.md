# Minimap overlay

`WorkflowMinimapOverlay` is a MAUI `Grid` implementing `IWorkflowMinimapOverlay` and `IDrawable`. It draws thumbnails through `ICanvas` and navigates through the surface's `ScrollViewerName`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (overlay) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.MAUI`.

## WorkflowMinimapOverlay

**Signature:** `class WorkflowMinimapOverlay : Grid, IDrawable, IWorkflowMinimapOverlay`

### Data and layout properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offsets. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Canvas content offsets. |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | Viewport size in scroll space. |
| `IsMinimapVisible` | `bool` | `true` | Whether the minimap draws. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | Thumbnail size. |
| `MinimapMargin` | `double` | `12` | Gap from the available corner. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | Usable corner edges. |
| `RulerThickness` | `double` | `28` | Ruler band avoided by the overlay. |
| `LinkStrokeThickness` | `double` | `2` | Thumbnail link stroke. |
| `ScrollViewerName` | `string?` | `null` | `ScrollView` to navigate. |
| `RulerBand` | `double` | read-only `0` | No ruler band is drawn. |

### Appearance properties

This adapter uses `Color` rather than brushes:

| Property | Default |
| --- | --- |
| `MinimapBackgroundColor` | `Color.FromRgba(30, 30, 30, 51)` |
| `MinimapBorderColor` | `Color.FromRgba(148, 163, 184, 220)` |
| `NodeFillColor` | `Color.FromRgba(56, 189, 248, 220)` |
| `LinkStrokeColor` | `Color.FromRgba(180, 200, 220, 180)` |
| `ViewportStrokeColor` | `Color.FromRgba(255, 255, 255, 240)` |
| `ViewportFillColor` | `Color.FromRgba(255, 255, 255, 40)` |
| `ViewportStrokeThickness` | `1.5` |
| `MinimapCornerRadius` | `4` |
| `MinimapBorderThickness` | `1` |
| `NodeCornerRadius` | `1` |
| `ContentPadding` | `2` |
| `MinimapMinSize` | `20` |

Navigation follows the always-centre rule: a press anywhere in the thumbnail recentres the viewport.

**Expected result:** the minimap follows scrolling and a click recentres the surface through the resolved `ScrollView`.

## MinimapPipeline

**Signature:** `sealed class MinimapPipeline : MinimapPipelineCore<ICanvas, IMinimapRenderer<ICanvas>, IMinimapViewportHost, IMinimapInputHost>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapPipeline(IMinimapRenderer<ICanvas> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)` | constructor | Composes the layers. |

## MinimapRenderer

**Signature:** `sealed class MinimapRenderer : IMinimapRenderer<ICanvas>`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | constructor | Throws `ArgumentNullException` for null. |
| `Render(ICanvas surface, MinimapDrawContext context)` | `void` | Delegates to the owner's protected `DrawMinimapSurface`. |

## MinimapViewportHost

**Signature:** `sealed class MinimapViewportHost : IMinimapViewportHost`

| Member | Signature | Description |
| --- | --- | --- |
| `MinimapViewportHost(WorkflowMinimapOverlay owner)` | constructor | Reads the pushed offsets and scrolls the resolved `ScrollView`. |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | Current state, sanitized to finite values. |
| `ViewportWidth` / `ViewportHeight` | `double` | Viewport size. |
| `ScrollableWidth` / `ScrollableHeight` | `double` | Scrollable extents. |
| `ApplyScroll(double x, double y)` | `void` | Applies a scroll position. |

## MinimapInputHost

**Signature:** `sealed class MinimapInputHost : IMinimapInputHost`

| Member | Signature | Description |
| --- | --- | --- |
| `Capture()` | `bool` | Captures for a drag. |
| `Release()` | `void` | Releases capture. |
| `PointerPosition` / `IsPressed` / `IsCaptured` / `ClampRect` | properties | Pointer state and clamp rectangle. |
