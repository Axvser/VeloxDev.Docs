# Input components

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

Each component wraps its content in an absolutely positioned element and owns one gesture. The matching JS initializer measures and drives that element; the component routes presses through Core and applies the resulting commands.

## Class: WorkflowNodeDragBehavior

`public partial class WorkflowNodeDragBehavior : ComponentBase, IAsyncDisposable`

Renders node content whose left/top/z-index follow `INodeComponent.Anchor`, and turns pointer drags into `MoveCommand` executions.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Node` | `INodeComponent?` | `null` | Node to render and move. |
| `IsEnabled` | `bool` | `false` | Loads the JS node-drag initializer. |
| `Style` | `string?` | `null` | Extra styles appended to the positioned wrapper. |
| `ChildContent` | `RenderFragment?` | `null` | Node content. |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`; routes the press on the node's relay. |
| `OnNodeDrag(double dx, double dy)` | `void` | `[JSInvokable]`; executes `MoveCommand` with a world delta. |
| `OnNodeDragEnd()` | `void` | `[JSInvokable]`; snaps the wrapper to the final .NET anchor. |
| `DisposeAsync()` | `ValueTask` | Releases the node subscription and JS handles. |

While a drag is active, `Anchor` changes do not re-render or reposition the wrapper: JS owns the position until the drag ends.

### Example

```razor
<WorkflowNodeDragBehavior Node="node" IsEnabled="true"
                          Style="width:260px;height:180px;">
    <NodeView />
</WorkflowNodeDragBehavior>
```

## Class: WorkflowSlotConnectionBehavior

`public partial class WorkflowSlotConnectionBehavior : ComponentBase, IAsyncDisposable`

Wraps a slot's content and translates connection gestures into send / set-pointer / receive / reset commands.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Slot` | `ISlotComponent?` | `null` | Slot that initiates and receives connections. |
| `Tree` | `ITreeComponent?` | `null` | Tree that owns the connection gesture. |
| `IsEnabled` | `bool` | `false` | Loads the JS slot-connection initializer. |
| `Style` | `string?` | `null` | Wrapper element style. |
| `ChildContent` | `RenderFragment?` | `null` | Slot content. |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`; routes the press on the slot's relay. |
| `OnSlotConnectionStart(double worldX, double worldY)` | `void` | `[JSInvokable]`; pins the slot anchor and sends `SendConnectionCommand`. |
| `OnSlotConnectionMove(double worldX, double worldY)` | `void` | `[JSInvokable]`; sets the pointer and updates the preview receiver. |
| `OnSlotConnectionEnd(string? targetSlotId)` | `void` | `[JSInvokable]`; receives on the target slot or resets the virtual link. |
| `DisposeAsync()` | `ValueTask` | Releases JS handles. |

### Notes

- `OnSlotConnectionEnd` resets the virtual link when the release does not land on a willing receiver, including the sender itself.
- `SlotView` already opens this component; wrapping it twice doubles measurement and gesture handling.

## Class: WorkflowSlotLayoutBehavior

`public partial class WorkflowSlotLayoutBehavior : ComponentBase, IAsyncDisposable`

Measures the on-screen centres of the wrapped slot elements (which expose `data-slot-id`) and writes their anchors back in canvas coordinates.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `Node` | `INodeComponent?` | `null` | Node whose slots are synchronized. |
| `IsEnabled` | `bool` | `false` | Loads the JS slot-layout initializer. |
| `CoordinateHostId` | `string?` | `null` | Reserved coordinate-host id. |
| `ChildContent` | `RenderFragment?` | `null` | Node content containing slot elements. |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `OnSlotLayoutBatch(string[][] batch)` | `void` | `[JSInvokable]`; each entry is `[slotId, canvasLocalX, canvasLocalY]`. |
| `DisposeAsync()` | `ValueTask` | Stops the pipeline and releases JS handles. |

### Notes

- The JS rAF/ResizeObserver schedule is the authority for when measurement runs; the component feeds one batch into the shared `SlotLayoutPipelineCore`.
- Values are parsed with `InvariantCulture`; a comma-decimal server would otherwise misplace anchors silently.
- If an anchor was written, the node is told its `Anchor` changed so links repaint during the drag.

## Enum: SurfacePointerKind

`public enum SurfacePointerKind`

| Member | Value | Meaning |
| --- | --- | --- |
| `Entered` | `0` | Pointer arrived over the element. |
| `Moved` | `1` | Pointer moved. |
| `Exited` | `2` | Pointer left the element. |
| `Pressed` | `3` | A button went down. |
| `Released` | `4` | A button came up. |
| `Wheel` | `5` | The wheel turned. |

`RoutePointerAsync` maps these to the matching Core `PointerEventArgs` subtype. This is a browser-boundary enum, not a Core input phase.
