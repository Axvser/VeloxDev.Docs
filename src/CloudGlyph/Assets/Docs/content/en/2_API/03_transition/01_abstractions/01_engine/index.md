# Transition — Abstractions: Engine

Namespace `VeloxDev.TransitionSystem.Abstractions` in the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `SamplerSet.cs`, `TransitionEffect.cs`, `TransitionScheduler.cs`, `TransitionInterpreter.cs`, `TransitionHostBase.cs`, `TransitionRun.cs`, `TransitionDiagnostics.cs`, `ReusableTimerWait.cs`). The builder and state bag are on [builder](../00_builder/index.md); the property path is on [paths](../02_paths/index.md).

### Abstract Class: `InterpolatorCore`

```csharp
public abstract class InterpolatorCore
{
    static InterpolatorCore();   // seeds the default registry

    public static bool TryGetInterpolator(Type type, out ISampler? sampler);
    public static bool RegisterInterpolator(Type type, ISampler sampler);
    public static bool UnregisterInterpolator(Type type, out ISampler? sampler);

    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect);   // base returns null

    public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(
        object target, IFrameState state, ITransitionEffectCore effect, ITransitionHost<TPriorityCore> host);
}
```

| Member | Description |
|---|---|
| `RegisterInterpolator` | Installs a sampler with **last-writer-wins** semantics (`AddOrUpdate`) — unconditional, atomic. Returns `true`. |
| `UnregisterInterpolator` | Removes the entry; reports it via `sampler`. |
| `TryGetInterpolator` | Resolves the sampler for a *property* type: the exact type, then base classes nearest-first, then interfaces. |
| `CreateScheduler` | The scheduler this platform animates `target` with, for a caller that knows the target only as an `object`; `null` when this platform cannot carry `effect`. |
| `Prepare<TPriorityCore>` | Normalizes a declared state into a runnable `SamplerSet<TPriorityCore>`. |

**Notes on the registry:** the dictionary itself is **private**, reached only through the three members above. It is held the way `TimerCore` holds its factories rather than as a public property: a caller that could reach the dictionary could replace it wholesale — dropping every default installed by the static constructor — or clear it, and neither is something a registration API should allow. The keys are never handed out. The static constructor seeds `double`, `float`, `int`, `long`, `System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`, and (only when not compiled for `netstandard2.0`) `System.Numerics.Vector2/Vector3/Vector4/Quaternion`.

**Notes on `TryGetInterpolator` (resolution order):** the lookup is not an exact match. The exact type is tried first; then the base-class chain, nearest first; then the type's interfaces, and when several interfaces match, the one whose full name sorts first (ordinal). Interfaces come last and their tie-break is explicit because reflection's own order is not specified. The reason for the walk is that a framework property is very often declared as a subclass of what the adapter registered — a `LinearGradientBrush` property against WPF's registered `Brush` — so an exact match alone would leave it unanimated and report it unsampleable. What that means for a registration: register the **general** type (a concrete-type registration is redundant once a base class or an interface is registered); a general registration must handle its whole family, because the walk will hand it subclasses; and the lookup is per *property type*, so a path declared as `LinearGradientBrush` finds a `Brush` sampler. The walk runs once per property per animation, inside `Prepare` — never per frame. *Verified by:* `InterpolatorCoreTests` (`TryGetInterpolator_FallsBackToABaseClass`, `TryGetInterpolator_PrefersTheNearestBaseClass`, `TryGetInterpolator_FallsBackToAnInterface`, `TryGetInterpolator_PrefersABaseClassOverAnInterface`, `TryGetInterpolator_WithTwoMatchingInterfaces_IsDeterministic`).

**Notes on `CreateScheduler`:** the seam the theme system runs on. A theme switch spans targets of many runtime types, so Core cannot name the type argument of `Transition<T>`, and which host, interpreter and dispatcher priority make up a scheduler is the one thing only the platform knows. The base returns `null`; every adapter overrides it and hands out the scheduler it parameterizes (see [adapter-provided/effect-interpolator](../../03_adapter-provided/01_effect-interpolator/index.md)). `null` is the honest answer both for "this platform has not opted in" and for "this effect does not belong to this platform" — the second mirroring the cast the scheduler itself performs before running — and the caller then falls back to switching without animating rather than starting a run that draws nothing. An override must return the instance `TransitionSchedulerCore<...>.FindOrCreate` gives it, never a scheduler it constructed itself: only that path files the scheduler under the target, and that registration is what a later `Transition.Pause` / `Transition.Seek` / `Transition.Exit(target)` reads. *Verified by:* all seven adapters' `PlatformAdapters/Interpolator.cs`; `ThemeManager` / `RunSwitch`.

