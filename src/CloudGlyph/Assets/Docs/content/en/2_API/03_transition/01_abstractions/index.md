# Transition — Namespace: `VeloxDev.TransitionSystem.Abstractions`

### Class: `TransitionCore` / `TransitionCore<TTarget, TStateSnapshotCore>`

```csharp
public abstract class TransitionCore
{
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
public class TransitionCore<TTarget, TStateSnapshotCore> : TransitionCore where TStateSnapshotCore : new()
{
    public static TStateSnapshotCore Create();
    public static void Execute<T>(T target, StateSnapshotCore value, bool CanMutualTask = true) where T : class, TTarget;
    public static void Execute(StateSnapshotCore values, bool CanMutualTask = true);
    public static void Execute<T>(T target, IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false) where T : class, TTarget;
    public static void Execute(IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false);
}
```

**Notes:** `Exit` stops the target's mutual schedulers and, optionally, its non-mutual ones. The adapter's `Transition` (non-generic) and `Transition<T>` subclass these.
**Verified by:** WPF demo `MainWindow.xaml.cs` (`Transition.Exit(Rec0, IncludeMutual: true, IncludeNoMutual: true)`).

### Class: `StateSnapshotCore` (fluent builder) + `TransitionCoreEx` extensions

`Transition<T>.StateSnapshot` (adapter) extends `StateSnapshotCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter[, TPriorityCore]>`. The public chaining methods are extension methods on `StateSnapshotCore` in `TransitionCoreEx`:

| Member | Signature | Description |
|---|---|---|
| `Property` | `StateSnapshot Property<T>(Expression<Func<TTarget, T>> lambda, T newValue, object? interpolationOptions = null)` | Record a target value. One overload per animatable type. |
| `Effect` | `StateSnapshot Effect(TransitionEffect effect)` / `Effect(Action<TransitionEffect> effectSetter)` | Set the animation timing descriptor. |
| `Await` | `StateSnapshot Await(TimeSpan)` | Wait before this segment. |
| `Then` | `StateSnapshot Then()` | Start the next segment. |
| `AwaitThen` | `StateSnapshot AwaitThen(TimeSpan)` | Wait, then start the next segment. |
| `Interpolator` | `StateSnapshot Interpolator<T>(Expression, ISampleable)` | Per-property sampler override. |
| `Execute` | `void Execute(object target, bool CanMutualTask = true)` / `void Execute(bool CanMutualTask = true)` | Run the snapshot. |

**Notes:** `GetState()` returns the underlying `IFrameState`. Segments are linked via `next`; `CoreExecute` drains samplers, delays, effects, and states segment-by-segment through the scheduler.

### Class: `StateCore : IFrameState`

Concrete implementation of `IFrameState`; `Values`/`Interpolators`/`Options` are `public virtual` with `protected set`. The adapter's `State` derives from it.
**Verified by:** `StateCoreTests`.

### Abstract Class: `InterpolatorCore`

Now a single non-generic tier (was three generic tiers; it no longer implements an interface). The registry is keyed by `Type` and holds `ISampleable` definitions:

| Member | Signature |
|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampleable> NativeInterpolators { get; protected set; }` |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampleable? sampleable)` |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampleable sampleable)` |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampleable? sampleable)` |

**Notes:** Static ctor seeds numeric + `System.Drawing` + (non-netstandard2.0) `System.Numerics` samplers. `Prepare` resolves the per-property `ISampleable` (custom from state → registered by property type → the value IS `ISampleable`), calls `Normalize` once to obtain the stateless `ISampler`, and stores each `(ITransitionProperty, ISampler, start, end, options)` entry in a `SamplerSet`. `TransitionProperty.UnreadablePath` results are skipped. Adapters derive `Interpolator : InterpolatorCore` and register platform types in their static ctor.
**Verified by:** `InterpolatorCoreTests`, `NativeSamplersTests`.

### Class: `TransitionEffectCore` / `TransitionEffectCore<TPriorityCore> : ITransitionEffectCore`

