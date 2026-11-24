# Workflow events

`WorkflowEvents` installs a model-event sink on an element through three attached properties. It is the WPF spelling of the Core sink contracts; the interface definitions live in the platform adapter contract, not in this assembly.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WPF`.

## WorkflowEvents

**Signature:** `static class WorkflowEvents`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `Node` | `INodeEventSink?` | `null` | Receives the bound node's move, resize and delete events. |
| `Slot` | `ISlotEventSink?` | `null` | Receives the bound slot's channel events. |
| `Tree` | `ITreeEventSink?` | `null` | Receives the bound tree's connection events. |

Accessors: `GetNode` / `SetNode`, `GetSlot` / `SetSlot`, `GetTree` / `SetTree`, all taking a `DependencyObject` and returning or accepting the sink interface.

The behavior observes the element's `DataContext`: when it becomes an `INodeComponent`, `ISlotComponent` or `ITreeComponent`, the matching helper's events are forwarded to the sink. The sink methods receive the same argument object the helper raises, including the `WorkflowEventHandle`, so an `On…ing` method can refuse one action.

```xml
<Grid behaviors:WorkflowEvents.Node="{Binding NodeSink}"
      behaviors:WorkflowEvents.Slot="{Binding SlotSink}"
      behaviors:WorkflowEvents.Tree="{Binding TreeSink}" />
```

**Expected result:** a node view that names a `Node` sink hears `OnMoving` before the node is placed and `OnMoved` after; setting `e.Handle.PreventDefault` in `OnMoving` pins the node.
