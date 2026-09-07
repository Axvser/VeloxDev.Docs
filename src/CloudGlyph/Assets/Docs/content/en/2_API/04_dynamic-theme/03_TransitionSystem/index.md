# API — Dynamic Theme · Backing Engine (TransitionSystem)

The dynamic-theme feature animates themed properties through the TransitionSystem engine. `ThemeManager` does not drive the engine's high-level `Transition` / `SamplerSet` / `State` pipeline: it resolves a sampler per property type, normalizes start/end values, and then calls the sampler itself inside a Stopwatch-based loop. This page documents the engine surface that `ThemeManager` actually consumes; the full engine is documented by the transition feature.

> The engine contracts live in `VeloxDev.TransitionSystem`; the engine base types and the concrete `TransitionProperty` live in `VeloxDev.TransitionSystem.Abstractions`. The complete engine reference lives under the transition feature (`2_API/03_transition`).

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
| `Prepare` (instance, `virtual`) | `public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` | Normalizes every property in a state snapshot into a `SamplerSet`. Used by the transition feature, not by `ThemeManager`. |

**Notes:**
- `ThemeManager.PrepareSamplers` uses `InterpolatorCore.TryGetInterpolator` to resolve a property's sampler by `PropertyInfo.PropertyType`. When no sampler is registered for that type, the property falls back to a simple hold-until-end switch.
- The platform adapter `Interpolator` extends `InterpolatorCore` and registers platform samplers in its static constructor (see [04 PlatformAdapters](../04_PlatformAdapters/index.md)).

### Class: `TransitionProperty`

`public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

Compiled getter/setter implementation of `ITransitionProperty`. A property path is one or more `PropertyInfo` segments; reads and writes go through lazily compiled delegates. When an intermediate object is non-null but its runtime type does not match the path, reads return the sentinel `UnreadablePath` and writes return `false`, so callers skip the property instead of treating it as null/identity.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`.

| Member | Signature | Description |
|---|---|---|
| `UnreadablePath` | `public static readonly object UnreadablePath` | Sentinel returned by `GetValue` when the path is invalid for the current target. |
| `FromProperty` | `public static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | Creates a single-segment path for one property. |
| `Members<TSource>` | `public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | Builds readable+writable member paths from expressions (for `ISampleable`). |
| `ReadableMembers<TSource>` | `public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | Builds readable member paths (for struct `ISampleable` assembly). |
| `Combine` | `public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix)` | Concatenates two paths into one. |
| `TryCreate` | `public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | Parses an expression tree into a path. |
| `Path` | `string Path` | Dot-joined segment names. |
| `PropertyType` / `PropertyInfo` / `Segments` | `Type` / `PropertyInfo` / `IReadOnlyList<PropertyInfo>` | Type, final segment info, and full segment list. |
| `CanRead` / `CanWrite` | `bool` | Readability of all segments / writability of the final segment. |
| `GetValue` / `SetValue` | `object? GetValue(object target)` / `bool SetValue(object target, object? value)` | Compiled path read/write. |

**Notes:**
- `ThemeManager.PrepareSamplers` wraps each animated property with `TransitionProperty.FromProperty(propertyInfo)` and later writes endpoint/working values through `SetValue`.

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

Stateless, thread-safe sampler. A sampler is normally a shared singleton registered in `InterpolatorCore.NativeInterpolators`. `ThemeManager` calls `NormalizeStart` / `NormalizeEnd` once per property at switch time and then `InsertFrame` once per sampled frame.

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`.

| Member | Signature | Description |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | Value to write at `t <= 0`. May return a copy so the target never aliases the shared start instance. |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | Value to write at `t >= 1`. May return a copy for the same aliasing reason. |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | Computes the interpolated frame at `t ∈ [0, 1]` and writes it to `property` on `target`. `working` is a per-animation reusable scratch object (created lazily via `ref` on the first middle-frame call). |

**Notes:**
- Endpoints are handled inside `InsertFrame`; implementations must not mutate the `start` / `end` arguments.
- A registered sampler is resolved for the theme switch by property type via `InterpolatorCore.TryGetInterpolator`.

### Interface: `ISampleable`

`public interface ISampleable { IReadOnlyList<ITransitionProperty> GetAnimatableMembers(); object? CreateFrameValue(IReadOnlyList<object?> memberValues); }`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`.

**Notes:**
- Declares which members of a type are animatable (one level) and how to rebuild a value from interpolated members. Used during the transition feature's capture/`Prepare` for property types that have no registered sampler.
- `ThemeManager` resolves samplers from the registry only, so `ISampleable` member expansion is not part of a theme switch.

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
- `ThemeManager` reads exactly two members: `Ease` (to compute the eased time) and `Duration` (to derive the total elapsed time in milliseconds). `FPS`, `IsAutoReverse`, `LoopTime`, the lifecycle events and `Clone` belong to the higher-level engine pipeline.
- The base implementation `TransitionEffectCore` defaults `FPS = 60`, `Duration = 0 ms`, `Ease = Eases.Default`. The adapter presets that the theme demos use are listed in [04 PlatformAdapters](../04_PlatformAdapters/index.md).

### Interface: `IEaseCalculator` and Static Class: `Eases`

`public interface IEaseCalculator { double Ease(double t); }`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs` and `Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`.

| Member | Description |
|---|---|
| `Eases.Default` | `IEaseCalculator` — linear (`Ease(t) = t`, backed by `EaseDefault`). Used by `ThemeManager.Jump` for its zero-duration pass. |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | Nested static classes, each exposing `In`, `Out`, `InOut` returning `IEaseCalculator`. |

**Notes:**
- The full ease catalogue is documented under the transition feature's Eases section (`2_API/03_transition`).
