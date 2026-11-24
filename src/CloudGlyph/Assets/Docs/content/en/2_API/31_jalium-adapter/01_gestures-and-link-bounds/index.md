# Gestures and link bounds

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

Jalium's gesture behaviors are attached properties on instance `DependencyObject` types. The shared Core pipelines still own ordering, duplicate suppression and re-measure scheduling; these classes own the visual-tree walk, coordinates and UI-thread hand-off.

## Class: WorkflowNodeDragBehavior

`public sealed class WorkflowNodeDragBehavior : DependencyObject`

Turns a press on the marked element into `INodeComponent.MoveCommand` executions.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`, `SetCoordinateHostName` |
| `CoordinateHostTypeProperty` | `Type?` | `null` | `GetCoordinateHostType`, `SetCoordinateHostType` |

All accessors take a `DependencyObject` and do not throw. The coordinate host is resolved by name first, then by type (default `Canvas`), walking up the visual tree.

### Example

```xml
<Border x:Name="PART_TitleRow"
        behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
        behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />
```

Attach it to the card's title bar rather than the whole card, so dragging a port does not drag the node.

## Class: WorkflowSlotConnectionBehavior

`public sealed class WorkflowSlotConnectionBehavior : DependencyObject`

Owns a complete connection gesture, including failure cleanup.

### Attached property

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |

### Notes

- A left-press executes `SendConnectionCommand`; the matching left-button release completes or resets the gesture.
- The slot is read from the element's `DataContext`, so a pooled slot view is wired to whichever slot it shows.
- Every release that does not land on a willing receiver resets the virtual link. Releasing on the sender is the common case and must not leave a rubber band hanging.

## Class: WorkflowSlotLayoutBehavior

`public sealed class WorkflowSlotLayoutBehavior : DependencyObject`

Measures a node card's slot controls and writes each centre back to the slot's `Anchor`.

### Attached properties

| Property field | CLR type | Default | Accessors |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`, `SetIsEnabled` |
| `SlotNamesProperty` | `string?` | `null` | `GetSlotNames`, `SetSlotNames` |
| `SlotEnumeratorNamesProperty` | `string?` | `null` | `GetSlotEnumeratorNames`, `SetSlotEnumeratorNames` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`, `SetCoordinateHostName` |
| `CoordinateHostTypeProperty` | `Type?` | `null` | `GetCoordinateHostType`, `SetCoordinateHostType` |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `Refresh(FrameworkElement control)` | `void` | Schedules a re-measure for a transform/scale-only change. |
| `SyncNow(FrameworkElement control)` | `void` | Measures immediately, for callers that already ran the layout pass. |

No exception is declared.

### Notes

- The locator reports `SlotCoordinateSpace.ScrollSpace`; the pipeline subtracts `CanvasLayout.ActualOffset`. A wrong coordinate host is a silent, uniform offset bug that shifts every port and link endpoint together.
- A reuse-mode `ItemsControl` hands containers out lazily; the enumerator branch reads containers through `ItemContainerGenerator.ContainerFromIndex` and walks down to the element carrying the slot.

## Class: WorkflowLinkBounds

`public static class WorkflowLinkBounds`

Grows and moves a self-drawing element's layout box so it covers everything it draws.

### Members

| Signature / member | Type | Description |
| --- | --- | --- |
| `BoxPad` | `double` (const `6`) | How far the box grows past the drawn extent, in canvas units. |
| `Apply(FrameworkElement view, IReadOnlyList<Point> canvasLocalPoints, out double originX, out double originY)` | `bool` | Moves the box onto the points' bounds; `false` when there is nothing to cover. |

`originX`/`originY` receive the box's left/top edge. Subtract them from the same canvas-local points when drawing. The box is not a hit target; hit testing uses the curve the view publishes to Core.

### Example

```csharp
if (WorkflowLinkBounds.Apply(this, points, out var ox, out var oy))
{
    DrawCurve(graphics, points, ox, oy);
}
// Source: source
```

### Notes

- Jalium's renderer culls a child when its layout box misses the clip and never inspects the drawn content. A curve drawn outside its box is dropped silently; the symptom is links vanishing at deep zoom.
- Because the box moves, the drawing coordinates must be expressed relative to it.
