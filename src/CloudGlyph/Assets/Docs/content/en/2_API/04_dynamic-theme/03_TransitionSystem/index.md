# API — Dynamic Theme · Backing Engine (TransitionSystem)

The Dynamic Theme feature drives its animation through the TransitionSystem engine. `InterpolatorCore` and the `ITransitionEffectCore`/`IEaseCalculator` contracts are shared with the transition feature; the theme feature uses them to sample themed property values and to time the switch.

> Namespace note: `ISampler`, `ISampleable`, `ITransitionEffectCore`, `IEaseCalculator`, and `Eases` are declared in `VeloxDev.TransitionSystem`; the abstract `InterpolatorCore` and the concrete `SamplerSet` are declared in `VeloxDev.TransitionSystem.Abstractions`.

## Namespace: `VeloxDev.TransitionSystem.Abstractions`

### Abstract Class: `InterpolatorCore`

`public abstract class InterpolatorCore`

Base for all value samplers — the former frame-interpolator hierarchy (`IValueInterpolator`, `IInterpolable`, the generic `InterpolatorCore<TOutputCore[, TPriorityCore]>` forms, `InterpolatorOutputBase`) is gone; `InterpolatorCore` is now a single non-generic class that no longer implements an interface. The static constructor pre-registers native samplers for primitive and BCL types: `double`, `float`, `int`, `long`, `Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF`, and (outside `NETSTANDARD2_0`) `Vector2`, `Vector3`, `Vector4`, `Quaternion`.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`.

##### Static Members

| Member | Signature | Description |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampleable> NativeInterpolators { get; protected set; }` | Registry of per-type sampleable definitions. |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampleable? sampleable)` | Looks up a sampleable for a type. |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampleable sampleable)` | Registers a sampleable (atomic add-or-update). |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampleable? sampleable)` | Removes a sampleable. |

**Instance member:** `public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` — resolves the per-property `ISampleable` (custom from state → registered by property type → the value IS `ISampleable`), calls `Normalize` once, and stores each `(ITransitionProperty, ISampler, start, end, options)` entry in a `SamplerSet`. Replaces the old `Interpolate(...) IFrameSequenceCore` instance method.

**Notes:**
- The platform `Interpolator` (adapter) extends the non-generic `InterpolatorCore` and registers platform samplers in its static constructor.
- `RegisterInterpolator` is last-writer-wins and atomic (`AddOrUpdate`).

### Class: `SamplerSet`

`public sealed class SamplerSet`

The prepared per-property sampler container (renamed from `FrameUpdaterSet`; replaces `IFrameSequence` + `InterpolatorOutputBase`). Non-generic: it holds the per-property `(ITransitionProperty, ISampler, start, end, options)` entries and the Core-level inspector, and priority flows through the `object?` overload of `IUIThreadInspectorCore.ProtectedInvoke`. The animation's cancellation token is attached via `SetCancellation`, giving `Apply` the former `ICancellableFrameSequence` stale-frame guard.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/SamplerSet.cs`.

| Member | Signature | Description |
|---|---|---|
| `Apply` | `public void Apply(object target, double t, object? priority = default)` | Marshals to the UI thread and calls each `sampler.Update(target, property, start, end, options, t)`; returns immediately when the animation is cancelled or the app is no longer alive, so stale queued frames never overwrite a reset result. |
| `CanSetValue` | `public bool CanSetValue()` | `true` while `inspector.IsAppAlive()`. |

## Namespace: `VeloxDev.TransitionSystem`

### Interface: `ISampler`

`public interface ISampler { void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t); }`

Stateless, thread-safe, shared-singleton sampling processor that directly updates the property at a normalized time `t ∈ [0,1]`: `t <= 0` writes the exact `start`, `t >= 1` the exact `end`, and `0 < t < 1` computes-and-assigns (value types) or MUTATES the live `start` instance in place (reference types). The caller (interpreter) applies easing and clamps the time before invoking. Replaces `IValueInterpolator` / `IInterpolable`.

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`.

### Interface: `ISampleable`

`public interface ISampleable { ISampler Normalize(object? start, object? end, object? options); }`

可采样定义 (sampleable definition) at the type level. User-defined types implement it to be directly animatable without registering a sampler. `Normalize` normalizes start/end once (called by the interpreter when it is created with the FrameState, per animated property) and returns the stateless `ISampler`. The former `IInPlaceSampler.CreateUpdater` / in-place `FrameUpdater` classes are now the per-type `ISampler.Update`: reference-type samplers mutate `start` in place inside `Update`; value types compute-and-assign.

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`.

### Interface: `ITransitionEffectCore`

`public interface ITransitionEffectCore`

Describes a transition effect: frame rate, duration, loop/easing, and lifecycle events.

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
- Default `FPS` is 60; default `Duration` is zero; default `Ease` is `Eases.Default`.
- `FPS` is the **maximum sample-rate cap** — the interpreter's sampling loop is Stopwatch-driven (`t = elapsed / Duration`) and does not step to `FPS` frames; the yield interval is `1000 / FPS` ms.
- `TransitionEffectCore` (base implementation) backs the adapter's `TransitionEffect`.

### Interface: `IEaseCalculator`

`public interface IEaseCalculator { double Ease(double t); }`

Source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs`.

**Notes:**
- Implementations map a normalized time `t ∈ [0, 1]` to an eased value.

### Static Class: `Eases`

Factory of `IEaseCalculator` strategies.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`.

| Member | Description |
|---|---|
| `Default` | `IEaseCalculator` — linear (`t → t`). |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | Nested static classes, each exposing `In`, `Out`, `InOut` members returning `IEaseCalculator`. |

**Notes:**
- `EaseDefault` is the concrete class behind `Eases.Default`.
- `ThemeManager.Jump` uses `Eases.Default` for its zero-duration pass.
