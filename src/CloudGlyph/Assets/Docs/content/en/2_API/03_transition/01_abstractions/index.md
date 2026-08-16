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
| `Interpolator` | `StateSnapshot Interpolator<T>(Expression, IValueInterpolator)` | Per-property interpolator override. |
| `Execute` | `void Execute(object target, bool CanMutualTask = true)` / `void Execute(bool CanMutualTask = true)` | Run the snapshot. |

**Notes:** `GetState()` returns the underlying `IFrameState`. Segments are linked via `next`; `CoreExecute` drains interpolators, delays, effects, and states segment-by-segment through the scheduler.

### Class: `StateCore : IFrameState`

Concrete implementation of `IFrameState`; `Values`/`Interpolators`/`Options` are `public virtual` with `protected set`. The adapter's `State` derives from it.
**Verified by:** `StateCoreTests`.

### Abstract Class: `InterpolatorCore`

| Member | Signature |
|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` |

**Notes:** Static ctor seeds numeric + `System.Drawing` + (non-netstandard2.0) `System.Numerics` interpolators. `Interpolate` resolves per-property custom interpolator → registry → `IInterpolable` fallback. `TransitionProperty.UnreadablePath` results are skipped. Adapters derive `Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>` and register platform types in their static ctor.
**Verified by:** `InterpolatorCoreTests`, `NativeInterpolatorsTests`.

### Class: `TransitionEffectCore` / `TransitionEffectCore<TPriorityCore> : ITransitionEffectCore`

Defaults: `FPS = 60`, `Duration = 0ms`, `IsAutoReverse = false`, `LoopTime = 0`, `Ease = Eases.Default`. Events are backed by `WeakDelegate` (leak-free). The `TPriorityCore` variant adds `Priority`. Adapter `TransitionEffect : TransitionEffectCore<DispatcherPriority>` sets `DispatcherPriority.Render` (WPF/Avalonia), `TransitionEffect : TransitionEffectCore<DispatcherQueuePriority>` sets `DispatcherQueuePriority.Normal` (WinUI).
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
    public abstract Task Execute(IFrameInterpolatorCore interpolator, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**Notes:** A `SemaphoreSlim` gate serializes executions on a mutual scheduler; `Exit()` cancels the current `CancellationTokenSource`. `FindOrCreate` (on the generic subclasses) caches one mutual scheduler per target in `MutualSchedulers` (collected with the target), or returns a fresh non-mutual scheduler.
**Verified by:** WPF demo `RepeatMutual` (new mutual animation cancels the previous).

### Abstract Class: `TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

The frame pump: computes an eased index list via `GetEaseIndex` (re-indexing the pre-computed frame array), invokes `effect.InvokeStart/Update/LateUpdate`, applies each frame through `frameSequence.Update(target, index)`, honors `IsAutoReverse` (backward walk) and `LoopTime`, then `InvokeCompleted` / `InvokeCancled` / `InvokeFinally`. `TransitionEventArgs.Handled` or a cancelled `cts` throws `OperationCanceledException` → `InvokeCancled`. Frame pacing uses a `Stopwatch`-calibrated delay (`WaitForFrameAsync`) that compensates for `Task.Delay` jitter.
**Verified by:** WPF demo animations (auto-reverse + loop), `TransitionEffectCoreTests` event order.

### Abstract Class: `InterpolatorOutputBase : IFrameSequenceCore`

`Frames` (`Dictionary<ITransitionProperty, List<object?>>`) + `Count`. `SetValues(target, frameIndex)` writes every property's frame value onto the target, skipping the write if the cancellation token is already requested (prevents stale queued frames overwriting a reset). `InterpolatorOutputCore<TUIThreadInspectorCore[, TPriorityCore]>` caches a reusable frame-write delegate and marshals via the inspector.

### Class: `TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public TransitionProperty(IEnumerable<PropertyInfo> segments);   // throws on empty / indexed
public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);
public IReadOnlyList<PropertyInfo> Segments { get; }
public static readonly object UnreadablePath;   // sentinel for invalid intermediate type
```

**Notes:** Getter/setter are **compiled into a single delegate** on first use (no per-frame reflection). An intermediate type mismatch returns `UnreadablePath` from `GetValue` (skipped by the interpolator) instead of throwing `TargetException`.
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
