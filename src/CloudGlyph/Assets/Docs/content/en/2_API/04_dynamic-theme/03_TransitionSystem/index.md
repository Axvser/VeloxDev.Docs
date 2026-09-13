# API — Dynamic Theme · Backing Engine (TransitionSystem)

The dynamic-theme feature animates themed properties through the TransitionSystem engine. A theme switch is not timed by `ThemeManager` at all: the manager builds the per-property start/end entries itself (per `StartModel`), then hands each target's `StateCore` to the platform's `TransitionSchedulerCore`, which does the sampler resolution and the sampling. This page documents the engine surface that `ThemeManager` actually consumes; the full engine is documented by the transition feature.

> The engine contracts (`ITransitionProperty`, `ISampler`, `ISampleable`, `ITransitionEffectCore`, `IEaseCalculator`) live in `VeloxDev.TransitionSystem`; the base and concrete types (`InterpolatorCore`, `TransitionSchedulerCore`, `TransitionCore`, `TransitionProperty`) live in `VeloxDev.TransitionSystem.Abstractions`; the shared transport's default implementation `TimeSourceCore` lives in `VeloxDev.Timing`. The complete engine reference lives under the transition feature (`2_API/03_transition`).

## Namespace: `VeloxDev.TransitionSystem.Abstractions`

### Abstract Class: `InterpolatorCore`

`public abstract class InterpolatorCore`

Base class for platform interpolators and holder of the static per-type sampler registry. The static constructor pre-registers native samplers for `double`, `float`, `int`, `long`, `Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF`, and (outside `NETSTANDARD2_0`) `Vector2`, `Vector3`, `Vector4`, `Quaternion`.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`.

| Member | Signature | Description |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampler> NativeInterpolators { get; protected set; }` | The per-type sampler registry. |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampler? sampler)` | Looks up a registered sampler for a type. |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampler sampler)` | Registers a sampler (atomic last-writer-wins). |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampler? sampler)` | Removes a registered sampler. |
| `Prepare` (instance, `virtual`) | `public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspector<TPriorityCore> inspector)` | Normalizes every property in a state snapshot into a `SamplerSet<TPriorityCore>`. Called by `TransitionSchedulerCore.Execute` on the path a theme switch takes; `ThemeManager` never calls it itself. |
| `CreateScheduler` (instance, `virtual`) | `public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` | The platform seam: hands back the scheduler that animates `target`, or `null` when the platform cannot carry `effect`. Default returns `null`. |

**Notes:**
- `ThemeManager.PrepareSamplers` uses `InterpolatorCore.TryGetInterpolator` to resolve a property's sampler by `PropertyInfo.PropertyType`. When no sampler is registered for that type, the property is held at its old value for the whole switch and written to its target value at the end.
- The platform adapter `Interpolator` extends `InterpolatorCore`, registers platform samplers in its static constructor, and overrides `CreateScheduler` (see [04 PlatformAdapters](../04_PlatformAdapters/index.md)).
- `CreateScheduler` exists because a switch spans targets of many runtime types, so Core cannot name the type argument of `Transition<T>`, and which inspector, interpreter and dispatcher priority make up a scheduler is the one thing only the adapter knows. `null` is the honest answer both for "this platform has not opted in" and for "this effect does not belong to this platform"; the caller then switches without animating rather than starting a run that draws nothing.
- An override must go through `TransitionSchedulerCore<...>.FindOrCreate(target)`, not construct a scheduler directly: only that path files it under the target, which is what makes a later `Transition.Pause`, `Seek` or `Exit` able to find the animation.

### Class: `TransitionSchedulerCore`

`public abstract class TransitionSchedulerCore : ITransitionSchedulerCore`

The per-target driver of a switch. `ThemeManager` resolves one per target through `InterpolatorCore.CreateScheduler` and runs the target's `StateCore` on it.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionScheduler.cs`.

| Member | Signature | Description |
|---|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | Prepares the sampler set from `state` and runs the interpreter's sampling loop. |
| `Exit` | `void Exit()` | Cancels every animation alive on this scheduler. |
| `Track` / `Untrack` (internal) | `void Track(TransitionRun run)` / `void Untrack(TransitionRun run)` | Registers a run under its own token source, so a later control call can find it. |

