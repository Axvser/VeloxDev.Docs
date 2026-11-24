# Input routing

`WorkflowInput` is the per-tree route. An adapter translates a native event into a `PointerEventArgs` or `KeyEventArgs` and calls `Route`; each helper on the way to the tree exposes an `InputRelay`; every hop receives the same `WorkflowEventHandle`.

## WorkflowInput

```csharp
public sealed class WorkflowInput
```

One instance per tree. `For` returns the same object for as long as the tree lives.

### Properties

| Member | Type | Access | Description |
|---|---|---|---|
| `Tree` | `ITreeComponent` | get | The tree this route belongs to. |
| `PointerTarget` | `IWorkflowComponent?` | get | Component currently under the pointer; `null` over empty canvas or while suspended. |
| `HoveredLink` | `ILinkComponent?` | get | `PointerTarget as ILinkComponent`. |
| `ConnectionSender` | `ISlotComponent?` | get | Port a connection drag started from. |
| `PreviewReceiver` | `ISlotComponent?` | get | Candidate receiver during a connection drag. |
| `PreviewState` | `ConnectionPreviewState` | get | Current preview state. |
| `PreviewCheck` | `ConnectionCheck?` | get | Result of the current connection check. |
| `HitRadius` | `double` | get/set | Pointer hit radius; defaults to `LinkHitTestEx.DefaultHitRadius` (6). |
| `IsSuspended` | `bool` | get/set | When `true`, pointer moves do not update `PointerTarget`; defaults to `false`. |
| `Scroller` | `IWorkflowSurfaceScroller?` | get/set | Scroller registered by an attached surface; `null` when none. |
| `Navigator` | `IWorkflowSurfaceNavigator?` | get/set | Navigator registered by an attached surface; `null` when none. |

### Events

| Event | Arguments | Description |
|---|---|---|
| `PreviewChanged` | `EventHandler<ConnectionPreviewEventArgs>` | Raised when the connection preview changes. |
| `PreviewValidating` | `EventHandler<ConnectionPreviewValidatingEventArgs>` | Raised once per framework-accepted connector before host validation. |

### Methods

| Signature | Returns | Description |
|---|---|---|
| `WorkflowInput(ITreeComponent tree)` | — | Creates a route for a tree. Throws `ArgumentNullException` when `tree` is null. |
| `static WorkflowInput For(ITreeComponent tree)` | `WorkflowInput` | Returns the shared per-tree route, creating it on first use. Throws `ArgumentNullException` when `tree` is null. |
| `Route(PointerEventArgs e)` | `void` | Raises `PointerExited`/`PointerEntered` on target change, then walks target, ancestors, tree. Throws `ArgumentNullException` when `e` is null. |
| `Route(KeyEventArgs e)` | `void` | Walks the same chain for a key event. Throws `ArgumentNullException` when `e` is null. |

The connection-preview properties and events are part of the connection feature; they are exposed here because the route owns them.

## IInputEvents and InputRelay

```csharp
public interface IInputEvents
{
    InputRelay Input { get; }
}

public sealed class InputRelay
```

`IInputEvents` is the optional helper capability that carries routed input. The default tree, node, slot, and link helpers implement it.

| Event | Arguments |
|---|---|
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>` |
| `PointerExited` | `EventHandler<PointerExitedEventArgs>` |
| `PointerMoved` | `EventHandler<PointerMovedEventArgs>` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>` |
| `PointerWheelChanged` | `EventHandler<PointerWheelEventArgs>` |
| `KeyDown` | `EventHandler<KeyDownEventArgs>` |
| `KeyUp` | `EventHandler<KeyUpEventArgs>` |

`Raise(PointerEventArgs)` and `Raise(KeyEventArgs)` are internal; an adapter routes through `WorkflowInput`, not through the relay directly.

## WorkflowEventHandle

```csharp
public sealed class WorkflowEventHandle
```

One handle travels with one logical action. A subscriber close to the target and a subscriber on the tree receive the same instance.

