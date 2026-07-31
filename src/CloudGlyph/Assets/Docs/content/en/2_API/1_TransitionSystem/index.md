# Transition System — API Reference

The engine lives in `VeloxDev.Core`; each platform adapter (WPF/Avalonia/WinUI/MAUI/WinForms/Razor) exposes the same public shapes in the `VeloxDev.TransitionSystem` namespace with its own `Interpolator`, `TransitionEffect`, `UIThreadInspector`, and native interpolators.

## Namespace: `VeloxDev.TransitionSystem`

### Interface: `IInterpolable`

```csharp
public interface IInterpolable
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**Returns:** `List<object?>` — the intermediate values for `steps` frames.

### Interface: `IValueInterpolator`

```csharp
public interface IValueInterpolator
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**Notes:** Implement this to register support for a custom type (via `InterpolatorCore.RegisterInterpolator`).

### Interface: `IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

### Interface: `ITransitionProperty`

| Member | Type | Description |
|---|---|---|
| `Path` | `string` | Dot-separated nested property path (e.g. `"RenderTransform.X"`). |
| `PropertyType` | `Type` | Type of the leaf property. |
| `PropertyInfo` | `PropertyInfo` | Leaf property metadata. |
| `CanRead` / `CanWrite` | `bool` | Whether the whole chain supports reading/writing. |
| `GetValue` | `object? GetValue(object target)` | Read through the chain. |
| `SetValue` | `bool SetValue(object target, object? value)` | Write through the chain. |

### Interface: `IFrameState`

A bag of three `ConcurrentDictionary`s keyed by `ITransitionProperty`:

| Member | Type |
|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, IValueInterpolator>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

Plus typed/strongly-named accessors: `SetValue`, `TryGetValue`, `SetInterpolator`, `TryGetInterpolator`, `SetOptions`, `TryGetOptions` — each with three overload families (expression lambda / `ITransitionProperty` / `PropertyInfo`), and `IFrameState Clone()`.

### Interface: `ITransitionEffectCore`

| Member | Type / Signature |
|---|---|
| `FPS` | `int FPS { get; set; }` (default 60) |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }` (`int.MaxValue` = infinite) |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| Events | `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` — `EventHandler<TransitionEventArgs>` |
| `Clone` | `ITransitionEffectCore Clone()` |

### Interface: `ITransitionEffect<TPriorityCore> : ITransitionEffectCore`

Adds `TPriorityCore Priority { get; set; }` and `new ITransitionEffect<TPriorityCore> Clone()`.

### Interface: `ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(IFrameInterpolatorCore interpolator, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**Notes:** `FindOrCreate<T>(T source, bool CanMutualTask = true)` (on the concrete scheduler) returns a per-target shared **mutual** scheduler (stored in a `ConditionalWeakTable`) when `CanMutualTask: true`, otherwise a one-off **non-mutual** scheduler that allows parallel animations.

### Interface: `ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, IFrameSequenceCore frameSequence, ITransitionEffectCore effect, bool isUIAccess, CancellationTokenSource cts);
    void Exit();
}
```

### Interface: `IUIThreadInspectorCore`

| Member | Signature |
|---|---|
| `IsAppAlive` | `bool IsAppAlive()` |
| `IsUIThread` | `bool IsUIThread()` |
| `ProtectedInvoke` | `abstract void ProtectedInvoke(bool isUIThread, Action action, object? priority = default)` |
| `ProtectedGetValue` | `object? ProtectedGetValue(bool isUIThread, object target, ITransitionProperty property)` |
| `ProtectedInterpolate` | `abstract List<object?> ProtectedInterpolate(bool isUIThread, Func<List<object?>> interpolate)` |

### Interface family (frame pump)

| Interface | Key member |
|---|---|
| `IFrameInterpolatorCore` | `IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, bool isUIAccess, IUIThreadInspectorCore inspector)` |
| `IFrameInterpolator : IFrameInterpolatorCore` | platform-specific overload |
| `IFrameInterpolator<TPriorityCore> : IFrameInterpolatorCore` | platform-specific overload |
| `IFrameSequenceCore` | `int Count`; `SetValues(target, frameIndex)`; `Update(target, frameIndex, isUIAccess, priority)`; `AddPropertyInterpolations(property, objects)`; `SetCount(count)` |
| `IFrameSequence : IFrameSequenceCore` | `Update(target, frameIndex, isUIAccess)` |
| `IFrameSequence<TPriorityCore> : IFrameSequenceCore` | `Update(target, frameIndex, isUIAccess, TPriorityCore)` |

### Enum: `RotationDirection`

```csharp
[Flags]
public enum RotationDirection : int
{
    Auto = 0, ClockWise = 1 << 0, CounterClockWise = 1 << 1,
    ClockWiseX = 1 << 2, CounterClockWiseX = 1 << 3,
    ClockWiseY = 1 << 4, CounterClockWiseY = 1 << 5,
    ClockWiseZ = 1 << 6, CounterClockWiseZ = 1 << 7,
}
```

**Notes:** Passed as the `interpolationOptions` of `.Property(lambda, value, options)` to steer angular interpolation.

### Static Class: `Eases`

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }
    public static class Sine    { public static IEaseCalculator In { get; } /* Out, InOut */ }
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — same shape
}
```

