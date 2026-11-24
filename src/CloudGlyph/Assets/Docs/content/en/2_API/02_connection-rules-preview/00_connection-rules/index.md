# Connection rules

The rule set is pure and shared by the preview and the release path. Channels decide direction and capacity; the check names the first rule that refuses a pair.

Namespace: `VeloxDev.WorkflowSystem` (types) and `VeloxDev.WorkflowSystem.StandardEx` (operations).

## ConnectionRejectReason

**Signature:** `enum ConnectionRejectReason`

| Value | Meaning |
| --- | --- |
| `None = 0` | The check passed. |
| `SenderCannotSend = 1` | The sender's channel has no outgoing direction. |
| `ReceiverCannotReceive = 2` | The receiver's channel has no incoming direction. |
| `SameNode = 3` | Both ports belong to the same node. |
| `RejectedByRule = 4` | `ITreeHelper.ValidateConnection` returned `false`. |
| `RejectedByHost = 5` | A `WorkflowInput.PreviewValidating` subscriber refused this preview. |

## ConnectionCheck

**Signature:** `readonly struct ConnectionCheck : IEquatable<ConnectionCheck>`

| Member | Type | Description |
| --- | --- | --- |
| `Valid` | `ConnectionCheck` | A passing check. |
| `IsValid` | `bool` | Whether the rules accept the pair. |
| `Reason` | `ConnectionRejectReason` | Why it failed, or `None`. |
| `Message` | `string?` | Optional host explanation; null for framework reasons. |
| `Rejected(ConnectionRejectReason reason, string? message = null)` | `ConnectionCheck` | Creates a failing check. |
| `Equals(ConnectionCheck)` / `Equals(object?)` / `GetHashCode()` | | Value semantics. |
| `ToString()` | `string` | `Valid`, `Rejected(Reason)` or `Rejected(Reason: message)`. |

Capacity is **not** a rejection: completing a connection cleans up existing links according to the channel, so a passing check means "acceptable, possibly after that cleanup".

## SlotChannel

**Signature:** `[Flags] enum SlotChannel : int`

| Value | Bits | Meaning |
| --- | --- | --- |
| `None = 0` | — | No connection allowed. |
| `OneTarget = 1` | outgoing | One outgoing link. |
| `OneSource = 2` | incoming | One incoming link. |
| `OneBoth = 3` | both, one each | One in each direction. |
| `MultipleTargets = 4` | outgoing | Any number of outgoing links. |
| `MultipleSources = 8` | incoming | Any number of incoming links. |
| `MultipleBoth = 12` | both, any | Any number in each direction. |

The generated slot starts at `MultipleBoth`; the default view model starts at `OneBoth`.

## SlotState

**Signature:** `[Flags] enum SlotState : int`

| Value | Meaning |
| --- | --- |
| `StandBy = 1` | No connection, no drag. |
| `PreviewSender = 2` | This slot is the sender of an in-progress drag. |
| `PreviewReceiver = 4` | This slot is the candidate receiver under the pointer. |
| `Sender = 8` | Has at least one outgoing link. |
| `Receiver = 16` | Has at least one incoming link. |

`Sender` and `Receiver` combine. The preview bits are owned by `WorkflowInput`, not by the connection lists.

## StandardCheckConnection

**Signature:** `static ConnectionCheck StandardCheckConnection(this ITreeComponent component, ISlotComponent sender, ISlotComponent receiver)`

Pure query: no events, no state changes, no preview. Tests in order: sender can send, receiver can receive, different parent nodes, then `component.GetHelper().ValidateConnection`.

| Parameter | Type | Description |
| --- | --- | --- |
| `component` | `ITreeComponent` | The tree owning both slots. |
| `sender` | `ISlotComponent` | Proposed source. |
| `receiver` | `ISlotComponent` | Proposed destination. |

**Returns:** `ConnectionCheck` — the first refusal, or `Valid`.

**Exceptions:** `ArgumentNullException` for any null argument.

The method deliberately does not raise `ITreeEvents.Connecting`; that event is a per-attempt veto on release only.

## StandardSendConnection

**Signature:** `static void StandardSendConnection(this ITreeComponent component, ISlotComponent slot)`

Starts a connection drag from `slot`. If the slot cannot be a sender, the virtual link is reset. Otherwise it cleans up the sender's existing connections according to its channel, copies the slot anchor to both ends of `VirtualLink`, sets `IsVisible = true`, marks `SlotState.PreviewSender` and records the sender on `WorkflowInput.For(component)`. A slot not attached to a tree calls `WorkflowGuard.Fail`.

## StandardReceiveConnection

**Signature:** `static void StandardReceiveConnection(this ITreeComponent component, ISlotComponent slot)`

Completes the drag at `slot`. The order is: receiver capability, `ITreeEvents.Connecting` (a handle with `PreventDefault` resets the drag and stops), the same rule set with the sender check skipped, same-direction cleanup, receiver-channel cleanup, link creation as one undo entry, `Connected`, reset.

If no drag is in progress (`WorkflowInput.ConnectionSender` is null) the call is a no-op.

## StandardResetVirtualLink

**Signature:** `static void StandardResetVirtualLink(this ITreeComponent component)`

Hides the virtual link, moves both ends to `Anchor(NaN, NaN, 0)` and clears the input route's drag state and preview bits.

## Cleanup semantics

Completing a connection removes what the channel disallows, as part of the same logical operation:

- a sender whose channel has `OneTarget` or `OneBoth` drops its previous outgoing links;
- a receiver whose channel has `OneSource` or `OneBoth` drops its previous incoming links;
- a link already joining the same two nodes in the same direction is replaced by the newest;
- all removals are submitted as undo entries, so undoing the new connection also restores what it displaced.

## Example

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel();
var b = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
a.CreateSlotCommand.Execute(from);
b.CreateSlotCommand.Execute(to);

from.SetChannelCommand.Execute(SlotChannel.OneTarget);
to.SetChannelCommand.Execute(SlotChannel.OneSource);

Console.WriteLine(tree.StandardCheckConnection(from, to)); // Valid
Console.WriteLine(tree.StandardCheckConnection(from, from)); // Rejected(SameNode)

tree.GetHelper().SendConnection(from);
tree.GetHelper().ReceiveConnection(to);
Console.WriteLine(tree.Links.Count); // 1
```
