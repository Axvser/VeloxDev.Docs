# Transition — Namespace: `VeloxDev.TimeLine`

The transition system's event-argument types (source: `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`, `TransitionEventArgs.cs`). `TimeLineEventArgs` is shared with the other time-line-driven systems (the `Tickable` feature); `TransitionEventArgs` is transition-specific. The rest of the namespace (`TickManager`, `TickableAttribute`, `FrameEventArgs`) belongs to the `tickable` feature.

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
    public string? Stage { get; init; }
    public string? Message { get; init; }
    public Exception? Exception { get; init; }
}
```

| Member | Description |
|---|---|
| `Stage` | Which callback or stage reported this — `"Update"`, `"Finally"`, `"Sampling"`, `"Prepare"`, `"Run"`, … |
| `Message` | Human-readable text for a degraded stage (a `Warn`). |
| `Exception` | The escaped exception for a failed stage (an `Error`). |

**Notes:**
- The sealed event-argument type passed to every `ITransitionEffectCore` event handler (`EventHandler<TransitionEventArgs>`) and invoker (`InvokeAwake` … `InvokeFinally`, `InvokeWarn`, `InvokeError`).
- Setting `e.Handled = true` inside an effect event handler short-circuits the sampling loop: the interpreter throws `OperationCanceledException`, which fires `Canceled` and then `Finally` (see [abstractions](../01_abstractions/01_engine/index.md)). A cancelled `CancellationTokenSource` has the same effect.
- The three descriptive members are `init`-only and are populated for the **diagnostic** channel: the engine raises `Warn` for a stage a run degrades through and carries on from (a dropped frame, a path skipped for the target's runtime type, an unsampled property, a refused `Awake`), and `Error` for a stage that failed (a throwing callback, sampler, host dispatch or `Prepare`). Raising either through a `Warn` / `Error` handler sets `Handled = true` to terminate the run. The seven lifecycle events leave all three `null`.
- *Verified by:* `SamplingLoopTests` (`HandledBeforeStart_CancelsAndFiresFinally`), `TransitionEffectCoreTests` (`Events_AreInvoked`), `TransitionDiagnosticsTests`.
