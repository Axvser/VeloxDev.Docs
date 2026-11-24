# WorkflowInput and the input relay

`WorkflowInput` is the single input route for one tree. An adapter translates its platform's pointer or key input into the standard argument types and calls `Route`; the route delivers the same argument instance to the target, then its ancestors, then the tree. `IInputEvents` is the optional helper capability that carries the per-component relay.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## WorkflowInput

**Signature:** `sealed class WorkflowInput`

| Member | Type | Description |
| --- | --- | --- |
| `WorkflowInput(ITreeComponent tree)` | constructor | Creates a route. Throws `ArgumentNullException` when `tree` is null. |
| `For(ITreeComponent tree)` | `static WorkflowInput` | Returns the one route for `tree`, created on first use and kept by a `ConditionalWeakTable`. |
| `Tree` | `ITreeComponent` | The tree this route belongs to. |
| `PointerTarget` | `IWorkflowComponent?` | The component the pointer is on; `null` over empty canvas. Maintained unless `IsSuspended` is set. |
| `HoveredLink` | `ILinkComponent?` | `PointerTarget` as a link, or `null`. |
| `ConnectionSender` | `ISlotComponent?` | The port a connection drag started from. |
| `PreviewReceiver` | `ISlotComponent?` | The candidate port under the pointer during a drag. |
| `PreviewState` | `ConnectionPreviewState` | The current stage of the connection drag. |
| `PreviewCheck` | `ConnectionCheck?` | The check for the candidate; invalid candidates still carry a check. |
| `PreviewChanged` | `event EventHandler<ConnectionPreviewEventArgs>` | Raised when the sender, candidate or stage changes. |
| `PreviewValidating` | `event EventHandler<ConnectionPreviewValidatingEventArgs>` | Raised once for a framework-valid candidate; a subscriber may refuse it for this preview only. |
| `HitRadius` | `double` | Reach either side of a link curve for hit-testing; defaults to `LinkHitTestEx.DefaultHitRadius` (6). |
| `IsSuspended` | `bool` | Stops pointer movement from updating `PointerTarget`, for a host popup. |
| `Scroller` | `IWorkflowSurfaceScroller?` | Registered by an attached adapter; `null` when detached. |
| `Navigator` | `IWorkflowSurfaceNavigator?` | Registered by an attached adapter; `null` when detached. |
| `Route(PointerEventArgs e)` | `void` | Delivers a pointer event to the target and its ancestors, then applies the framework's own reaction. |
| `Route(KeyEventArgs e)` | `void` | Delivers a key event; Core has no default key action. |

Both `Route` overloads throw `ArgumentNullException` for a null argument.

### Routing order

`Route(PointerEventArgs)` does three things in order:

1. If the pointer changed component, it bubbles a `PointerExitedEventArgs` to the previous component and a `PointerEnteredEventArgs` to the new one. Those are independent actions, each with its own `WorkflowEventHandle`.
2. It bubbles the argument through `target → target's node (for a slot) → tree`.
3. Unless `PreventDefault` was set, it records the new `PointerTarget` (unless `IsSuspended`).

A key event bubbles the same chain but has no default reaction. The tree is always the last element of the chain, so a tree-level `KeyDown` handler hears every routed key whichever component was the target.

```csharp
var input = WorkflowInput.For(tree);

if (tree.GetHelper() is IInputEvents events)
{
    events.Input.KeyDown += (_, e) =>
    {
        if (e.Key == InputKey.Delete && e.Target is ILinkComponent link)
        {
            link.DeleteCommand.Execute(null);
            e.Handle.PreventDefault = true;
        }
    };
}
```

**Expected result:** a key pressed while any component is the pointer target reaches the tree's relay, and the handler can refuse further routing with `StopPropagation`.

## IInputEvents

**Signature:** `interface IInputEvents`

| Member | Type | Description |
| --- | --- | --- |
| `Input` | `InputRelay` | The events this component receives while an input event routed through it. |

The interface is separate from the helper interfaces so an existing helper implementer does not break, and a helper that does not want input need not answer for it. Helpers derived from `NodeHelper<T>` and its siblings already implement it.

## InputRelay

**Signature:** `sealed class InputRelay`

| Event | Argument |
| --- | --- |
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>` |
| `PointerExited` | `EventHandler<PointerExitedEventArgs>` |
| `PointerMoved` | `EventHandler<PointerMovedEventArgs>` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>` |
| `PointerWheelChanged` | `EventHandler<PointerWheelEventArgs>` |
| `KeyDown` | `EventHandler<KeyDownEventArgs>` |
| `KeyUp` | `EventHandler<KeyUpEventArgs>` |

The `sender` is the relay, which is how a subscriber tells which element of the route it is hearing from. One argument instance is raised once per level of the route.

## WorkflowEventHandle

**Signature:** `sealed class WorkflowEventHandle`

| Member | Type | Description |
| --- | --- | --- |
| `PreventDefault` | `bool` | Refuses a `…ing` model action, or stands down the framework's own action on routed input. On a `…ed` report it has no effect. |
| `StopPropagation` | `bool` | On routed input, no ancestor hears it; on a `…ed` report, later subscribers do not. The framework's own handling is unaffected. |

One handle travels with one logical action, not one per event, so a subscriber further along the route can read what a nearer subscriber decided.

```csharp
input.Route(new PointerWheelEventArgs(
    new Anchor(120, 80, 0),
    InputModifiers.Shift,
    source: null,
    target: tree.Nodes[0],
    deltaX: 0d,
    deltaY: 120d,
    handle: new WorkflowEventHandle()));
```

**Expected result:** the wheel argument reaches the node's relay and then the tree's relay; a handler that sets `PreventDefault` makes the adapter skip its own scroll for that notch.