**Notes:**
- The concrete per-platform type is the generic `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>`, which adapters create through the static `FindOrCreate<T>(T source, bool CanMutualTask = true)`.
- `ThemeManager` calls `Track` before `Execute` and `Untrack` when the switch ends: `Execute` finds the run in the scheduler's active table through the token source it was handed, so a run that was never tracked would be sampled on a timeline nothing controls.

### Class: `TimeSourceCore`

`public sealed class TimeSourceCore : ITimeSourceControl`

Namespace: `VeloxDev.Timing`. This is the default implementation of `ITimeSourceControl`, the contract a consumer passes when several animations must share one transport; `TimerCore.CreateTimeSource<ITimeSourceControl>()` is the registry call that creates it.

An absolute virtual timeline: where it is, how fast it is moving, and the gate that parks sampling loops while it is paused. `ThemeManager` creates exactly one `ITimeSourceControl` per switch and anchors every target's run to it.

Source: `Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs`.

**Notes:**
- Sharing one timeline is what lets the control surface reach a theme switch unchanged: pausing, seeking or re-rating any one target moves the whole switch, because there is only one transport to move. The surface is `TransitionCore` in this same namespace — `Pause` / `Resume` / `Seek` / `SetRate` / `Position` / `Rate` / `Cycle` / `IsPaused` / `Exit`, each taking a target. *Verified by:* `ThemeTransitionTests.Switch_EveryTargetIsAnchoredToTheSameTimeline`, `Switch_SeekIsReachableAndFinishesThePass`.
- `ThemeManager.CancelActiveSwitch` calls the timeline's `Wake` (internal) on every run it cancels: a paused loop parks on the timeline's gate, and the gate knows nothing about cancellation tokens, so without the wake a cancelled switch would sit still until something else resumed it.

### Class: `TransitionProperty`

`public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

Compiled getter/setter implementation of `ITransitionProperty`. A property path is one or more `PropertyInfo` segments; reads and writes go through lazily compiled delegates. When an intermediate object is non-null but its runtime type does not match the path, reads return the sentinel `UnreadablePath` and writes return `false`, so callers skip the property instead of treating it as null/identity.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`.

| Member | Signature | Description |
|---|---|---|
| `UnreadablePath` | `public static readonly object UnreadablePath` | Sentinel returned by `GetValue` when the path is invalid for the current target. |
| `FromProperty` | `public static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | The memoized single-segment path for one property: the same `PropertyInfo` always yields the same instance. |
| `Members<TSource>` | `public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | Builds readable+writable member paths from expressions (for `ISampleable`). |
| `ReadableMembers<TSource>` | `public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | Builds readable member paths (for struct `ISampleable` assembly). |
| `Combine` | `public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix)` | Concatenates two paths into one. |
| `TryCreate` | `public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | Parses an expression tree into a path. |
| `Path` | `string Path` | Dot-joined segment names. |
| `PropertyType` / `PropertyInfo` / `Segments` | `Type` / `PropertyInfo` / `IReadOnlyList<PropertyInfo>` | Type, final segment info, and full segment list. |
| `CanRead` / `CanWrite` | `bool` | Readability of all segments / writability of the final segment. |
| `GetValue` / `SetValue` | `object? GetValue(object target)` / `bool SetValue(object target, object? value)` | Compiled path read/write. |

**Notes:**
- `ThemeManager.PrepareSamplers` wraps each animated property with `TransitionProperty.FromProperty(propertyInfo)` and later writes start/end values through `SetValue`.
- `FromProperty` is the reflection-driven entry point: a theme switch rebuilds a path for every themed property of every registered target on *every* switch, where a declaration-based path is built once and held in a field. It therefore goes through a static `ConcurrentDictionary<PropertyInfo, TransitionProperty>` and returns a **shared** instance rather than constructing one, so the per-path getter/setter expression is compiled once per property instead of once per switch. The commit `58ae23b3` measured the un-memoized cost at ~1.6 s of UI-thread stall and 29 MB allocated before the first frame for a thousand two-property elements, against ~10 ms and 6 MB after.
- Sharing is safe because a path is immutable, and `BindTo` returns the instance itself when there are no index arguments to freeze — always the case here. The lazy compile is idempotent, so a concurrent first use can only compile twice and discard one.

## Namespace: `VeloxDev.TransitionSystem`

### Interface: `ITransitionProperty`

