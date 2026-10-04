# Transition — Namespace: `VeloxDev.TimeLine`

The transition system inherits one type from the `VeloxDev.TimeLine` namespace: `TimeLineEventArgs`, the abstract base every transition payload derives from. It is shared with the other time-line-driven systems (the `Tickable` feature) and documented in full with [TimeLineEventArgs](../../06_tickable/02_TimeLineEventArgs/index.md). The transition-specific payloads — `TransitionEventArgs`, the typed `TransitionEventArgs<TStage, TValue>` and the `WarnStage` / `ErrorStage` enums — moved **out** of this namespace into `VeloxDev.TransitionSystem`; they are documented on [event arguments](../00_transitionsystem/04_transition-event-args/index.md). The rest of the namespace (`TickManager`, `TickableAttribute`, `FrameEventArgs`) belongs to the `tickable` feature.

Source: `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`.

### Class: `TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
    public TimeSpan DeltaTime { get; internal set; } = TimeSpan.Zero;
    public TimeSpan TotalTime { get; internal set; } = TimeSpan.Zero;
}
```

| Member | Description |
|---|---|
| `Handled` | The timeline kill switch — `false` by default, `true` ends the running timeline. The only writable member. |
| `DeltaTime` | Time since the previous frame. `internal` setter; the interpreter writes it once per sample. |
| `TotalTime` | Time accumulated since the current segment began (not reset per pass — the pass is `TransitionEventArgs.Loop`). `internal` setter. |

**Notes:**
- `TransitionEventArgs` derives from it and is what `ITransitionInterpreter<TPriorityCore>.Args` surfaces; its instance is shared for the whole run and re-stamped each frame.
- Setting `e.Handled = true` inside an effect event handler short-circuits the sampling loop: the interpreter throws `OperationCanceledException`, which fires `Canceled` and then `Finally` (see [abstractions](../01_abstractions/01_engine/index.md)). A cancelled `CancellationTokenSource` has the same effect.
- The diagnostic channel is separate: the engine raises `Warn` (through `TransitionEventArgs<WarnStage, string>`) for a stage a run degrades through and carries on from, and `Error` (through `TransitionEventArgs<ErrorStage, Exception>`) for a stage that failed. Raising either through its handler sets `Handled = true` to terminate the run. See [event arguments](../00_transitionsystem/04_transition-event-args/index.md).
- *Verified by:* `TimeLineEventArgsTests`, `SamplingLoopTests` (`HandledBeforeStart_CancelsAndFiresFinally`), `TransitionDiagnosticsTests`.
