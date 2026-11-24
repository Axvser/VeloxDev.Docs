# Input enumerations

Three small enumerations keep input identical across adapters: the key identity, the modifier flags, and the mouse button. An adapter maps its native values onto these; a host never sees a platform enum.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## InputKey

**Signature:** `enum InputKey`

| Group | Members |
| --- | --- |
| Unmapped / control | `Unknown = 0`, `None = 1`, `Cancel = 2`, `Back = 3`, `Tab = 4`, `Enter = 5`, `Escape = 6`, `Space = 7` |
| Navigation | `PageUp = 8`, `PageDown = 9`, `End = 10`, `Home = 11`, `Left = 12`, `Up = 13`, `Right = 14`, `Down = 15`, `Insert = 16`, `Delete = 17` |
| Modifier keys | `LeftShift = 18`, `RightShift = 19`, `LeftCtrl = 20`, `RightCtrl = 21`, `LeftAlt = 22`, `RightAlt = 23`, `LWin = 24`, `RWin = 25` |
| Letters | `A = 30` through `Z = 55` (contiguous) |
| Digits | `D0 = 60` through `D9 = 69` (contiguous) |
| Function keys | `F1 = 80` through `F12 = 91` (contiguous) |

An adapter that cannot name a key reports `Unknown` and still supplies the real code in `KeyEventArgs.RawKeyCode`.

## InputModifiers

**Signature:** `[Flags] enum InputModifiers`

| Member | Value |
| --- | --- |
| `None` | `0` |
| `Alt` | `1` |
| `Control` | `2` |
| `Shift` | `4` |
| `Meta` | `8` |

Modifier state is always precise, even when `Key` is `Unknown`, so Ctrl plus an unmapped key is still distinguishable.

```csharp
if (e.Modifiers.HasFlag(InputModifiers.Control) && e.Key == InputKey.Z)
{
    tree.UndoCommand.Execute(null);
    e.Handle.PreventDefault = true;
}
```

**Expected result:** a Ctrl+Z key event is matched by the flag test and reaches the tree's relay; the host decides the action.

## MouseButton

**Signature:** `enum MouseButton`

| Member | Value | Meaning |
| --- | --- | --- |
| `None` | `0` | No button — a move, or a device that cannot say. |
| `Left` | `1` | Primary button. |
| `Right` | `2` | Secondary button, commonly the context-menu button. |
| `Middle` | `3` | Middle button. |
| `XButton1` | `4` | First extended button. |
| `XButton2` | `5` | Second extended button. |

The name is prefixed by the enclosing namespace (`VeloxDev.WorkflowSystem.MouseButton`) because adapter files also import a platform input namespace that defines its own `MouseButton`.