**Notes on `Prepare<TPriorityCore>`:** For every declared value it binds the path to the target (`TransitionProperty.BindTo` — frozen index arguments are resolved here, once, against the target, the first moment a target exists; a path with nothing to freeze returns itself, so the common case allocates nothing), then reads the current value through `host.Run<object?>(target, ...)`. An invalid path (`TransitionProperty.UnreadablePath`) is **skipped and reported through the effect's `Warn`**, not interpolated as null. Sampler resolution order: (1) a per-property custom sampler from `state.Interpolators`; (2) the registry by `PropertyType`; (3) a *struct* value type implementing `ISampleable` → the internal `StructAssembler` (member samplers must all resolve, otherwise skipped). A property that resolves to nothing is reported through `Warn` and skipped. It then calls `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)` once and stores `(property, sampler, normalizedStart, normalizedEnd, options)` per entry. Adapters derive `Interpolator : InterpolatorCore`, register platform types in their static constructor, and override `CreateScheduler`. *Verified by:* `InterpolatorCoreTests`, `TransitionSchedulerPrepareTests`.

### Class: `SamplerSet<TPriorityCore>`

```csharp
public sealed class SamplerSet<TPriorityCore>
{
    public SamplerSet(ITransitionHost<TPriorityCore> host);
    public bool CanSetValue();
    public void Apply(object target, double t, TPriorityCore priority = default!);
}
```

**Notes:** the type parameter is the host's dispatcher priority (or `NonPriority`), carried as a type parameter rather than as `object?` so `Apply` hands the priority to the host **unboxed** — the previous `object?` parameter boxed a `DispatcherPriority` on every frame of every animation. The constructor throws `ArgumentNullException` on a null host. `CanSetValue()` returns `host.IsAlive`. `Apply` marshals the per-property updates to the UI thread: it returns immediately when the animation is cancelled or the app is not alive (the stale-frame guard, so a queued frame can never overwrite a reset), caches one closure per target and passes the eased time through an `Interlocked`-read field (zero closure allocation per sample), resolves the thread the run is pinned to (falling back to `host.ThreadFor(target)` for a caller with no run), and posts through `host.Post`. On the UI thread it runs each entry's `sampler.InsertFrame(...)`; a sampler that throws is reported once through `Error` and the run ends quietly rather than throwing at frame rate. *Verified by:* `SamplerSetTests`, `FramePathAllocationTests`.

### Class: `TransitionEffectCore` / `TransitionEffectCore<TPriorityCore>`

Default descriptor implementation. Defaults: `FPS = 60`, `Duration = 0`, `IsAutoReverse = false`, `LoopTime = 0`, `Ease = Eases.Default`.

| Member | Type / Signature |
|---|---|
| Properties | `virtual int FPS`, `virtual TimeSpan Duration`, `virtual bool IsAutoReverse`, `virtual int LoopTime`, `virtual IEaseCalculator Ease` (all `{ get; set; }`) |
| Events | `virtual event EventHandler<TransitionEventArgs>` — `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally`, `Warn`, `Error` |
| Invokers | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally/InvokeWarn/InvokeError(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**Notes:** events are backed by `WeakDelegate` (`VeloxDev.WeakTypes`), so short-lived handler owners do not leak; `Clone` deep-clones the event backing stores and copies all properties (including `Warn`/`Error` and `Priority`). `InvokeCancled` (sic) is the real member name. `InvokeWarn` / `InvokeError` write a `Debug.WriteLine` line and then raise the event, and they deliberately do **not** call `Debug.Fail` — that would terminate the process in a non-interactive host, which is exactly what this channel exists to prevent. The plain base itself implements `ITransitionEffect<NonPriority>` (with an explicit `NonPriority` priority that is always `default`), so a priority-free adapter can use it directly; the subclass `TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` adds `virtual TPriorityCore Priority { get; set; }` and `new ITransitionEffect<TPriorityCore> Clone()`. *Verified by:* `TransitionEffectCoreTests`, `TransitionDiagnosticsTests`.

### Abstract Class: `TransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> NoMutualSchedulers { get; internal set; }

    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);

    protected readonly SemaphoreSlim _gate = new(1, 1);
    public virtual WeakReference<object>? TargetRef { get; protected set; }

    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**Notes:** `MutualSchedulers` caches one *mutual* scheduler per target (a `ConditionalWeakTable`, collected with the target); `NoMutualSchedulers` holds the active one-off *non-mutual* schedulers per target as a concurrent **set** (animations register/unregister themselves from several threads at once, so a plain `List` would lose entries and `Exit` would miss a live run). A second `ConditionalWeakTable` (`GetTargetLock`) serializes the **control plane** of one target — entering (creating the token and registering the animation) against leaving (cancelling everything alive on it); it is only ever held across synchronous bookkeeping, never across the animation body.

