# Overlays

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`; the scroll-source interface is in `VeloxDev.WorkflowSystem.Platform`.

## Class: WorkflowMinimapOverlay

`public class WorkflowMinimapOverlay : VisualElement, IWorkflowMinimapOverlay, IWorkflowMinimapScrollSource`

Full-surface thumbnail layer. Only the thumbnail rectangle is hit-testable; the rest of the layer lets pointer input through. Tree subscription, mapping, placement and drag math live in the Core `MinimapPipeline`; this class supplies the palette, drawing and pointer handlers.

### Constructor

`public WorkflowMinimapOverlay()`

Creates the overlay as a full-surface layer, its `MinimapPipeline`, and the input host.

### Event

| Member | Type | Description |
| --- | --- | --- |
| `ViewportScrollRequested` | `event Action<double, double>?` | World origin requested by dragging the viewport block. |

### Properties

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `MinimapBackground` | `Color` | `#331E1E1E` | Panel fill. |
| `MinimapBorderBrush` | `Color` | `#DC94A3B8` | Panel border. |
| `NodeBrush` | `Color` | `#DC38BDF8` | Thumbnail fill per node. |
| `ViewportStroke` | `Color` | `#F0FFFFFF` | Viewport-block stroke. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | Surface scroll offset pushed by the surface. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | Content offset pushed by the surface. |
| `RulerBand` | `double` | `0` | Always zero: the minimap reserves no ruler band. |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | Visible viewport size. |
| `WorkflowTree` | `ITreeComponent?` | `null` | Tree the minimap renders. |
| `IsMinimapVisible` | `bool` | `true` | Whether the minimap draws and hit-tests. |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | Requested thumbnail size in surface pixels. |
| `MinimapMargin` | `double` | `12` | Gap to the available corner. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | Corner exclusions pushed by the surface. |

### Extension point

`protected virtual void DrawMinimap(Graphics graphics, MinimapDrawContext context)` draws the default panel. Override and call `base` to add to it. `protected static Color ParseColor(string hex)` accepts `#RRGGBB`, `#AARRGGBB` and named colours.

### Notes

- `IWorkflowMinimapOverlay` is implemented so the surface can push metrics without knowing the concrete type.
- `IWorkflowMinimapScrollSource` is adapter-declared: the event carries screen-space scroll, which only a host with its own scroll model can consume.

## Class: WorkflowInfoOverlay

`public sealed class WorkflowInfoOverlay : VisualElement`

Realtime canvas-information HUD. The surface feeds offsets and zoom; the HUD reads the tree for actual size and visible counts.

### Constructor

`public WorkflowInfoOverlay()`

Creates the HUD, its copy button and model subscriptions. The text area is hit-test transparent.

### Properties

| Property field | CLR type | Default |
| --- | --- | --- |
| `ScrollOffsetXProperty` | `double` | `0` |
| `ScrollOffsetYProperty` | `double` | `0` |
| `ContentOffsetXProperty` | `double` | `0` |
| `ContentOffsetYProperty` | `double` | `0` |
| `ZoomProperty` | `double` | `1` |

| Member | Type | Description |
| --- | --- | --- |
| `CopyButton` | `VisualButton` | The only interactive region; the host may restyle it. |
| `CopyFeedback` | `event EventHandler<string>?` | Raised with a short status after a copy attempt. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Horizontal/vertical scroll offset in surface pixels. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Content offset (layout origin plus ruler band). |
| `Zoom` | `double` | Camera zoom. |
| `Lines` | `IReadOnlyList<string>` | Lines currently shown, in display order. |

### Example

```csharp
var info = new WorkflowInfoOverlay { Zoom = 1.25 };
info.CopyFeedback += (_, message) => statusLabel.Text = message;
// Source: source
```

Copying joins `Lines` with the platform newline. Clipboard failures are reported through `CopyFeedback` instead of throwing.

## Interface: IWorkflowMinimapScrollSource

`public interface IWorkflowMinimapScrollSource` — namespace `VeloxDev.WorkflowSystem.Platform`.

| Member | Type | Description |
| --- | --- | --- |
| `ViewportScrollRequested` | `event Action<double, double>?` | Requested world origin when the minimap viewport is dragged. |

Kept off `IWorkflowMinimapOverlay` so the shared Core interface stays framework-agnostic.
