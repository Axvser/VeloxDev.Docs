# Workflow System — Design Patterns — Connection Preview

The connection drag preview is a small **Chain of Rules** with a **host policy hook**. It is not a second connection implementation: the preview and the completed connection run the same rule set, so they cannot disagree about whether a pair is legal.

## The rule chain

`StandardCheckConnection` is pure — no events, no state changes — and returns the first refusal:

| Order | Rule | Rejection reason |
|---|---|---|
| 1 | `sender.StandardCanBeSender()` — the channel allows an outgoing direction | `SenderCannotSend` |
| 2 | `receiver.StandardCanBeReceiver()` — the channel allows an incoming direction | `ReceiverCannotReceive` |
| 3 | `sender.Parent != receiver.Parent` | `SameNode` |
| 4 | `IWorkflowTreeViewModelHelper.ValidateConnection(sender, receiver)` | `RejectedByRule` |

Channel **capacity** is deliberately missing: completing a connection cleans up existing links according to the channel first, so "at capacity" is not a refusal, it is "acceptable after that cleanup". The result is a `ConnectionCheck` — `IsValid`, `Reason`, optional `Message`.

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:195-216
public static ConnectionCheck StandardCheckConnection(
    this IWorkflowTreeViewModel component,
    IWorkflowSlotViewModel sender,
    IWorkflowSlotViewModel receiver)
{
    if (component is null) throw new ArgumentNullException(nameof(component));
    if (sender is null) throw new ArgumentNullException(nameof(sender));
    if (receiver is null) throw new ArgumentNullException(nameof(receiver));

    if (!sender.StandardCanBeSender())
        return ConnectionCheck.Rejected(ConnectionRejectReason.SenderCannotSend);

    if (!receiver.StandardCanBeReceiver())
        return ConnectionCheck.Rejected(ConnectionRejectReason.ReceiverCannotReceive);

    if (ReferenceEquals(sender.Parent, receiver.Parent))
        return ConnectionCheck.Rejected(ConnectionRejectReason.SameNode);

    return component.GetHelper().ValidateConnection(sender, receiver)
        ? ConnectionCheck.Valid
        : ConnectionCheck.Rejected(ConnectionRejectReason.RejectedByRule);
}
```

## The host hook tightens, never relaxes

After the framework check passes, `SetPreviewReceiver` offers the candidate to `WorkflowInput.PreviewValidating`. A subscriber can call `Reject(message)`, which replaces the check with `RejectedByHost`. A candidate the framework already refused is never offered — that asymmetry is the contract: *a preview may make a green candidate red, never a red one green.*

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:194-203
internal ConnectionCheck RaisePreviewValidating(
    IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver, ConnectionCheck check)
{
    var handler = PreviewValidating;
    if (handler is null) return check;

    var args = new ConnectionPreviewValidatingEventArgs(sender, receiver, check);
    handler.Invoke(this, args);
    return args.Check;
}
```

The release-time decision is still `IWorkflowTreeEvents.Connecting` plus `ValidateConnection`; the preview is advisory. That is why `ConnectionCheck` has no concept of a host veto that survives the drag: refusing one candidate for the preview does not cancel the connection — it only paints that candidate red while the pointer is on it.

## State ownership: the drag, not the connection lists

The two preview bits are part of `SlotState`, but they are **not** derived from `Targets` / `Sources`. `StandardUpdateState` recomputes the connection bits and preserves the preview bits:

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSlotEx.cs:91-106
public static void StandardUpdateState(this IWorkflowSlotViewModel component)
{
    bool hasOutgoingConnections = component.Targets.Count > 0;
    bool hasIncomingConnections = component.Sources.Count > 0;

    var preview = component.State & (SlotState.PreviewSender | SlotState.PreviewReceiver);
    component.State = preview | ((hasOutgoingConnections, hasIncomingConnections) switch
    {
        (true, false) => SlotState.Sender,
        (false, true) => SlotState.Receiver,
        (true, true) => SlotState.Sender | SlotState.Receiver,
        (false, false) => SlotState.StandBy,
    });
}
```

Without that preservation, completing or removing an unrelated connection during a drag would silently clear the sender's / candidate's preview mark, and the renderer would lose its highlight mid-gesture.

## Deduplication and asynchronous validation

`StandardSetPreviewReceiver` short-circuits when the **candidate reference** is unchanged (`SetPreviewReceiver` returns before recomputing the check), so moving inside one slot does not re-run the host's validation every frame; `WorkflowInput.SetConnectionPreview` adds a second no-op guard on state + check. `StandardRefreshConnectionPreview` bypasses the candidate guard — it is the entry for asynchronous work: start the check from `PreviewValidating`, let the drag continue, and call refresh when the verdict lands. The design keeps the synchronous path cheap and gives the asynchronous path an explicit "re-check now" door.

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:162-174
public static void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)
{
    if (component is null) return;

    var input = WorkflowInput.For(component);
    if (input.ConnectionSender is null)
    {
        input.ClearConnectionPreview();
        return;
    }

    SetPreviewReceiver(component, input.PreviewReceiver, force: true);
}
```

## Why the stage lives on the virtual link

`IConnectionPreviewLink` is an optional capability interface, kept off `IWorkflowLinkViewModel` for the same reason as the other optional event interfaces: adding a member there would break every implementer. `LinkDefaultViewModel` implements it; a custom virtual link may too. `WorkflowInput.SetPreviewState` writes the stage through this interface, so a link view can paint `Started` / `ValidTarget` / `InvalidTarget` without polling `WorkflowInput` — and a host that prefers an event subscribes to `PreviewChanged`, which carries the same snapshot.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardEx/WorkflowSlotEx.cs`, `GUI/Events/WorkflowInput.cs`, `Interfaces/WorkflowSystem/ConnectionCheck.cs`, `Interfaces/WorkflowSystem/IConnectionPreviewLink.cs`, `GUI/Events/Tree/ConnectionPreviewEventArgs.cs`, `GUI/Events/Tree/ConnectionPreviewValidatingEventArgs.cs`. Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs`. Demo: `Examples/Workflow/Avalonia/Demo/Views/Workflow/BezierCurveView.axaml.cs` paints the three stages.*
