# Surface and view pool

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Class: WorkflowSurfaceBehavior

`public partial class WorkflowSurfaceBehavior : ComponentBase, IAsyncDisposable`

Blazor analogue of the XAML surface attached behavior. It renders the scroll container, canvas, grid layer, panes and link-menu chrome; it routes pointer, wheel and key input into `WorkflowInput`.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Tree` | `ITreeComponent?` | `null` | Workflow tree rendered by the surface. |
| `IsEnabled` | `bool` | `false` | Enables pan and scroll tracking, and loads the JS module. |
| `ZoomEnabled` | `bool` | `false` | Wires Ctrl+wheel zoom through JS. |
| `ScrollViewerId` | `string` | `"veloxdev-wf-scroll"` | Scroll-container element id. |
| `CanvasId` | `string` | `"veloxdev-wf-canvas"` | Canvas element id. |
| `GridDecorator` | `RenderFragment<SurfaceViewport>?` | `null` | Optional ruler/grid fragment receiving the viewport. |
| `Minimap` | `RenderFragment<SurfaceViewport>?` | `null` | Optional minimap fragment receiving the viewport. |
| `ChildContent` | `RenderFragment<SurfaceCanvas>?` | `null` | Canvas content; receives the computed canvas size. |
| `LinkMenu` | `RenderFragment<ILinkComponent>?` | `null` | Menu entries; the fragment receives the pressed link. |
| `Background` | `string` | `"#0B1120"` | Canvas background colour. |
| `GridColor` | `string` | `"#2A2D2E"` | Minor grid-line colour. |
| `GridSpacing` | `double` | `40` | Grid spacing in pixels. |
| `MajorGridColor` | `string` | `"#3A3D40"` | Major grid-line colour. |
| `MajorLineEvery` | `int` | `5` | Minor cells between major grid lines. |
| `AxisColor` | `string` | `"#4D4D4D"` | World-origin axis colour. |
| `RulerThickness` | `double` | `28` | Ruler band reserved for the decorator. |

### Properties

| Member | Type | Description |
| --- | --- | --- |
| `MenuLink` | `ILinkComponent?` (get) | The link the open context menu acts on, or `null`. |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `RoutePointerAsync(SurfacePointerKind kind, double clientX, double clientY, MouseButton button = MouseButton.None, double deltaY = 0, IWorkflowComponent? target = null, InputModifiers modifiers = InputModifiers.None)` | `Task` | Converts viewport coordinates to canvas-local space and routes one pointer event. |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`; returns whether a subscriber refused the press. |
| `RequestWheelVerdict(double localX, double localY, double deltaY, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`; decides Ctrl+wheel before JS zooms. |
| `RequestWheelScroll(double localX, double localY, double deltaX, double deltaY, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`; routes a plain wheel and applies the default scroll when not refused. |
| `OnHoverTarget(string? id)` | `void` | `[JSInvokable]`; records the hovered node/slot id. |
| `OnWheelZoom(int wheelDelta, double scrollX, double scrollY, double viewportW, double viewportH, double reachW, double reachH)` | `Task` | `[JSInvokable]`; applies a coalesced zoom burst in one atomic step. |
| `OnSurfaceScroll(double scrollLeft, double scrollTop, double viewportW, double viewportH, double canvasW, double canvasH, double offsetX, double offsetY)` | `void` | `[JSInvokable]`; records scroll, grows the canvas, publishes the viewport. |
| `DisposeAsync()` | `ValueTask` | Releases model subscriptions and JS handles. |

None of the public methods declare exceptions. Interop failures inside `RoutePointerAsync` are swallowed and the event is dropped.

### Example

```razor
<div style="position:relative;width:100vw;height:100vh;">
    <TreeView Tree="_tree" />
</div>
```

```razor
<LinkMenu Context="link">
    <button type="button" @onclick="() => link.DeleteCommand.Execute(null)">Delete</button>
</LinkMenu>
```

### Notes

- The surface needs a parent with a real height. `100vh` gives the scroll element a viewport; `height:auto` collapses it and the canvas measures zero.
- The plain wheel is owned by JS because it needs a synchronous `preventDefault`; the surface applies the default scroll from `RequestWheelScroll`.
- While a link menu is open, `WorkflowInput.IsSuspended` keeps the pointer target so moving onto the menu does not clear it.
- Link hover moves focus to the surface root with `preventScroll`, which is what lets Delete reach the input route.

## Class: ViewPool

`public partial class ViewPool : ComponentBase, IDisposable`

Blazor-native pool: the renderer owns component instantiation and diffing, so this component is a thin wrapper over a source and a per-item fragment.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `ItemsSource` | `IEnumerable?` | `null` | Items to render; re-renders when it implements `INotifyCollectionChanged`. |
| `ItemTemplate` | `RenderFragment<object>?` | `null` | Per-item fragment; the item is the fragment context. |
| `EmptyContent` | `RenderFragment?` | `null` | Rendered when the source is empty. |
| `KeySelector` | `Func<object, object>?` | `null` | Key used to stabilize re-renders (analogue of `@key`). |

### Methods

`public void Dispose()` detaches the collection-changed handler.

### Notes

- A virtualization sweep emits many Add/Remove events; the pool coalesces them into one snapshot and one `StateHasChanged` per renderer turn.
- Keyed rendering through `KeySelector` is what preserves per-item component state.
