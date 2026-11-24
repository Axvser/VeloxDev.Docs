# Overlays and decorators

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

Both components consume a `SurfaceViewport` supplied by the surface and implement the same Core interfaces as the XAML adapters, so host code can carry its ruler/minimap settings across platforms.

## Class: WorkflowGridDecorator

`public partial class WorkflowGridDecorator : ComponentBase, IWorkflowGridDecorator, IDisposable`

Ruler bars that mirror the surface's scroll/content offset. The band itself is moved by the surface's JS in the same frame as the scroll; only the tick window needs a server render.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Viewport` | `SurfaceViewport?` | `null` | Viewport context pushed by the surface. |
| `ViewportFeed` | `SurfaceViewportFeed?` | `null` | `[CascadingParameter]`; cheap tick-layer updates on every viewport change. |
| `RulerThickness` | `double` | `28` | Ruler band thickness in pixels. |
| `Spacing` | `double` | `40` | Tick spacing in pixels. |
| `RulerBackground` | `string` | `"rgba(37,37,38,0.78)"` | Band fill. |
| `TickColor` | `string` | `"#555555"` | Tick colour. |
| `LabelColor` | `string` | `"#888888"` | Numeric label colour. |
| `MajorLineEvery` | `int` | `5` | Minor cells per major tick. |
| `DividerColor` | `string` | `"#3A3D40"` | Ruler divider colour. |
| `AxisColor` | `string?` | `null` | World-zero tick colour; defaults to `TickColor`. |

### Interface properties

| Member | Type | Description |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Surface scroll offset. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Effective world origin. |
| `RulerBand` | `double` | Returns `RulerThickness`. |

`public void Dispose()` unsubscribes from `ViewportFeed`.

### Notes

- The tick set covers a window around the visible range, not the exact range; the JS translate handles per-frame motion.
- Unqualified CSS lengths are invalid; internal values are emitted with `px` and an invariant decimal point.

## Class: WorkflowMinimapOverlay

`public partial class WorkflowMinimapOverlay : ComponentBase, IWorkflowMinimapOverlay, IAsyncDisposable`

Full-surface, click-through thumbnail layer. The inner minimap box is placed in the content viewport's top-right corner using the area measured by JS.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Viewport` | `SurfaceViewport?` | `null` | Viewport context pushed by the surface. |
| `Width` | `double` | `180` | Minimap width in pixels. |
| `Height` | `double` | `120` | Minimap height in pixels. |
| `Background` | `string` | `"#331E1E1E"` | Minimap background. |
| `BorderColor` | `string` | `"#DC94A3B8"` | Minimap border. |
| `NodeFill` | `string` | `"#DC38BDF8"` | Node fill. |
| `NodeRadius` | `double` | `2` | Node corner radius. |
| `ViewportFill` | `string` | `"rgba(255,255,255,0.15)"` | Viewport indicator fill. |
| `ViewportStroke` | `string` | `"#F0FFFFFF"` | Viewport indicator stroke. |
| `ViewportStrokeWidth` | `double` | `1.5` | Viewport indicator stroke width. |
| `Padding` | `double` | `6` | Inner padding around mapped content. |
| `ScrollViewerId` | `string?` | `null` | Surface scroll container to measure and navigate. |
| `DrawMinimap` | `RenderFragment<MinimapDrawContext>?` | `null` | Extra content after the default nodes and viewport block. |

### Interface properties

| Member | Type |
| --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` |
| `ContentOffsetX` / `ContentOffsetY` | `double` |
| `RulerBand` | `double` (always `0`) |
| `ViewportWidth` / `ViewportHeight` | `double` |
| `WorkflowTree` | `ITreeComponent?` |
| `IsMinimapVisible` | `bool` |
| `MinimapMargin` | `double` (default `12`) |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `OnMinimapAreaMeasured(double availableRight, double availableTop, double availableBottom, double overlayWidth)` | `void` | `[JSInvokable]`; receives the free corner measured by JS. |
| `OnMinimapScrollRange(double maximumX, double maximumY)` | `void` | `[JSInvokable]`; caches the DOM scroll maxima. |
| `DisposeAsync()` | `ValueTask` | Disposes the pipeline, throttle and JS handles. |

### Notes

- `DrawMinimap` is a render fragment, not a virtual method: Blazor components cannot override another component's render tree.
- The viewport block is moved by JS on scroll, so scrolling costs one small interop instead of a full .NET re-render.
- Drag navigation stays in JS because this adapter keeps overscroll outside the model; applying the Core drag math here would translate content twice.
