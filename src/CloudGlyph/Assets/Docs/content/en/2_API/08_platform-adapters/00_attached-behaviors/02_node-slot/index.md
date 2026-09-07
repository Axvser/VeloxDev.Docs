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

**Avalonia touch note:** on Android/iOS Avalonia registers pointer handlers with `Tunnel` routing so the `ScrollViewer`'s gesture recognizer does not steal capture (see the internal `PlatformDetection.IsTouchPlatform`). *Avalonia touch-competition behavior is source-verified; desktop drag semantics mirror WPF.*

### Razor component: `WorkflowSlotLayoutBehavior`

| Parameter | Type | Description |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | Node whose slots are laid out. |
| `IsEnabled` | `bool` | Enables layout sync. |
| `CoordinateHostId` | `string?` | Coordinate-space element id. |
| `ChildContent` | `RenderFragment?` | Slot content. |

Public JS-callback method: `OnSlotLayoutBatch(string[][] batch)` receives the recomputed anchors as a batch.
