# Gesture behaviors

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

These three attached behaviors own the platform half of node dragging, slot connection and slot measurement. The shared pipelines in Core own ordering, duplicate suppression and re-measure scheduling.

## Class: WorkflowNodeDragBehavior

`public sealed class WorkflowNodeDragBehavior`

Turns a press on the marked element into `INodeComponent.MoveCommand` executions, coalesced to roughly 60 Hz.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`, `SetCoordinateHostName` |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | Reads the drag switch. |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | Writes the drag switch. |
| `GetCoordinateHostName(VisualElement element)` | `string?` | Reads the coordinate-host name. |
| `SetCoordinateHostName(VisualElement element, string? value)` | `void` | Writes the coordinate-host name. |
| `Ensure(VisualElement element)` | `void` | Subscribes when enabled, unsubscribes otherwise. |

The drag is measured in the coordinate host's local space — the named element, or the nearest visual canvas. The node is found by walking visual ancestors for an `INodeComponent` data context. A press refused by `WorkflowSurfaceBehavior.GetPressHandle(...).PreventDefault` does not start a drag.

### Example

```xml
<Border x:Name="PART_TitleRow"
        behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
        behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />
```

## Class: WorkflowSlotConnectionBehavior

`public sealed class WorkflowSlotConnectionBehavior`

Starts a connection on a left-press and completes it on release.

### Attached property

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | Reads the connection switch. |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | Writes the connection switch. |
| `Ensure(VisualElement element)` | `void` | Subscribes when enabled, unsubscribes otherwise. |

Press executes `ISlotComponent.SendConnectionCommand`. Release resolves the slot under the pointer and executes that slot's `ReceiveConnectionCommand`; releasing on the sender does not connect. Whether a connection is legal is decided by the model.

### Example

```xml
<local:SlotView behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

## Class: WorkflowSlotLayoutBehavior

`public sealed class WorkflowSlotLayoutBehavior`

Measures the declared slot parts and writes their world-space anchors to the model.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `SlotNamesProperty` | `string?` | `null` | `GetSlotNames`, `SetSlotNames` |
| `SlotEnumeratorNamesProperty` | `string?` | `null` | `GetSlotEnumeratorNames`, `SetSlotEnumeratorNames` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`, `SetCoordinateHostName` |

`SlotNames` and `SlotEnumeratorNames` are comma-separated `x:Name` lists. Enumerators must be visual items controls whose realized items are slots.

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | Reads the layout switch. |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | Writes the layout switch. |
| `GetSlotNames(VisualElement element)` | `string?` | Reads the named slot parts. |
| `SetSlotNames(VisualElement element, string? value)` | `void` | Writes the named slot parts. |
| `GetSlotEnumeratorNames(VisualElement element)` | `string?` | Reads the named enumerator parts. |
| `SetSlotEnumeratorNames(VisualElement element, string? value)` | `void` | Writes the named enumerator parts. |
| `GetCoordinateHostName(VisualElement element)` | `string?` | Reads the coordinate-host name. |
| `SetCoordinateHostName(VisualElement element, string? value)` | `void` | Writes the coordinate-host name. |
| `Ensure(VisualElement element)` | `void` | Attaches when enabled, detaches otherwise. |

Measurement runs after each surface layout pass. The locator reports `SlotCoordinateSpace.CanvasLocal`, because `PointFromSurface` already inverts the camera. The pipeline suppresses sub-pixel changes and preserves the slot's layer number.

### Example

```xml
<local:NodeView behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                 behaviors:WorkflowSlotLayoutBehavior.SlotNames="InputSlot"
                 behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="OutputSlots"
                 behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas" />
```

### Notes

- A renamed `PART_*` or slot name must change here in the same edit; nothing enumerates `node.Slots`.
- `Ensure` is idempotent and called by the surface for every visual on a pool refresh.
