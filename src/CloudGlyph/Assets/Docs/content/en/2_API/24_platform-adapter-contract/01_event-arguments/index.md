# Input event arguments

An adapter constructs one argument per action and passes it to `WorkflowInput.Route`. Every argument carries the position or key, the modifiers, the source view, the target component and the `WorkflowEventHandle` shared with the whole route. The base constructors are `protected`; the concrete subclasses are what an adapter instantiates.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## PointerEventArgs

**Signature:** `abstract class PointerEventArgs : EventArgs`

| Member | Type | Description |
| --- | --- | --- |
| `Position` | `Anchor` | Where the pointer is, layer included. |
| `Modifiers` | `InputModifiers` | Modifier keys held. |
| `Source` | `object?` | The view the input came from, or `null` when the platform has none. |
| `Target` | `IWorkflowComponent?` | The component the pointer is on, or `null` for empty canvas. |
| `Handle` | `WorkflowEventHandle` | The handle for this action. |

**Protected signature:** `PointerEventArgs(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)`

### Concrete pointer arguments

| Type | Constructor | Extra members |
| --- | --- | --- |
| `PointerEnteredEventArgs` | `(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)` | — |
| `PointerExitedEventArgs` | same five parameters | — |
| `PointerMovedEventArgs` | same five parameters | — |
| `PointerPressedEventArgs` | `(Anchor, InputModifiers, object?, IWorkflowComponent?, MouseButton button, int clickCount, WorkflowEventHandle)` | `Button` (`MouseButton`), `ClickCount` (`int`) |
| `PointerReleasedEventArgs` | same as pressed | `Button`, `ClickCount` |
| `PointerWheelEventArgs` | `(Anchor, InputModifiers, object?, IWorkflowComponent?, double deltaX, double deltaY, WorkflowEventHandle)` | `DeltaX`, `DeltaY` (`double`) |

`PointerWheelEventArgs.DeltaX` is positive towards the right; `DeltaY` is positive away from the user. A mouse without a tilt wheel reports `DeltaX == 0`.

```csharp
var pressed = new PointerPressedEventArgs(
    new Anchor(120, 80, 0), InputModifiers.None, source: view, target: node,
    MouseButton.Left, clickCount: 1, new WorkflowEventHandle());

input.Route(pressed);
```

**Expected result:** the node's `PointerPressed` subscriber runs before the tree's, and both see the same `pressed` instance.

## KeyEventArgs

**Signature:** `abstract class KeyEventArgs : EventArgs`

| Member | Type | Description |
| --- | --- | --- |
| `Key` | `InputKey` | The key, or `InputKey.Unknown` when the enum does not name it. |
| `RawKeyCode` | `int` | The platform's own key code; not comparable across adapters. |
| `Modifiers` | `InputModifiers` | Modifier keys held; precise even when `Key` is `Unknown`. |
| `IsRepeat` | `bool` | Whether the platform reports an auto-repeat. |
| `Source` | `object?` | The view that had keyboard focus, or `null`. |
| `Target` | `IWorkflowComponent?` | The component the adapter applies this key to. |
| `Handle` | `WorkflowEventHandle` | The handle for this action. |

**Protected signature:** `KeyEventArgs(InputKey key, int rawKeyCode, InputModifiers modifiers, bool isRepeat, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)`

| Concrete type | Constructor |
| --- | --- |
| `KeyDownEventArgs` | `(InputKey key, int rawKeyCode, InputModifiers modifiers, bool isRepeat, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)` |
| `KeyUpEventArgs` | same seven parameters |

```csharp
var down = new KeyDownEventArgs(
    InputKey.Delete, rawKeyCode: 0, InputModifiers.None, isRepeat: false,
    source: view, target: link, new WorkflowEventHandle());

input.Route(down);
```

**Expected result:** `KeyDown` reaches the link's relay, then the tree's; Core performs no deletion of its own.