`public interface ITransitionProperty`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionProperty.cs`.

| Member | Signature |
|---|---|
| `Path` | `string Path { get; }` |
| `PropertyType` | `Type PropertyType { get; }` |
| `PropertyInfo` | `PropertyInfo PropertyInfo { get; }` |
| `Segments` | `IReadOnlyList<PropertyInfo> Segments { get; }` |
| `CanRead` / `CanWrite` | `bool CanRead { get; }` / `bool CanWrite { get; }` |
| `GetValue` | `object? GetValue(object target)` |
| `SetValue` | `bool SetValue(object target, object? value)` |

### Interface: `ISampler`

`public interface ISampler`

Stateless, thread-safe sampler. A sampler is normally a shared singleton registered in `InterpolatorCore.NativeInterpolators`. `InterpolatorCore.Prepare` calls `NormalizeStart` / `NormalizeEnd` once per property when a run starts, and the interpreter then calls `InsertFrame` once per sampled frame.

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`.

| Member | Signature | Description |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | Value to write at `t <= 0`. May return a copy so the target never aliases the shared start instance. |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | Value to write at `t >= 1`. May return a copy for the same aliasing reason. |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | Computes the interpolated frame at `t ∈ [0, 1]` and writes it to `property` on `target`. `working` is a per-animation reusable scratch object (created lazily via `ref` on the first middle-frame call). |

**Notes:**
- Endpoints are handled inside `InsertFrame`; implementations must not mutate the `start` / `end` arguments.
- The sampler a theme switch uses is resolved by property type via `InterpolatorCore.TryGetInterpolator`, inside `InterpolatorCore.Prepare`.

### Interface: `ISampleable`

`public interface ISampleable { IReadOnlyList<ITransitionProperty> GetAnimatableMembers(); object? CreateFrameValue(IReadOnlyList<object?> memberValues); }`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`.

**Notes:**
- Declares which members of a type are animatable (one level) and how to rebuild a value from interpolated members. Used during the transition feature's capture/`Prepare` for property types that have no registered sampler.
- The expansion does take part in a theme switch: `InterpolatorCore.Prepare`, which the scheduler runs, falls back to struct `ISampleable` assembly when no sampler is registered for a value type. `ThemeManager` itself only consults the registry, and only to decide whether a property has a sampler at all (`ThemeManager.cs`, `PrepareSamplers`).

### Interface: `ITransitionEffectCore`

`public interface ITransitionEffectCore`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionEffect.cs`.

| Member | Type / Signature |
|---|---|
| `FPS` | `int FPS { get; set; }` |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }` |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| Events | `event EventHandler<TransitionEventArgs> Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` |
| Invoke methods | `void InvokeAwake(object, TransitionEventArgs)`, `InvokeStart`, `InvokeUpdate`, `InvokeLateUpdate`, `InvokeCompleted`, `InvokeCancled`, `InvokeFinally` |
| `Clone` | `ITransitionEffectCore Clone()` |

**Notes:**
- Since a theme switch runs on the transition system, the whole effect is honoured: `Duration` and `Ease` time a pass, `FPS` caps the sample rate, `IsAutoReverse` adds a reverse pass, `LoopTime` repeats, and the lifecycle events fire. *Verified by:* `ThemeTransitionTests.Switch_HonoursAutoReverseAndLoopTime`.
- The effect is used as given and is read per frame by every target, so it must be the platform's own effect type and must not be mutated while a switch that uses it is running. The effect type also decides whether a platform can carry the switch at all: `InterpolatorCore.CreateScheduler` returns `null` for an effect that is not its own `ITransitionEffect<TPriority>`.
- The base implementation `TransitionEffectCore` defaults `FPS = 60`, `Duration = 0 ms`, `Ease = Eases.Default`, `IsAutoReverse = false`, `LoopTime = 0`. The adapter presets are listed in [04 PlatformAdapters](../04_PlatformAdapters/index.md).

### Interface: `IEaseCalculator` and Static Class: `Eases`

`public interface IEaseCalculator { double Ease(double t); }`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs` and `Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`.

| Member | Description |
|---|---|
| `Eases.Default` | `IEaseCalculator` — linear (`Ease(t) = t`, backed by `EaseDefault`). The default of `TransitionEffectCore.Ease`; an un-animated `ThemeManager.Jump` has no pass and never consults it. |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | Nested static classes, each exposing `In`, `Out`, `InOut` returning `IEaseCalculator`. |

**Notes:**
- The full ease catalogue is documented under the transition feature's Eases section (`2_API/03_transition`).
