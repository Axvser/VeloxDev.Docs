# Workflow events

`WorkflowEvents` installs a Core model-event sink on a WinUI element through three attached properties.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WinUI`.

## WorkflowEvents

**Signature:** `static class WorkflowEvents`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `Node` | `INodeEventSink?` | `null` | Receives the bound node's move, resize and delete events. |
| `Slot` | `ISlotEventSink?` | `null` | Receives the bound slot's channel events. |
| `Tree` | `ITreeEventSink?` | `null` | Receives the bound tree's connection events. |

Accessors: `GetNode` / `SetNode`, `GetSlot` / `SetSlot`, `GetTree` / `SetTree`, all taking a `DependencyObject`.

The behavior watches `DataContext`; when it becomes an `INodeComponent`, `ISlotComponent` or `ITreeComponent`, the matching helper's events are forwarded to the sink. A sink method receives the helper's own argument, including the `WorkflowEventHandle`.

```xml
<Grid behaviors:WorkflowEvents.Node="{Binding NodeSink}"
      behaviors:WorkflowEvents.Tree="{Binding TreeSink}" />
```

**Expected result:** a node view with a `Node` sink hears `OnMoving` before placement and `OnMoved` after; `e.Handle.PreventDefault` in `OnMoving` pins the node.
