# Transition — Namespace: `VeloxDev.TimeLine`

### Class: `TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;
public sealed class TransitionEventArgs : TimeLineEventArgs { }
```

Empty; inherits `bool Handled { get; set; }` from `TimeLineEventArgs`. Setting `Handled = true` inside an effect event handler short-circuits the animation timeline (the interpreter throws `OperationCanceledException`, firing `Canceled` + `Finally`).
**Verified by:** `TransitionEffectCoreTests` (`Events_AreInvoked`).
