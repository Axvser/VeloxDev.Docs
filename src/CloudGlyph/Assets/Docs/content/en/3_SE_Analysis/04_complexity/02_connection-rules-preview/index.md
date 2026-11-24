# Connection rules and preview

A connection attempt has two very different costs. The legality check and the drag-time preview are constant-time flag and reference tests. Actually committing the connection is where the work is: it may have to clear conflicting links, and some cleanup modes scan every sender in the map or every slot pair across two nodes.

Notation: $U$ distinct sender slots in `LinksMap`, $d$ degree of one slot, $S_s$ and $S_r$ slots on the sender and receiver nodes, $L$ links.

## Cost model

| Operation | Time | Source |
|---|---|---|
| `StandardCheckConnection` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:202` |
| `StandardSetPreviewReceiver`, same candidate | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:157` |
| `StandardRefreshConnectionPreview` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:169` |
| `StandardSendConnection` | $O(U + d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:111` |
| `StandardReceiveConnection` | $O(S_s S_r + U + d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:271` |
| `StandardResetVirtualLink` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:317` |
| `StandardSetChannel` | $O(d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSlotEx.cs:19` |

The check is genuinely constant: two flag tests, a parent reference comparison, and one host rule call.

```csharp
if (checkSender && !sender.StandardCanBeSender())
    return ConnectionCheck.Rejected(ConnectionRejectReason.SenderCannotSend);
...
if (ReferenceEquals(sender.Parent, receiver.Parent))
    return ConnectionCheck.Rejected(ConnectionRejectReason.SameNode);
...
return component.GetHelper().ValidateConnection(sender, receiver)
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:222-231`

The default `ValidateConnection` returns `true` in constant time, so the host rule does not change the bound unless a host overrides it. That override is the only *inferred* cost in this page.

## Preview is deduplicated per pointer move

Dragging fires a preview update for every pointer move. The implementation short-circuits when the candidate has not changed, so the common case is one reference comparison:

```csharp
if (!force && ReferenceEquals(input.PreviewReceiver, slot)) return;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:255`

Only when the candidate changes does it write slot state flags, recompute the preview state, and raise the event. That keeps a drag at $O(1)$ per move.

## Committing can be quadratic in slots

The expensive path is the "same direction" cleanup, which compares every slot of the sender node against every slot of the receiver node:

```csharp
foreach (var potentialSender in senderNode.Slots)
{
    if (component.LinksMap.TryGetValue(potentialSender, out var targetLinks))
    {
        foreach (var potentialReceiver in receiverNode.Slots)
        {
            if (targetLinks.TryGetValue(potentialReceiver, out var existingLink))
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:494-500`

That is the $S_s S_r$ term. The `OneBoth` cleanup mode instead scans the outer `LinksMap`, giving the $U$ term. The full bound is therefore:

$$
T_{\text{receive}} = O(S_s S_r + U + d)
$$

Sending is cheaper because it cleans only around the sender: $O(U + d)$. In a bounded-degree graph — a few slots per node — every term is constant in the size of the graph, and the nested product is small. The quadratic shape only appears on nodes with many ports.

## Memory

The live preview state is a fixed handful of fields per tree, created lazily through a `ConditionalWeakTable`. A cleanup batch allocates one `List<(ISlotComponent, ISlotComponent, ILinkComponent)>` sized by $d$ or $U$ for the duration of the call, and each preview change allocates one `ConnectionCheck` value and one event-args object. Nothing accumulates across attempts.
