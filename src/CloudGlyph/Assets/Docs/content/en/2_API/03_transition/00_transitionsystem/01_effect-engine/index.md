# Transition — Contracts: Effect, Scheduler, Interpreter, Pacing

Namespace `VeloxDev.TransitionSystem`. These interfaces describe the timing descriptor, the per-target execution coordinator, the sampling-loop runner, and the abstract base that decides when the loop's next frame happens. Every generic interface carries the host's dispatcher priority as a **type parameter**; an adapter whose host has no priority (MAUI, WinForms, Razor) fills it with `NonPriority`. There are no priority-free interface variants.

The host and thread contracts these types are handed — `ITransitionHost<TPriorityCore>`, `IThreadDispatcher<TPriorityCore>`, `ThreadRef` — are documented in [host](../03_host/index.md).

### Interface: `ITransitionEffectCore`

| Member | Type / Signature | Description |
|---|---|---|
| `FPS` | `int FPS { get; set; }` | **Maximum sample-rate cap**, default `60`. The yield interval is `1000 / FPS` ms. Timing is timeline-driven continuous sampling — `FPS` bounds how often the loop samples; it is *not* a frame grid. |
| `Duration` | `TimeSpan Duration { get; set; }` | Nominal pass length; default `0` (a zero-duration pass samples once and jumps to the end). |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` | When `true`, each pass is followed by a reverse pass. |
| `LoopTime` | `int LoopTime { get; set; }` | Number of repeat passes after the first; `int.MaxValue` = infinite looping. The current segment's pass number rides on `TransitionEventArgs.Loop`. |
| `Ease` | `IEaseCalculator Ease { get; set; }` | Easing curve applied to the raw normalized time. |
| Events | `EventHandler<TransitionEventArgs>` for `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally`; `EventHandler<TransitionEventArgs<WarnStage, string>>` for `Warn`; `EventHandler<TransitionEventArgs<ErrorStage, Exception>>` for `Error` | The seven payload-free lifecycle events share the plain arguments; the two diagnostics carry a typed stage and value. |
| Invokers | `void Invoke*(object sender, TransitionEventArgs e)` for the seven lifecycle events; `InvokeWarn(object, TransitionEventArgs<WarnStage, string>)`; `InvokeError(object, TransitionEventArgs<ErrorStage, Exception>)` | `InvokeAwake`, `InvokeStart`, `InvokeUpdate`, `InvokeLateUpdate`, `InvokeCompleted`, `InvokeCancled`, `InvokeFinally`, plus `InvokeWarn` / `InvokeError` (the misspelling `InvokeCancled` is the real member name). |
| `Clone` | `ITransitionEffectCore Clone()` | Deep copy that also clones the (weak) event backing stores. |

**Notes:**
- Event ordering in a normal run: scheduler fires `Awaked` on the UI thread before preparing, then the loop fires `Start` once, then `Update` / `LateUpdate` per sample, and `Completed` after the last pass. A cancelled run fires `Canceled`, and **every** end path (completed or cancelled) fires `Finally`.
- `Warn` and `Error` are the **diagnostic** channel, not the lifecycle channel: the engine raises them (through `Abstractions.TransitionDiagnostics`) when a run degrades and carries on (`Warn`: a dropped frame, a path skipped for the target's runtime type, an unsampled property, a refused `Awake`) or when a stage fails (`Error`: a throwing callback, sampler, host dispatch or `Prepare`). Each stage is reported **at most once per run**, so a property that cannot be sampled does not report at frame rate. Setting `Handled = true` on a `Warn`/`Error` argument asks for the run to be terminated (the argument is a typed `TransitionEventArgs<TStage, TValue>` carrying `Stage` / `Value` — see [event arguments](../04_transition-event-args/index.md)).
- *Verified by:* `TransitionEffectCoreTests` (`Defaults_AreCorrect`, `Events_AreInvoked`, `Clone_CopiesProperties`, `EventRemove_StopsFiring`), `SamplingLoopTests` (event-order assertions), `TransitionDiagnosticsTests`.

### Interface: `ITransitionEffect<TPriorityCore>`

Extends `ITransitionEffectCore` with a typed priority and a covariant clone:

```csharp
public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore
{
    TPriorityCore Priority { get; set; }
    new ITransitionEffect<TPriorityCore> Clone();
}
```

**Notes:** Adapter effects set a concrete priority default (e.g. WPF/Avalonia `DispatcherPriority.Render`, WinUI `DispatcherQueuePriority.High`); the loop passes `Priority` through to the sampler set's `Apply`.

### Interface: `ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**Notes:**
- `Execute` runs one prepared animation on the scheduler's target: it awaits the `Awaked` dispatch (so `Awake` finishes before anything reads the target), prepares the `SamplerSet<TPriorityCore>`, then delegates to the interpreter. A `SemaphoreSlim` gate serializes executions on a *mutual* scheduler (a second animation cancels the first); `externCts` lets the caller supply its own cancellation source.
- `Exit()` cancels every animation currently tracked by that scheduler.
- Typed variants narrow the effect parameter:
  - `ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore` — `Execute(InterpolatorCore, IFrameState, ITransitionEffect<TPriorityCore>, CancellationTokenSource? externCts = default)`.
  - `ITransitionScheduler : ITransitionSchedulerCore` — marker (no new members).
