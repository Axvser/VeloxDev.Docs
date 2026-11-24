# Event sinks

Input is the pointer and keyboard route; a **sink** is the other direction — a host object that receives a component's model events because markup cannot subscribe to an event handler directly. An adapter exposes a `WorkflowEvents` attached property that installs a sink on a node, slot or tree.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`. The attached properties are in each adapter's `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## INodeEventSink

**Signature:** `interface INodeEventSink`

| Member | Signature | Description |
| --- | --- | --- |
| `OnMoving` / `OnMoved` | `void (NodeMoveEventArgs e)` | Before and after the node is placed. |
| `OnResizing` / `OnResized` | `void (NodeResizeEventArgs e)` | Before and after the size changes. |
| `OnDeleting` / `OnDeleted` | `void (NodeEventArgs e)` | Before and after the node is torn down. |

## ISlotEventSink

**Signature:** `interface ISlotEventSink`

| Member | Signature | Description |
| --- | --- | --- |
| `OnChannelChanging` | `void (SlotChannelEventArgs e)` | Before the slot's channel changes; refuse via the handle. |
| `OnChannelChanged` | `void (SlotChannelEventArgs e)` | After the change. |

## ITreeEventSink

**Signature:** `interface ITreeEventSink`

| Member | Signature | Description |
| --- | --- | --- |
| `OnConnecting` | `void (ConnectionEventArgs e)` | Before a connection is made; refuses that drag through the handle. |
| `OnConnected` | `void (ConnectionEventArgs e)` | Once the link exists. |

Each method receives the same argument object the helper's own event carries, so the `WorkflowEventHandle` travels with it. Setting `PreventDefault` in an `On…ing` method refuses that one action. The methods run synchronously; a sink that blocks blocks the interaction. `OnConnecting` composes with `ITreeHelper.ValidateConnection`: the connection happens only when neither refuses.

```csharp
sealed class TreeSink : ITreeEventSink
{
    public void OnConnecting(ConnectionEventArgs e)
    {
        if (e.Sender.Parent != e.Receiver.Parent) e.Handle.PreventDefault = true;
    }

    public void OnConnected(ConnectionEventArgs e) { }
}
```

**Expected result:** a `WorkflowEvents.SetTree(host, sink)` attached to the graph host invokes `OnConnecting` before the link is created, and refusing it cancels that drag.
