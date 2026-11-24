# Transition system

Namespaces: `VeloxDev.TransitionSystem`, `VeloxDev.Adapters.NativeSamplers`.

The Jalium adapter closes the shared transition engine over `DispatcherPriority` and registers Jalium media samplers. There is no `VeloxDev.DynamicTheme` converter set on this platform.

## Class: Transition

`public class Transition : TransitionCore` — untyped base for shared effect declarations.

## Class: Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, DispatcherPriority> where T : class`

| Signature | Returns | Description |
| --- | --- | --- |
| `Create()` | `Transition<T>` | Creates an empty transition. |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | Configures the effect. |
| `Effect(TransitionEffect effect)` | `Transition<T>` | Uses the supplied effect. |
| `Property<TValue>(Expression<Func<T, TValue>>, TValue, object?)` | `Transition<T>` | Generic target. |
| `Property(Expression<Func<T, Brush?>>, Brush?, object?)` | `Transition<T>` | Brush target. |
| `Property(Expression<Func<T, Transform?>>, ICollection<Transform>, object?)` | `Transition<T>` | Transform collection; a single item is assigned directly to preserve its runtime type. |
| `Property(Expression<Func<T, Transform3D?>>, Transform3D?, object?)` | `Transition<T>` | 3D transform target. |
| `Property(Expression<Func<T, Point>>, Point, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Rect>>, Rect, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Thickness>>, Thickness, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, CornerRadius>>, CornerRadius, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Size>>, Size, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, Color>>, Color, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | Typed overload. |

## Class: State / TransitionEffect / TransitionEffects

| Type | Base | Public surface |
| --- | --- | --- |
| `State` | `StateCore` | Per-transition property snapshot. |
| `TransitionEffect` | `TransitionEffectCore<DispatcherPriority>` | Duration, easing, FPS, loop, auto-reverse and priority. |
| `TransitionEffects` | static | `Empty` (zero), `Theme` (0.46 s), `Hover` (0.32 s). |

## Class: Interpolator

`public class Interpolator : InterpolatorCore`

Registers these exact types in its static constructor: `Point`, `Rect`, `Thickness`, `CornerRadius`, `Size`, `Color`, `Brush`, `SolidColorBrush`, `Transform` and `Media3D.Transform3D`. Both `Brush` and `SolidColorBrush` are registered so a property declared as either type can animate.

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` creates a scheduler only for `DispatcherPriority` effects.

## Class: TransitionScheduler / TransitionInterpreter / UIThreadInspector

| Type | Base | Public surface |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | Inherited scheduling surface. |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | Inherited interpreter surface. |
| `UIThreadInspector` | `TransitionHostBase<DispatcherPriority>` | `override ThreadRef ThreadFor(object target)`. |

The host type reports `DispatcherPriority`, so transitions marshal through Jalium's dispatcher.

## Samplers

Namespace `VeloxDev.Adapters.NativeSamplers`. Every sampler implements `ISampler` with `NormalizeStart`, `NormalizeEnd` and `InsertFrame`.

| Type | Interpolates |
| --- | --- |
| `BrushSampler` | `Brush` (and `SolidColorBrush`). |
| `ColorSampler` | `Color`. |
| `CornerRadiusSampler` | `CornerRadius`. |
| `PointSampler` | `Point`. |
| `RectSampler` | `Rect`. |
| `SizeSampler` | `Size`. |
| `ThicknessSampler` | `Thickness`. |
| `TransformSampler` | `Transform`. |
| `Transform3DSampler` | `Media3D.Transform3D`. |

### Example

```csharp
var transition = Transition<MyCard>.Create()
    .Effect(TransitionEffects.Hover)
    .Property(card => card.CornerRadius, new CornerRadius(12));
// Source: source
```
