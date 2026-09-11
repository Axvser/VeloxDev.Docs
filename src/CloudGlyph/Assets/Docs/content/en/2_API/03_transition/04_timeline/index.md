# Transition — Namespace: `VeloxDev.TimeLine`

The transition system's event-argument types (source: `Src/Core/VeloxDev.Core/TimeLine/*.cs`). `TimeLineEventArgs` is shared with the other time-line-driven systems (e.g. MonoBehaviour); `TransitionEventArgs` is transition-specific.

### Class: `TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

**Notes:** `Handled` is the timeline kill switch — `false` by default, `true` ends the running timeline. It is inherited by `TransitionEventArgs`, whose instance is surfaced as `ITransitionInterpreter<TPriorityCore>.Args`.

### Class: `TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public sealed class TransitionEventArgs : TimeLineEventArgs
{
}
```

**Notes:**
- The empty sealed event-argument type passed to every `ITransitionEffectCore` event handler (`EventHandler<TransitionEventArgs>`) and invoker (`InvokeAwake` … `InvokeFinally`).
- Setting `e.Handled = true` inside an effect event handler short-circuits the sampling loop: the interpreter throws `OperationCanceledException`, which fires `Canceled` and then `Finally` (see [01_abstractions](../01_abstractions/index.md)). A cancelled `CancellationTokenSource` has the same effect.
- *Verified by:* `SamplingLoopTests` (`HandledBeforeStart_CancelsAndFiresFinally`), `TransitionEffectCoreTests` (`Events_AreInvoked`).