Concrete ease classes (each `: IEaseCalculator`): `EaseDefault`, `EaseInSine`, `EaseOutSine`, `EaseInOutSine`, ..., `EaseInOutBounce`.

## Namespace: `VeloxDev.TransitionSystem.Abstractions`

### Class: `Transition` / `Transition<T>`

```csharp
public abstract class TransitionCore
{
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
public class Transition : TransitionCore { }   // non-generic; adapter subclass
public class Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot> { }
public class TransitionCore<TTarget, TStateSnapshotCore> : TransitionCore where TStateSnapshotCore : new()
{
    public static TStateSnapshotCore Create();
    public static void Execute<T>(T target, StateSnapshotCore value, bool CanMutualTask = true) where T : class, TTarget;
    public static void Execute(StateSnapshotCore values, bool CanMutualTask = true);
    public static void Execute<T>(T target, IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false) where T : class, TTarget;
    public static void Execute(IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false);
}
```

### Class: `StateSnapshotCore` (fluent builder)

`Transition<T>.StateSnapshot` extends `StateSnapshotCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter[, TPriorityCore]>`.

| Member | Signature | Description |
|---|---|---|
| `Property` | `StateSnapshot Property<T>(Expression<Func<TTarget, T>> lambda, T newValue, object? interpolationOptions = null)` | Record a target value. One overload per animatable type. |
| `Effect` | `StateSnapshot Effect(TransitionEffect effect)` / `Effect(Action<TransitionEffect> effectSetter)` | Set the animation timing descriptor. |
| `Await` | `StateSnapshot Await(TimeSpan)` | Wait before this segment. |
| `Then` | `StateSnapshot Then()` | Start the next segment. |
| `AwaitThen` | `StateSnapshot AwaitThen(TimeSpan)` | Wait, then start the next segment. |
| `Interpolator` | `StateSnapshot Interpolator<T>(Expression, IValueInterpolator)` | Per-property interpolator override. |

### Class: `StateCore : IFrameState`

Concrete implementation of `IFrameState`; `Values`/`Interpolators`/`Options` are `public virtual` with `protected set`. The adapter's `State` derives from it.

### Abstract Class: `InterpolatorCore : IFrameInterpolatorCore`

| Member | Signature |
|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` |

**Notes:** Static ctor seeds numeric + `System.Drawing` + `System.Numerics` interpolators. Adapters derive `Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>` and register platform types in their static ctor.

### Class: `TransitionEffectCore : ITransitionEffectCore`

Defaults: `FPS = 60`, `Duration = 0ms`, `Ease = Eases.Default`. Events are backed by `WeakDelegate`. Adapter `TransitionEffect : TransitionEffectCore<TPriorityCore>` sets a platform priority (WPF/Avalonia `DispatcherPriority.Render`, WinUI `DispatcherQueuePriority.Normal`).

### Class: `TransitionSchedulerCore` (abstract)

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

### Class: `TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