One generic subclass parameterizes the concrete host / interpreter:

```csharp
public class TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>
    : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>
    where THost : ITransitionHost<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    protected static readonly THost host = new();

    public static ITransitionScheduler<TPriorityCore> FindOrCreate<T>(T source, bool CanMutualTask = true) where T : class;

    public virtual Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
    public virtual Task<SamplerSet<TPriorityCore>?> ExecuteCapturing(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
    public virtual Task Replay(SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
}
```

| Member | Description |
|---|---|
| `FindOrCreate(source, CanMutualTask)` | The cached mutual scheduler (installed atomically via `GetValue`) or a fresh non-mutual one carrying a `WeakReference` to the source. |
| `Execute` | Runs one prepared animation: awaits the `Awake` dispatch on the UI thread (awaited, not fire-and-forget, so `Awake` finishes before `Prepare` reads the target — it may veto the animation through `Args.Handled` and may put the target into the state the animation starts from), prepares the `SamplerSet`, registers the run, then hands the set to a fresh interpreter. A `_gate` serializes executions; a **generation counter** lets a run still queued on the gate give up when an `Exit` landed first. |
| `ExecuteCapturing` | Same, but hands back the frame set it prepared, so the caller can run that same segment again against the same endpoints. |
| `Replay(frameSet, effect, cts)` | Runs one segment again against the frame set it was prepared with. The target is **not** re-read and `Awake` is **not** re-raised; `Start`, `Update`, `LateUpdate`, `Completed` and the diagnostics fire exactly as for any other pass, so a replay is observable the same way a pass is. This pair is what a chain's `Repeat` loops are built on. |

Each animation registers its `CancellationTokenSource` for its **whole lifetime** (including the `Await` gaps between segments) so `Exit()` can cancel a run that is not currently executing a segment. `Exit()` bumps the generation and drains the tracked runs, then cancels them *outside* any lock. *Verified by:* WPF demo `RepeatMutual` / `ExitAll`, `TransitionSchedulerExitTests`, `TransitionSchedulerAwakeTests`, `NoMutualSchedulerRegistryTests`, `ChainRepeatTests`, `AUTO TEST` `LoadModes_MatchTheLibrarySemantics`.

### Abstract Class: `TransitionInterpreterCore`

```csharp
public abstract class TransitionInterpreterCore : IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    protected virtual FramePacerCore? CreateFramePacer(object target, IThreadAffinity affinity);   // default null
    protected virtual void ArmNextFrame(Action continuation, TimeSpan interval, CancellationToken cancellationToken);

    public virtual void Exit();
    public virtual void Dispose();   // cancels the active CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync<TPriorityCore>(object target, SamplerSet<TPriorityCore> frameSet,
        ITransitionEffectCore effect, CancellationTokenSource cts, Action<double> apply);
}
```

| Member | Description |
|---|---|
| `CreateFramePacer(target, affinity)` | The host's own frame pacer, or null to wait on the default thread-pool timer. Called **at most once per run**, before the loop's first frame, and still synchronously on the thread the loop was started on — so an implementation may also capture the current thread's dispatcher. A host should derive the pacer from `affinity.ThreadFor(target)`: a pacer that disagrees with the write path turns every frame into a dispatch. `ThreadRef.None` and null are both supported answers. |
| `ArmNextFrame(continuation, interval, token)` | Schedules the next frame: an already-cancelled token runs the continuation immediately, otherwise it goes through the pacer when the host supplied one and through one reused `ReusableTimerWait` (a single `Timer` for the whole loop, one cancellation registration for the animation rather than one per frame) when it did not. Must not block and must invoke the continuation **exactly once** — an implementation that simply stopped calling back would park the loop for good. |

