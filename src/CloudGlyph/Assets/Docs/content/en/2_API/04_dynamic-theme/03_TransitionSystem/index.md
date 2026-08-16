# API — Dynamic Theme · Backing Engine (TransitionSystem)

The Dynamic Theme feature drives its animation through the TransitionSystem engine. `InterpolatorCore` and the `ITransitionEffectCore`/`IEaseCalculator` contracts are shared with the transition feature; the theme feature uses them to interpolate themed property values and to time the switch.

> Namespace note: `ITransitionEffectCore`, `IEaseCalculator`, and `Eases` are declared in `VeloxDev.TransitionSystem`; the abstract `InterpolatorCore` and its generic derived forms are declared in `VeloxDev.TransitionSystem.Abstractions`.

## Namespace: `VeloxDev.TransitionSystem.Abstractions`

### Abstract Class: `InterpolatorCore`

`public abstract class InterpolatorCore : IFrameInterpolatorCore`

Base for all frame interpolators. The static constructor pre-registers native interpolators for primitive and BCL types: `double`, `float`, `int`, `long`, `Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF`, and (outside `NETSTANDARD2_0`) `Vector2`, `Vector3`, `Vector4`, `Quaternion`.

Source: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`.

##### Static Members

| Member | Signature | Description |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` | Registry of per-type value interpolators. |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` | Looks up an interpolator for a type. |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` | Registers an interpolator (atomic add-or-update). |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` | Removes an interpolator. |

**Instance member:** `public abstract IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector);`

**Generic derived forms** (also declared in `VeloxDev.TransitionSystem.Abstractions`):
- `public abstract class InterpolatorCore<TOutputCore> : InterpolatorCore, IFrameInterpolator where TOutputCore : IFrameSequence, new()`
- `public abstract class InterpolatorCore<TOutputCore, TPriorityCore> : InterpolatorCore, IFrameInterpolator<TPriorityCore> where TOutputCore : IFrameSequence<TPriorityCore>, new()`

**Notes:**
- The platform `Interpolator` (adapter) extends `InterpolatorCore<InterpolatorOutput, DispatcherPriority>` and registers platform types in its static constructor.
- `RegisterInterpolator` is last-writer-wins and atomic (`AddOrUpdate`).

## Namespace: `VeloxDev.TransitionSystem`

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
- `ThemeManager.Jump` uses `Eases.Default` for its single frame.