Defaults: `FPS = 60` (maximum sample-rate cap — yield interval = `1000 / FPS` ms; timing is Stopwatch-driven continuous sampling), `Duration = 0ms`, `IsAutoReverse = false`, `LoopTime = 0`, `Ease = Eases.Default`. Events are backed by `WeakDelegate` (leak-free). The `TPriorityCore` variant adds `Priority`. Adapter `TransitionEffect : TransitionEffectCore<DispatcherPriority>` sets `DispatcherPriority.Render` (WPF/Avalonia), `TransitionEffect : TransitionEffectCore<DispatcherQueuePriority>` sets `DispatcherQueuePriority.Normal` (WinUI).
**Verified by:** `TransitionEffectCoreTests`.

### Abstract Class: `TransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, List<ITransitionSchedulerCore>> NoMutualSchedulers { get; internal set; }
    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);
    public virtual WeakReference<object>? TargetRef { get; protected set; }
    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**Notes:** A `SemaphoreSlim` gate serializes executions on a mutual scheduler; `Exit()` cancels the current `CancellationTokenSource`. `FindOrCreate` (on the generic subclasses) caches one mutual scheduler per target in `MutualSchedulers` (collected with the target), or returns a fresh non-mutual scheduler.
**Verified by:** WPF demo `RepeatMutual` (new mutual animation cancels the previous).

### Abstract Class: `TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

A Stopwatch-driven sampling loop (not a frame pump): computes `t = elapsed / Duration` from a `Stopwatch`, applies easing (clamped to `[0, 1]`), invokes `effect.InvokeStart/Update/LateUpdate`, and drives the prepared `SamplerSet` via `samplerSet.Apply(target, t, priority)`. Honors `IsAutoReverse` (forward pass samples the end, reverse pass samples the start) and `LoopTime` (`int.MaxValue` = infinite), then `InvokeCompleted` / `InvokeCancled` / `InvokeFinally`. The pass-final frame is the exact endpoint. `TransitionEventArgs.Handled` or a cancelled `cts` throws `OperationCanceledException` → `InvokeCancled`. There is no FPS-based frame stepping and no `Task.Delay` frame calibration.
**Verified by:** `SamplingLoopTests`, WPF demo animations (auto-reverse + loop), `TransitionEffectCoreTests` event order.

### Class: `SamplerSet`

The prepared per-property sampler container (renamed from `FrameUpdaterSet`; replaces `IFrameSequence` + `InterpolatorOutputBase`). Non-generic: holds the per-property `(ITransitionProperty, ISampler, start, end, options)` entries produced by `InterpolatorCore.Prepare` and carries the animation's cancellation token. `Apply(object target, double t, object? priority = default)` marshals to the UI thread, calls each `sampler.Update(target, property, start, end, options, t)`, and returns immediately when the animation is cancelled or the app is no longer alive, so stale queued frames never overwrite a reset result.
**Verified by:** `SamplerSetTests`.

### Class: `TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public TransitionProperty(IEnumerable<PropertyInfo> segments);   // throws on empty / indexed
public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);
public IReadOnlyList<PropertyInfo> Segments { get; }
public static readonly object UnreadablePath;   // sentinel for invalid intermediate type
```

**Notes:** Getter/setter are **compiled into a single delegate** on first use (no per-frame reflection). An intermediate type mismatch returns `UnreadablePath` from `GetValue` (skipped by the sampler/updater) instead of throwing `TargetException`.
**Verified by:** `TransitionPropertyTests`.

### Static Class: `TransitionSnapshotHelper`

| Member | Signature |
|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null, int maxDepth = 4)` |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null, int maxDepth = 4)` |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType, int maxDepth = 4)` |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` |

**Notes:** Discovery is a depth-limited DFS (`maxDepth = 4`) that refuses to descend into primitives, enums, value types, `string`, `object`, `IEnumerable`, and `Delegate`. `CaptureAllExcept` also excludes child paths of an excluded property.