Two generic subclasses wire the loop to the sampler set's `Apply`:
- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>` (constraint `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`) — applies `easedT => frameSet.Apply(target, easedT, effect.Priority)`.
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority>` (constraint `TTransitionEffectCore : ITransitionEffectCore`) — applies `easedT => frameSet.Apply(target, easedT)`; a priority-free host keeps sampling on the priority-free path, so `NonPriority` costs nothing per frame.

**Sampling-loop semantics** (`ExecuteSamplingLoopAsync`): timeline-driven continuous sampling, not a frame pump. The normalized time is the distance from the running pass's anchor into the animation's `ITimeSource` — `Task.Delay` is never a timing source, and its imprecision cannot affect correctness. The yield interval is capped at `1000 / FPS` ms (`FPS` is a maximum sample rate, not a frame grid): that bounds the allocation rate and stops the loop flooding the UI render thread when the system timer resolution is fine. Each pass computes the raw time, eases it (**unclamped** — `Back` and `Elastic` are defined by leaving `[0, 1]`), then `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`; the final frame of each pass is the **exact endpoint** (`t >= 1` → eased `1` forward / `0` reverse), independent of whether `Ease(1)` is exactly `1`. While the timeline is not advancing the loop draws the frozen position first and then **parks** on `WaitWhileStalledAsync`, so a paused or frozen animation costs no timer wake-ups at all (a rate of zero freezes the timeline without pausing it, and the loop parks for that too). `Start` fires once before the loop; `IsAutoReverse` adds a reverse pass; `LoopTime` repeats (`int.MaxValue` = forever), and the pass counter is read from the run rather than held privately, so a `Seek` can move it. Normal completion fires `Completed`; cancellation — a cancelled `cts` **or** `Args.Handled = true` → `OperationCanceledException` — fires `Canceled`; `Finally` fires on every end path, and the loop's own resources (the pacer and the reused wait) are released in a nested `finally` so a throwing callback cannot leak a host timer. **An exception never leaves the method**: a callback, a sampler or a host that throws ends the run and is reported through `Error`, then the run unwinds down its normal cancellation path so `Canceled` and `Finally` still fire. *Verified by:* `SamplingLoopTests`, `FramePacerTests`, `ReusableTimerWaitTests`, `TransitionDiagnosticsTests`.

### Class: `TransitionHostBase<TPriorityCore>`

The base an adapter's host derives from: `ThreadDispatcherBase<TPriorityCore>` plus an `ApplicationState` liveness flag. Documented with the host contracts — see [host](../../00_transitionsystem/03_host/index.md).

### Internal-support types (not public API)

Documented here because the behavior they implement is observable, even though the types are `internal`:

- **`TransitionRun`** — one running animation: the token that ends it, the `ITimeSourceControl` it is anchored to, the timeline position the current pass started at (`PassAnchor`), the pass counter (`Cycle`), and the `ThreadRef` it posts its frames to (pinned once by the scheduler, because the write path runs on the sampling loop's thread and that thread carries no answer for a host whose answer depends on the caller — a Blazor circuit's renderer). Both `PassAnchor` and `Cycle` are single `long` fields, each moved by one atomic operation.
- **`TransitionDiagnostics`** — reports a run's degraded and failed stages: a `Debug` line, plus the effect's `Warn` / `Error` event when someone is listening. Neither channel throws to the caller, and each `stage` is reported **at most once per instance**, because most of them are per-frame facts. A handler that sets `Handled` on the argument asks for the run to terminate.
- **`ReusableTimerWait`** — one `Timer` for a whole loop, re-armed per wait, and one cancellation registration for the whole loop rather than one per wait. `await Task.Delay(interval, token)` builds a fresh `DelayPromise` and registers a fresh cancellation callback on every wait; the sampling loop waits once per animation per frame, so this was the last allocation left on an otherwise allocation-free path — `ReusableTimerWaitTests` measures the difference. It is the same `Timer` `Task.Delay` ends up in, so it changes what a wait costs and not when it lands. A parked wait is **resumed**, not dropped, on disposal: dropping it would leave the loop suspended with nothing left that could ever wake it.
