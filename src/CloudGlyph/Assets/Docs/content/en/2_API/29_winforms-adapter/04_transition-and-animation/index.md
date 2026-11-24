# Transition and animation

Namespaces: `VeloxDev.TransitionSystem`, `VeloxDev.Adapters.NativeSamplers`, `VeloxDev.WinForms.XamlAnimation`.

The WinForms adapter closes the shared transition engine over Easel visuals. The fluent declaration, chaining and easing families are the same surface documented for Transition Animation; this page lists the adapter's concrete types and its Easel bridge.

## Class: Transition

`public class Transition : TransitionCore` — untyped base for shared effect declarations.

## Class: Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, NonPriority> where T : class`

| Signature | Returns | Description |
| --- | --- | --- |
| `Create()` | `Transition<T>` | Creates an empty transition. |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | Configures the effect. |
| `Effect(TransitionEffect effect)` | `Transition<T>` | Uses the supplied effect. |
| `Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null)` | `Transition<T>` | Sets a property target. |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, decimal>>, decimal, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Padding>>, Padding, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Point>>, Point, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, PointF>>, PointF, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Size>>, Size, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, SizeF>>, SizeF, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Color>>, Color, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Rectangle>>, Rectangle, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, RectangleF>>, RectangleF, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Vector2>>, Vector2, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Vector3>>, Vector3, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Vector4>>, Vector4, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Quaternion>>, Quaternion, object?)` | `Transition<T>` | Typed overload. |

The typed overloads are overload resolution aids; they all store a value in `State`.

## Class: State

`public class State : StateCore` — per-transition property snapshot.

## Class: TransitionEffect

`public class TransitionEffect : TransitionEffectCore` — duration, easing, FPS, loop and auto-reverse settings.

## Class: TransitionEffects

`public static class TransitionEffects`

| Member | Type | Default |
| --- | --- | --- |
| `Empty` | `TransitionEffect` | Zero duration; values snap. |
| `Theme` | `TransitionEffect` | 0.46 s. |
| `Hover` | `TransitionEffect` | 0.32 s. |

## Class: Interpolator

`public class Interpolator : InterpolatorCore`

Registers Easel and `System.Drawing` samplers in its static constructor: `Padding`, `Thickness`, `Easel.Brush`, `Matrix`, `Easel.Transform3D` and `RectangleF?`.

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` creates a scheduler only when the effect declares `NonPriority`.

## Class: TransitionScheduler / TransitionInterpreter / UIThreadInspector

| Type | Base | Public surface |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | Inherited scheduling surface only. |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect>` | Inherited interpreter surface; owns a `PostedFramePacer`. |
| `UIThreadInspector` | `TransitionHostBase<NonPriority>` | `static void CaptureUIThread()`, `override bool IsAlive`, `override ThreadRef ThreadFor(object target)`. |

`UIThreadInspector.CaptureUIThread()` records the WinForms UI thread so later transitions marshal to it. It throws `InvalidOperationException` when it is not called on a WinForms UI thread before `Application.Run`.

## Samplers

Namespace `VeloxDev.Adapters.NativeSamplers`. Every sampler implements `ISampler` with `NormalizeStart`, `NormalizeEnd` and `InsertFrame`.

| Type | Interpolates |
| --- | --- |
| `BrushSampler` | Easel `Brush`. |
| `MatrixSampler` | `System.Drawing.Drawing2D.Matrix`. |
| `NullableRectangleFSampler` | `RectangleF?`. |
| `PaddingSampler` | `Padding`. |
| `ThicknessSampler` | `Easel.Controls.Thickness`. |
| `Transform3DSampler` | `Easel.Transform3D`. |

## Class: EaselAnimationBootstrap

`public static class EaselAnimationBootstrap` — namespace `VeloxDev.WinForms.XamlAnimation`.

| Signature | Returns | Description |
| --- | --- | --- |
| `EnsureRegistered()` | `void` | Assigns the VeloxDev animator unless the host already supplied one. |

A module initializer calls `EnsureRegistered` when code from the assembly first runs. A host that installs the package only for the animation backend and never touches another type should call it once at startup.

### Example

```csharp
EaselAnimationBootstrap.EnsureRegistered();
// Source: source
```

### Notes

- The bridge uses `Transition<EaselVisualElement>` so runs are registered and `TransitionCore.Exit` can stop them.
- `Interpolator`'s static constructor must run before `CanAnimate` checks the registry; the animator triggers it explicitly.

## Theme value converters

The `VeloxDev.DynamicTheme` converters for `System.Drawing` are listed in [Theme converters](../05_theme-converters/index.md).