The frame pump: loops over the frame sequence, invokes `effect.InvokeStart/Update/LateUpdate`, applies each frame, honors `IsAutoReverse`/`LoopTime`, then `InvokeCompleted`/`InvokeCancled`/`InvokeFinally`. `TransitionEventArgs.Handled` cancels the timeline.

### Abstract Class: `InterpolatorOutputBase : IFrameSequenceCore`

`Frames` (`Dictionary<ITransitionProperty, List<object?>>`) + `Count`. `Update(target, frameIndex, isUIAccess, priority)` writes every property's frame value onto the target, marshalling to the UI thread when needed.

### Class: `TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public TransitionProperty(IEnumerable<PropertyInfo> segments);   // throws on empty / indexed
public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);
public IReadOnlyList<PropertyInfo> Segments { get; }
```

### Static Class: `TransitionSnapshotHelper`

| Member | Signature |
|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null, int maxDepth = 4)` |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null, int maxDepth = 4)` |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType, int maxDepth = 4)` |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` |

## Namespace: `VeloxDev.TransitionSystem.NativeInterpolators`

All implement `IValueInterpolator.Interpolate(start, end, steps, options)`:

`DoubleInterpolator` (honors `RotationDirection` shortest-path angle), `FloatInterpolator`, `IntInterpolator`, `LongInterpolator` (decimal math), `PointInterpolator`, `PointFInterpolator`, `SizeInterpolator`, `SizeFInterpolator`, `RectangleInterpolator`, `RectangleFInterpolator`, `ColorInterpolator` (ARGB lerp), and (non-netstandard2.0) `Vector2Interpolator`, `Vector3Interpolator`, `Vector4Interpolator`, `QuaternionInterpolator` (directional `Slerp`).

## Namespace: `VeloxDev.TransitionSystem` (adapter-provided)

### Static Class: `TransitionEx`

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

### Class: `StateSnapshot` — `.Property(...)` overload set (per adapter)

Each overload: `StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`.

| Adapter | Priority type | Extra overloads | Notable absence |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `CornerRadius`, `Thickness`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect?`, `Point3D`, `Vector3D` | — |
| Avalonia | `DispatcherPriority` | `IInterpolable?`, `ITransform?`, `IBrush?`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows` | — |
| WinUI | `DispatcherQueuePriority` | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `CornerRadius`, `Thickness`, `Projection?`, `Size`, `Rect`, `GridLength`, `Color` | — |
| MAUI | none | `IInterpolable?`, `Brush?`, `Transform?`, `Point`, `PointF`, `CornerRadius`, `Thickness`, `Color?`, `Size`, `SizeF`, `Rect`, `RectF`, `Shadow?` | `interpolationOptions` on `Transform?` |
| WinForms | none | `IInterpolable?`, `Padding` | — |
| Razor | none | `string?` | no `IInterpolable?`; has `string?` |

Common overloads across all adapters: `int`, `double`, `float`, `decimal`, `System.Drawing.*`, and (non-netstandard2.0) `System.Numerics.*`.

### Platform-specific types

- `UIThreadInspector` — WPF: `Application.Current.Dispatcher`; Avalonia: `Dispatcher.UIThread`; WinUI: **requires `SetWindow(Window)`**; MAUI: `Application.Current.Dispatcher`; WinForms/Razor: `SynchronizationContext` + `CaptureUIThread()`.
- `Interpolator` static ctor registers platform types (WPF: `Brush`, `Thickness`, `Transform`, `DropShadowEffect`, ...; Avalonia: `IBrush`, `ITransform`, `BoxShadows`, `GridLength`, ...; WinUI: `Projection`, `GridLength`, ...; MAUI: `Shadow`, `RectF`, ...; WinForms: `Padding`; Razor: `string` → `StringInterpolator`).
- `TransitionEffects` — static presets: `Empty` (0 s), `Theme` (0.46 s), `Hover` (0.32 s). **Note:** WinUI's `TransitionEffects` is a non-static class.

## Namespace: `VeloxDev.TimeLine`

### Class: `TransitionEventArgs : TimeLineEventArgs`

Empty; inherits `bool Handled { get; set; }` from `TimeLineEventArgs` (setting `Handled = true` short-circuits the animation timeline).