| Member | Type | Access | Default | Description |
|---|---|---|---|---|
| `PreventDefault` | `bool` | get/set | `false` | Suppresses the framework's own reaction for this action. |
| `StopPropagation` | `bool` | get/set | `false` | Stops the walk; no ancestor helper hears the event. |

## Pointer event arguments

```csharp
public abstract class PointerEventArgs : EventArgs
```

| Member | Type | Description |
|---|---|---|
| `Position` | `Anchor` | Surface coordinates; `Anchor.Layer` is the source view's layer. |
| `Modifiers` | `InputModifiers` | Modifier keys held during the event. |
| `Source` | `object?` | The view the input came from. |
| `Target` | `IWorkflowComponent?` | Hit component; `null` on empty canvas. Every hop sees the original target. |
| `Handle` | `WorkflowEventHandle` | The per-action handle. |

The protected constructor takes `(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)` and throws `ArgumentNullException` for a null position or handle.

| Type | Extra members |
|---|---|
| `PointerEnteredEventArgs` | — |
| `PointerExitedEventArgs` | — |
| `PointerMovedEventArgs` | — |
| `PointerPressedEventArgs` | `MouseButton Button`, `int ClickCount` |
| `PointerReleasedEventArgs` | `MouseButton Button`, `int ClickCount` |
| `PointerWheelEventArgs` | `double DeltaX`, `double DeltaY` |

`DeltaY` is positive away from the user (wheel up) and is sign-normalised across platforms. On non-tilt mice `DeltaX` is 0; only the sign is contractual.

## Key event arguments

```csharp
public abstract class KeyEventArgs : EventArgs
```

| Member | Type | Description |
|---|---|---|
| `Key` | `InputKey` | The mapped key. |
| `RawKeyCode` | `int` | Platform-native key code; not comparable across adapters. |
| `Modifiers` | `InputModifiers` | Modifier keys held during the event. |
| `IsRepeat` | `bool` | Best effort; `false` means "not reported as repeat". |
| `Source` | `object?` | The focused view. |
| `Target` | `IWorkflowComponent?` | The component the adapter applies the key to. |
| `Handle` | `WorkflowEventHandle` | The per-action handle. |

`KeyDownEventArgs` and `KeyUpEventArgs` add no members. Core has no default key action; a host decides what `Delete` or `Ctrl+Z` does.

## Enums

```csharp
public enum MouseButton
{
    None = 0, Left = 1, Right = 2, Middle = 3, XButton1 = 4, XButton2 = 5
}

[Flags]
public enum InputModifiers
{
    None = 0, Alt = 1, Control = 2, Shift = 4, Meta = 8
}
```

`InputKey` is a curated, platform-neutral key set. Keys it does not name map to `Unknown` and remain recoverable through `RawKeyCode`.

| Range | Members |
|---|---|
| Control | `Unknown=0`, `None=1`, `Cancel=2`, `Back=3`, `Tab=4`, `Enter=5`, `Escape=6`, `Space=7`, `PageUp=8`, `PageDown=9`, `End=10`, `Home=11`, `Left=12`, `Up=13`, `Right=14`, `Down=15`, `Insert=16`, `Delete=17` |
| Modifiers | `LeftShift=18`, `RightShift=19`, `LeftCtrl=20`, `RightCtrl=21`, `LeftAlt=22`, `RightAlt=23`, `LWin=24`, `RWin=25` |
| Letters | `A=30`, `B=31`, `C=32`, `D=33`, `E=34`, `F=35`, `G=36`, `H=37`, `I=38`, `J=39`, `K=40`, `L=41`, `M=42`, `N=43`, `O=44`, `P=45`, `Q=46`, `R=47`, `S=48`, `T=49`, `U=50`, `V=51`, `W=52`, `X=53`, `Y=54`, `Z=55` |
| Digits | `D0=60`, `D1=61`, `D2=62`, `D3=63`, `D4=64`, `D5=65`, `D6=66`, `D7=67`, `D8=68`, `D9=69` |
| Function row | `F1=80`, `F2=81`, `F3=82`, `F4=83`, `F5=84`, `F6=85`, `F7=86`, `F8=87`, `F9=88`, `F10=89`, `F11=90`, `F12=91` |
