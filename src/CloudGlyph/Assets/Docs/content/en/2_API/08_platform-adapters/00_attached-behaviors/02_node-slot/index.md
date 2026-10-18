# API — Attached Behaviors · Node Drag & Slot Behaviors

The three behaviors that make a workflow interactive: dragging nodes, connecting slots, and keeping slot anchors aligned to the node layout. All are in `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Class: `WorkflowNodeDragBehavior`

Makes a node draggable. On press it captures the pointer; on move it executes `node.MoveCommand.Execute(new Offset(current - last))`; on release/lost capture it stops.

Attached properties (WPF / Avalonia / WinUI / MAUI / Jalium use their native property system; Razor is a component):

| Property | Type | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Enables capture + move handling. |
| `CoordinateHostName` | attached `string?` | Name of the element whose coordinate space is used for the delta. |
| `CoordinateHostType` | attached `Type?` | Fallback host type; defaults to `Canvas`. |

| Adapter | Shape / notes |
|---|---|
| WPF | `sealed class : DependencyObject`; getters `GetIsEnabled(DependencyObject)`, `GetCoordinateHostName/Type(...)` |
| Avalonia | `sealed class : AvaloniaObject`; `RegisterAttached<WorkflowNodeDragBehavior, Control, ...>` |
| WinUI | `sealed class : DependencyObject` |
| MAUI | `sealed class`; `BindableProperty.CreateAttached`; getters take `BindableObject` |
| WinForms | `sealed class` over a `Control` state table (mouse down/move/up handling) |
| Jalium | `sealed class : DependencyObject` |

### Razor component: `WorkflowNodeDragBehavior`

| Parameter | Type | Description |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | Node to drag. |
| `IsEnabled` | `bool` | Enables drag wiring. |
| `Style` | `string?` | Optional CSS style. |
| `ChildContent` | `RenderFragment?` | Node content. |

Public methods `OnNodeDrag(double dx, double dy)` and `OnNodeDragEnd()` are the JS callbacks that run `MoveCommand`.

## Class: `WorkflowSlotConnectionBehavior`

Connects slots by press/release. On press it executes `slot.SendConnectionCommand.Execute(null)`; on release `slot.ReceiveConnectionCommand.Execute(null)`.

| Adapter | Shape | Extra |
|---|---|---|
| WPF | `sealed class : DependencyObject`; attached `IsEnabled` (`bool`) | |
| Avalonia | `sealed class : AvaloniaObject` | |
| WinUI | `sealed class : DependencyObject` | |
| MAUI | `sealed class`; `BindableProperty.CreateAttached` | also `public static void SetIsDraggingConnection(bool)` global drag-flag setter |
| WinForms | `sealed class` over a `Control` state table | |
| Jalium | `sealed class : DependencyObject` | |

### Razor component: `WorkflowSlotConnectionBehavior`

| Parameter | Type | Description |
|---|---|---|
| `Slot` | `IWorkflowSlotViewModel?` | The slot to connect. |
| `Tree` | `IWorkflowTreeViewModel?` | Tree used for drop-target lookup. |
| `IsEnabled` | `bool` | Enables connection wiring. |
| `Style` | `string?` | Optional CSS style. |
| `ChildContent` | `RenderFragment?` | Slot content. |

Public JS-callback methods: `OnSlotConnectionStart(double worldX, double worldY)`, `OnSlotConnectionMove(double worldX, double worldY)`, `OnSlotConnectionEnd(string? targetSlotId)`.

### Connection preview during the drag

The connection gesture exposes a live candidate receiver through two Core members (namespace `VeloxDev.WorkflowSystem`), not through adapter types:

| Member | Signature | Role |
|---|---|---|
| `WorkflowTreeEx.StandardSetPreviewReceiver` | `static void StandardSetPreviewReceiver(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel? slot)` | Reports the slot under the pointer. Ignores the sender, skips re-validation while the candidate is unchanged, and otherwise writes `SlotState.PreviewReceiver` + `ConnectionPreviewState`. |
| `WorkflowTreeEx.StandardRefreshConnectionPreview` | `static void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)` | Re-runs the check for the current candidate (for an asynchronous host verdict). |
| `WorkflowTreeEx.StandardCheckConnection` | `static ConnectionCheck StandardCheckConnection(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | Pure pre-check: direction, same-node, and the helper's `ValidateConnection`. |
| `SlotHitTestEx.HitTest` | `static IWorkflowSlotViewModel? HitTest(IWorkflowTreeViewModel tree, double x, double y, double radius = 12d)` | Nearest measured slot anchor within `radius`; `NaN` anchors are skipped. |

Each adapter calls these from its own pointer-move path while `tree.VirtualLink.IsVisible`:

| Adapter | Pointer-move call site |
|---|---|
| WPF | `WorkflowSurfaceBehavior.OnPreviewMouseMove` (returns before hover routing) |
| Avalonia | `WorkflowSurfaceBehavior.OnPointerMoved` |
| WinUI | `WorkflowSurfaceBehavior.OnPointerMoved` |
| Jalium | `WorkflowSurfaceBehavior.OnMouseMove` |
| MAUI | `WorkflowSlotConnectionBehavior.UpdatePointer` |
| WinForms | `WorkflowSlotConnectionBehavior.UpdatePointer` |
| Razor | `WorkflowSlotConnectionBehavior.OnSlotConnectionMove` (`[JSInvokable]`) |

```csharp
// Source: Src/Adapters/VeloxDev.WPF/Attached/Workflow/WorkflowSurfaceBehavior.cs
viewModel.SetPointerCommand.Execute(pointer);

if (viewModel.VirtualLink.IsVisible)
{
    viewModel.StandardSetPreviewReceiver(
        SlotHitTestEx.HitTest(viewModel, pointer.Horizontal, pointer.Vertical));
    return;
}
```

**Evidence:** the Core tests `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs` cover `StandardSetPreviewReceiver` (candidate changes, sender self-hit, clearing) and `SlotHitTestEx.HitTest` (nearest slot, empty tree).

## Class: `WorkflowSlotLayoutBehavior`

Keeps slot anchors in sync with the node layout. It watches the node's `Anchor` / `Size` / slot properties and re-computes each slot's `Anchor` (accounting for `Layout.ActualOffset`), using `TranslatePoint` to find the slot center.

| Property | Type | Description |
|---|---|---|
| `IsEnabled` | attached `bool` | Enables layout sync. |
| `SlotNames` | attached `string?` | Comma-separated names of single slot controls (e.g. `PART_InputSlot`). |
| `SlotEnumeratorNames` | attached `string?` | Comma-separated names of `ItemsControl`s enumerating slots (e.g. `PART_OutputSlots`). |
| `CoordinateHostName` | attached `string?` | Coordinate space for computing the anchor. |
| `CoordinateHostType` | attached `Type?` | Fallback host type; defaults to `Canvas`. |

| Adapter | Shape |
|---|---|
| WPF | `sealed class : DependencyObject` |
| Avalonia | `sealed class : AvaloniaObject` |
| WinUI | `sealed class : DependencyObject` |
| MAUI | `sealed class`; `BindableProperty.CreateAttached` |
| WinForms | `sealed class` over a `Control` state table |
| Jalium | `sealed class : DependencyObject` |

### Razor component: `WorkflowSlotLayoutBehavior`

| Parameter | Type | Description |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | Node whose slots are laid out. |
| `IsEnabled` | `bool` | Enables layout sync. |
| `CoordinateHostId` | `string?` | Coordinate-space element id. |
| `ChildContent` | `RenderFragment?` | Slot content. |

Public JS-callback method: `OnSlotLayoutBatch(string[][] batch)` receives the recomputed anchors as a batch.