- A generic implementation is supplied by `Abstractions.TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>`, whose extra public members `ExecuteCapturing` and `Replay` back a chain's loops (see [abstractions](../../01_abstractions/index.md)).
- *Verified by:* `SamplingLoopTests`; WPF demo `RepeatMutual` (a new mutual animation cancels the previous one); `AUTO TEST` `LoadModes_MatchTheLibrarySemantics` (concurrent vs. exclusive registration).

### Interface: `ITransitionInterpreter<TPriorityCore>`

```csharp
public interface ITransitionInterpreter<TPriorityCore> : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet<TPriorityCore> samplerSet,
        ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts);
    void Exit();
}
```

**Notes:**
- `Args` is the event-arguments instance the interpreter drives; setting `Args.Handled = true` short-circuits the timeline (the loop throws `OperationCanceledException` → `Canceled` + `Finally`).
- `Execute` runs the sampling loop against the prepared `SamplerSet<TPriorityCore>`. `Exit()` (alias of `Dispose`) cancels the active `CancellationTokenSource`.
- The interpreter is a **single, priority-typed** interface: an adapter with no dispatcher priority instantiates `ITransitionInterpreter<NonPriority>` (its `SamplerSet<NonPriority>` applies frames without a priority). There is no non-generic variant.
- The concrete loop behavior lives in `Abstractions.TransitionInterpreterCore` (see [abstractions](../../01_abstractions/index.md)).
- *Verified by:* `SamplingLoopTests` (`DurationZero_JumpsToEnd_AndCompletes`, `HandledBeforeStart_CancelsAndFiresFinally`).

### Class: `FramePacerCore`

Decides when the sampling loop's next frame happens, and owns the bookkeeping that keeps it safe.

```csharp
public abstract class FramePacerCore : IDisposable
{
    public void Schedule(Action continuation, TimeSpan interval, CancellationToken cancellationToken);
    protected abstract void Arm(TimeSpan interval);
    protected abstract void Disarm();
    protected void Fire();
    public virtual void Dispose();
}
```

| Member | Description |
|---|---|
| `Schedule(continuation, interval, token)` | Arranges for `continuation` to run **once**, no earlier than `interval` from now, or as soon as `token` is cancelled. A pending continuation is *replaced* rather than queued (one loop owns one pacer and re-arms after every frame). An already-cancelled token runs the continuation immediately. |
| `Arm(interval)` | Subclass hook: starts or re-arms the wait so it completes once after `interval`. Called once per frame, always after the continuation was published; the interval is re-read every time because an effect's `FPS` may change mid-animation. |
| `Disarm()` | Subclass hook: ends the wait. Must tolerate being called when nothing is armed and must not allocate (called once per frame). |
| `Fire()` | Subclass calls this when its wait completes — from a host timer's tick, or from the central loop's own frame. Disarms first, then invokes the pending continuation exactly once. |
| `Dispose()` | Ends the wait and **releases** the pending continuation (invoking it), because a loop waiting on a continuation that is never invoked is stranded for good. |

**Notes:**
- The abstract base is a class rather than an interface so the bookkeeping lives in one place: a pacer that invoked its continuation twice would double-sample, and one that never invoked it would park the loop for good — with no exception and no frame. Neither failure is visible from the host side.
- The default wait is a thread-pool timer (`Abstractions.ReusableTimerWait`), so the continuation resumes on whatever thread that timer fired on: a custom awaiter is **not** marshalled back to a `SynchronizationContext`. A host that owns a UI thread overrides `Arm`/`Disarm` to wait on that thread instead (`TransitionInterpreterCore.CreateFramePacer`), so the continuation is invoked there in the first place — the effect's `Update`/`LateUpdate` callbacks belong on the UI thread and the property writes reach the target without a dispatch per frame. Waiting on an existing central frame loop rather than on a timer of one's own is the same shape: arm means registering with that loop, disarm means leaving it.
- *Verified by:* `FramePacerTests` (`Src/Core/VeloxDev.Core.Test/TransitionSystem/FramePacerTests.cs`), `ReusableTimerWaitTests`, and the per-adapter pacer overrides (`Src/Adapters/VeloxDev.WPF/PlatformAdapters/TransitionInterpreter.cs` and siblings).
