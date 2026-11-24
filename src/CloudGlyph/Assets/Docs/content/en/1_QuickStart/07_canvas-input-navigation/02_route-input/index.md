# Route input

Core routes input; it never acts on it. A key press, a wheel turn or a pointer move is delivered to the helper of the component under the pointer, then to that component's ancestors, then to the tree. Subscribing means subscribing to one component's `InputRelay`; cancelling means writing the one `WorkflowEventHandle` that travels with the event.

## One route per tree

`WorkflowInput.For(tree)` returns the same instance for the same tree for as long as the tree lives. An adapter forwards into it; a host reads the current pointer target and scroll capabilities from it.

```csharp
var input = WorkflowInput.For(tree);

// Read-only state the route maintains.
IWorkflowComponent? under = input.PointerTarget;   // null over empty canvas
ILinkComponent? hovered = input.HoveredLink;

// Optional capabilities registered by an attached adapter.
IWorkflowSurfaceScroller? scroller = input.Scroller;
IWorkflowSurfaceNavigator? navigator = input.Navigator;
```

The route owns exactly one piece of state — which component the pointer is on. Everything else a host might expect (selection, hover paint, deleting) belongs to the host.

## Subscribe on a helper

Every default helper implements `IInputEvents`. The tree helper, node helper, slot helper and link helper all expose the same `InputRelay`.

```csharp
if (tree.GetHelper() is not IInputEvents events) return;

events.Input.KeyDown += OnKeyDown;
events.Input.PointerWheelChanged += OnWheel;
```

The event arguments are concrete subclasses of `PointerEventArgs` and `KeyEventArgs`:

| Event | Argument | Extra members |
|---|---|---|
| `PointerEntered` / `PointerExited` / `PointerMoved` | `PointerEnteredEventArgs` / `PointerExitedEventArgs` / `PointerMovedEventArgs` | — |
| `PointerPressed` / `PointerReleased` | `PointerPressedEventArgs` / `PointerReleasedEventArgs` | `Button`, `ClickCount` |
| `PointerWheelChanged` | `PointerWheelEventArgs` | `DeltaX`, `DeltaY` |
| `KeyDown` / `KeyUp` | `KeyDownEventArgs` / `KeyUpEventArgs` | `Key`, `RawKeyCode`, `IsRepeat` |

Every argument carries `Position`, `Modifiers`, `Source` (the view), `Target` (the component, or `null` for empty canvas) and `Handle`. `Target` is the original target at every hop — an ancestor does not see itself.

## Cancel, don't reimplement

`WorkflowEventHandle` has two independent flags:

- `PreventDefault` — the framework's own reaction does not run. On a routed pointer or key event that reaction belongs to the adapter (a wheel scroll, a pan, a node drag, a connection drag). On a model `…ing` event it refuses the action outright.
- `StopPropagation` — the event stops here; no ancestor helper hears it.

One handle travels with one action, so a subscriber closer to the target and one on the tree read the same instance. The default (neither flag set) changes nothing.

```csharp
private void OnKeyDown(object? sender, KeyDownEventArgs e)
{
    if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;
    if (_tree is not { } tree) return;

    var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
    if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
    else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
    else return;

    e.Handle.PreventDefault = true;
}
```

Node drag and slot connection are *not* model actions and are not undoable by design. A `Ctrl+Z` after a drag undoes the most recent structural edit, not the drag; to make a drag undoable, submit your own `IActionPair` through `tree.GetHelper().Submit(...)`.

## The wheel is the adapter's, until you take it

The adapter keeps the platform scroll container from scrolling the workflow surface and applies the scroll itself. A plain wheel therefore keeps doing the default vertical scroll. If a subscriber sets `PreventDefault`, that wheel turn does not scroll, and the subscriber decides where it goes through `WorkflowInput.Scroller`.

```csharp
// Horizontal scrolling on Shift+wheel, exactly as the WPF Trimmed demo writes it.
private void OnWheel(object? sender, PointerWheelEventArgs e)
{
    if (!e.Modifiers.HasFlag(InputModifiers.Shift) || _tree is not { } tree) return;

    e.Handle.PreventDefault = true;

    // Vertical positive is "away from the user"; the horizontal axis positive is "right".
    // The two axes are not the same physical direction, so the sign is flipped here.
    WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
}
```

Read `e.Modifiers`, not the keyboard state. The modifiers travel with the wheel event and do not depend on which element has keyboard focus; tracking `Shift` through `KeyDown`/`KeyUp` instead makes Shift+wheel fail whenever the surface is not focused.

## Delete and other keys

Core has no default key action. The adapter routes the key, and the host decides:

```csharp
events.Input.KeyDown += (_, e) =>
{
    if (e.Key != InputKey.Delete || e.Handle.PreventDefault) return;
    if (e.Target is not ILinkComponent link || !link.DeleteCommand.CanExecute(null)) return;
    link.DeleteCommand.Execute(null);
};
```

The key's `Target` is whatever component the pointer is on: a key has no position of its own. A tree-level key such as `Ctrl+Z` still reaches the tree when the pointer is over blank canvas, because the chain always ends at the tree.

## Pointer enter and exit

When the pointer moves onto a different component, the route first raises `PointerExited` for the one it left and `PointerEntered` for the one it arrived at, each with its own handle. A component view can subscribe only to its own helper to hear its whole hover — it does not have to compare targets on every move.

## Expected result

- `Ctrl+Z` / `Ctrl+Y` undo and redo structural edits while the pointer is anywhere on the surface.
- `Shift` + wheel scrolls horizontally; plain wheel scrolls vertically.
- `Delete` over a link deletes it; over a node it does nothing unless you write that handler.
- Setting `e.Handle.PreventDefault` in your press handler keeps the adapter from panning or dragging for that one press.

## Next

[Navigation](../03_navigate/index.md) covers the built-in gestures and the two navigation capabilities.
