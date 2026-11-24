# Connection preview

`WorkflowInput` is the one input route per tree. During a connection drag it owns the sender, the candidate receiver and the preview stage; a link view reads that state instead of re-deriving it.

Namespace: `VeloxDev.WorkflowSystem` (types) and `VeloxDev.WorkflowSystem.StandardEx` (the two preview operations).

## ConnectionPreviewState

**Signature:** `enum ConnectionPreviewState`

| Value | Meaning |
| --- | --- |
| `None = 0` | No drag is in progress. |
| `Started = 1` | Sender fixed; the pointer is not over a candidate. |
| `ValidTarget = 2` | Pointer over a slot that could receive. |
| `InvalidTarget = 3` | Pointer over a slot that would be refused. |

## IConnectionPreviewLink

**Signature:** `interface IConnectionPreviewLink : ILinkComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Preview` | `ConnectionPreviewState` | Current drag stage. |
| `SetPreview(ConnectionPreviewState state)` | `void` | Called by `WorkflowInput`; a view model does not call it. |

The capability is kept off `ILinkComponent` so adding it does not break existing implementers. `LinkDefaultViewModel` implements it.

## WorkflowInput

**Signature:** `sealed class WorkflowInput`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowInput(ITreeComponent tree)` | constructor | Creates a route; throws `ArgumentNullException` for null. |
| `For(ITreeComponent tree)` | `WorkflowInput` | The process-wide instance for the tree, created on first use and kept while the tree lives. |
| `Tree` | `ITreeComponent` | The tree this route belongs to. |
| `PointerTarget` | `IWorkflowComponent?` | Component under the pointer, or null over empty canvas. |
| `HoveredLink` | `ILinkComponent?` | `PointerTarget` as a link. |
| `ConnectionSender` | `ISlotComponent?` | The drag's source, or null. |
| `PreviewReceiver` | `ISlotComponent?` | The candidate receiver, or null. |
| `PreviewState` | `ConnectionPreviewState` | Current drag stage. |
| `PreviewCheck` | `ConnectionCheck?` | Check for the candidate; null when there is no candidate. |
| `PreviewChanged` | `EventHandler<ConnectionPreviewEventArgs>` | Raised when sender, candidate or stage changes. |
| `PreviewValidating` | `EventHandler<ConnectionPreviewValidatingEventArgs>` | Raised once per new candidate the framework would accept, and again on an explicit refresh. |
| `HitRadius` | `double` | Hit tolerance for link resolution; defaults to `LinkHitTestEx.DefaultHitRadius`. |
| `IsSuspended` | `bool` | When set, pointer moves no longer update `PointerTarget`. |
| `Scroller` | `IWorkflowSurfaceScroller?` | Adapter-registered wheel-scroll capability. |
| `Navigator` | `IWorkflowSurfaceNavigator?` | Adapter-registered centring capability. |
| `Route(PointerEventArgs e)` | `void` | Routes a pointer event to the target and its ancestors, then applies the framework's default. Throws `ArgumentNullException` for null. |
| `Route(KeyEventArgs e)` | `void` | Routes a key event; keys have no default action in Core. |

`Route` sends a `PointerExited` to the component it left and a `PointerEntered` to the one it arrived at before delivering the event itself. The chain is target → owning node (for a slot) → tree.

## StandardSetPreviewReceiver

**Signature:** `static void StandardSetPreviewReceiver(this ITreeComponent component, ISlotComponent? slot)`

Reports the candidate under the pointer. The sender is never its own candidate. Repeating the same candidate is cheap: the host's validation is not consulted again until the candidate changes. A null `slot` returns the preview to `Started`.

Marks `SlotState.PreviewReceiver` on the candidate and updates the virtual link's `Preview` when it implements `IConnectionPreviewLink`.

## StandardRefreshConnectionPreview

**Signature:** `static void StandardRefreshConnectionPreview(this ITreeComponent component)`

Re-runs the check for the candidate currently under the pointer, bypassing the same-candidate short circuit. Use it when an asynchronous verdict lands after the pointer reached the candidate. A no-op when no drag is in progress.

## ITreeEvents

**Signature:** `interface ITreeEvents`

| Member | Type | Description |
| --- | --- | --- |
| `Connecting` | `EventHandler<ConnectionEventArgs>` | Raised before `ValidateConnection`, so the two compose. |
| `Connected` | `EventHandler<ConnectionEventArgs>` | Raised once the link exists, with the same handle. |
| `RaiseConnecting(ISlotComponent, ISlotComponent)` | `WorkflowEventHandle` | Asks the host and returns the handle for the report. |
| `RaiseConnected(ISlotComponent, ISlotComponent, WorkflowEventHandle)` | `void` | Reports unless the handle stopped propagation. |

`TreeHelper<T>` implements this interface, so `(ITreeEvents)tree.GetHelper()` is the usual cast.

## ITreeEventSink

**Signature:** `interface ITreeEventSink`

| Member | Type | Description |
| --- | --- | --- |
| `OnConnecting(ConnectionEventArgs e)` | `void` | Called before a connection; refuse with the handle. |
| `OnConnected(ConnectionEventArgs e)` | `void` | Called once the link exists. |

The sink is the host-implemented form; `WorkflowEventRelay` is how a platform adapts it.

## ConnectionEventArgs

**Signature:** `sealed class ConnectionEventArgs : EventArgs`

Members: constructor `(ISlotComponent sender, ISlotComponent receiver, WorkflowEventHandle handle)`; read-only `Sender`, `Receiver`, `Handle`.

## ConnectionPreviewEventArgs

**Signature:** `sealed class ConnectionPreviewEventArgs : EventArgs`

Members: constructor `(ISlotComponent? sender, ISlotComponent? receiver, ConnectionPreviewState state, ConnectionCheck? check)`; read-only `Sender`, `Receiver`, `State`, `Check`.

## ConnectionPreviewValidatingEventArgs

**Signature:** `sealed class ConnectionPreviewValidatingEventArgs : EventArgs`

| Member | Type | Description |
| --- | --- | --- |
| `Sender` / `Receiver` | `ISlotComponent` | The drag's source and the candidate. |
| `Check` | `ConnectionCheck` | The current verdict; starts as the framework's. |
| `Reject(string? message = null)` | `void` | Replaces `Check` with `RejectedByHost`. |

A preview may only tighten the framework's rules: a candidate the framework already refused is not offered. The release-time `Connecting` remains the final decision.

## WorkflowEventHandle

**Signature:** `sealed class WorkflowEventHandle`

| Member | Type | Description |
| --- | --- | --- |
| `PreventDefault` | `bool` | On a `…ing` action: refuse it. On routed input: stand the framework's own reaction down. On a `…ed` report: no effect. |
| `StopPropagation` | `bool` | Stop the event travelling further (ancestor chain, or later report subscribers). |

The same handle instance travels with one logical action, so a subscriber on an ancestor or on the report sees what a nearer subscriber decided.

## Example

```csharp
var tree = new TreeDefaultViewModel();
var input = WorkflowInput.For(tree);
input.PreviewChanged += (_, e) =>
    Console.WriteLine($"{e.State} reason={e.Check?.Reason}");

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
var nodeA = new NodeDefaultViewModel();
var nodeB = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(nodeA);
tree.GetHelper().CreateNode(nodeB);
nodeA.CreateSlotCommand.Execute(from);
nodeB.CreateSlotCommand.Execute(to);

tree.GetHelper().SendConnection(from);   // Started
tree.StandardSetPreviewReceiver(to);     // ValidTarget
input.PreviewValidating += (_, e) => e.Reject("policy");
tree.StandardRefreshConnectionPreview(); // InvalidTarget / RejectedByHost
tree.GetHelper().ResetVirtualLink();     // None
```
