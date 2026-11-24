# Adapter overlay

The WPF minimap is a `FrameworkElement` overlay plus three small platform classes. The overlay exposes dependency properties for placement and brushes; dragging and drawing are handled by the pipeline.

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors` for the overlay; `VeloxDev.WorkflowSystem.ViewHosting` for the pipeline classes.

## WorkflowMinimapOverlay

```csharp
public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay
```

### Placement and state properties

| Property | Type | Default | Meaning |
|---|---|---:|---|
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree to render. |
| `ViewportWidth` / `ViewportHeight` | `double` | `1d` | Viewport size in scroll space. |
| `IsMinimapVisible` | `bool` | `true` | Whether a pass draws. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200d` / `140d` | Requested size. |
| `MinimapMargin` | `double` | `12d` | Gap from the corner. |
| `MinimapMinSize` | `double` | `20d` | Smallest edge. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0d` | Corner edges pushed by the surface. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0d` | Scroll offsets pushed by the surface. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0d` | Content offsets pushed by the surface. |
| `RulerThickness` | `double` | `28d` | Ruler thickness reported to the surface. |
| `ScrollViewerName` | `string?` | `null` | Scroll viewer a drag writes back to. |

### Appearance properties

| Property | Type | Default |
|---|---|---|
| `MinimapBackground` | `Brush?` | `#331E1E1E` |
| `MinimapBorderBrush` | `Brush?` | `#DC94A3B8` |
| `NodeBrush` | `Brush?` | `#DC38BDF8` |
| `LinkBrush` | `Brush?` | `#B4B4C8DC` |
| `ViewportFill` | `Brush?` | `#28FFFFFF` |
| `ViewportStroke` | `Brush?` | `#F0FFFFFF` |
| `MinimapBorderThickness` | `double` | `1.0` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `LinkStrokeThickness` | `double` | `2.0` |
| `MinimapCornerRadius` | `double` | `4.0` |
| `NodeCornerRadius` | `double` | `1.0` |
| `ContentPadding` | `double` | `2.0` |

### Interface member

| Member | Description |
|---|---|
| `RulerBand` | Always `0`; the WPF overlay draws no separate ruler band. |

### Protected drawing hook

```csharp
protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context);
```

Override and call `base` to add to the default frame, thumbnails, and viewport block; replace it to draw your own. `LinkBrush` and `LinkStrokeThickness` are declared but the default drawing does not paint links; `MinimapDrawContext` carries node and viewport rectangles only.

The constructor sets `IsHitTestVisible = true` and `Focusable = true`, resolves `ScrollViewerName` on load, and drops the pipeline's tree on unload.

## MinimapPipeline

```csharp
public sealed class MinimapPipeline
    : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>,
        IMinimapViewportHost, IMinimapInputHost>
```

The WPF closure of the generic pipeline. The constructor has the same four parameters as the base: renderer, viewport host, input host, and optional metrics.

## MinimapRenderer

```csharp
public sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>
```

| Member | Description |
|---|---|
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | Throws `ArgumentNullException` for a null owner. |
| `Render(DrawingContext surface, MinimapDrawContext context)` | Routes to the owner's protected `DrawMinimap`. |

## MinimapViewportHost

```csharp
public sealed class MinimapViewportHost : IMinimapViewportHost
```

| Constructor / member | Description |
|---|---|
| `MinimapViewportHost(ScrollViewer scrollViewer)` | Standalone host that reads and scrolls the viewer directly. Throws `ArgumentNullException` for null. |
| `ScrollOffsetX` / `ScrollOffsetY` | The overlay's pushed value when owner-backed, else the viewer's offset. |
| `ContentOffsetX` / `ContentOffsetY` | The overlay's pushed content offset. |
| `ViewportWidth` / `ViewportHeight` | The overlay's pushed viewport size, else the viewer's. |
| `ScrollableWidth` / `ScrollableHeight` | The viewer's scrollable extent. |
| `ApplyScroll(double x, double y)` | Calls `ScrollToHorizontalOffset` and `ScrollToVerticalOffset`. |

## MinimapInputHost

```csharp
public sealed class MinimapInputHost : IMinimapInputHost
```

| Member | Description |
|---|---|
| `MinimapInputHost()` | Detached host for tests or a custom surface. |
| `PointerPosition` | Overlay-local pointer position; public setter. |
| `IsPressed` | Whether the primary button is down; public setter. |
| `IsCaptured` | Whether capture is held; private setter. |
| `ClampRect` | Optional hit rectangle; public setter. |
| `Capture()` | Captures the owner's mouse; returns whether it succeeded. |
| `Release()` | Releases capture. |

## Notes

- The surface behavior must resolve `MinimapOverlayName`; without it the overlay has no tree and draws nothing.
- `ScrollViewerName` on the overlay is what lets a drag write offsets back; it is separate from the surface's own `ScrollViewerName`.
- A host subclasses the overlay to change colours in the constructor or override `DrawMinimap`; no other member needs to be touched.
