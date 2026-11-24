# Transition and theme

Namespaces: `VeloxDev.TransitionSystem`, `VeloxDev.Adapters.NativeSamplers`, `VeloxDev.DynamicTheme`.

The Razor adapter runs the shared transition engine on `NonPriority` and registers a string sampler, so colours written as CSS strings can animate. Theme converters produce values a Razor view can render.

## Class: Transition

`public class Transition : TransitionCore` — untyped base for shared effect declarations.

## Class: Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, NonPriority> where T : class`

| Signature | Returns | Description |
| --- | --- | --- |
| `Create()` | `Transition<T>` | Creates an empty transition. |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | Configures the effect. |
| `Effect(TransitionEffect effect)` | `Transition<T>` | Uses the supplied effect. |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, string?>>, string?, object?)` | `Transition<T>` | String/CSS-colour target. |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | Typed overload. |
| `Property(Expression<Func<T, decimal>>, decimal, object?)` | `Transition<T>` | Typed overload. |
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

## Class: State / TransitionEffect / TransitionEffects

| Type | Base | Public surface |
| --- | --- | --- |
| `State` | `StateCore` | Per-transition property snapshot. |
| `TransitionEffect` | `TransitionEffectCore` | Duration, easing, FPS, loop and auto-reverse settings. |
| `TransitionEffects` | static | `Empty` (zero), `Theme` (0.46 s), `Hover` (0.32 s). |

## Class: Interpolator

`public class Interpolator : InterpolatorCore`

Registers `StringSampler` for `string` in its static constructor.

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` creates a scheduler only for `NonPriority` effects.

## Class: TransitionScheduler / TransitionInterpreter / UIThreadInspector

| Type | Base | Public surface |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | Inherited scheduling surface. |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect>` | Inherited interpreter surface. |
| `UIThreadInspector` | `TransitionHostBase<NonPriority>` | `static void CaptureUIThread()`, `static void NotifyShutdown()`, `override bool IsAlive`, `override ThreadRef ThreadFor(object target)`. |

`CaptureUIThread()` records the renderer thread; `NotifyShutdown()` marks the host dead so pending schedulers stop. A Blazor host should call both at circuit start and end.

## Class: StringSampler

`public class StringSampler : ISampler` — namespace `VeloxDev.Adapters.NativeSamplers`.

Implements `NormalizeStart`, `NormalizeEnd` and `InsertFrame`. It interpolates CSS colour strings (3/4/6/8-digit hex, `rgb()`, `rgba()` or a known colour name) channel by channel; non-colour strings stay at the start value until the end frame.

## Theme converters

Namespace `VeloxDev.DynamicTheme`. Each implements `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)` and returns `null` when it cannot convert.

| Converter | Output | Accepted parameters |
| --- | --- | --- |
| `DoubleConverter` | `double` | `double`, `int`, `float`, invariant numeric string, or any `IConvertible`. |
| `StringConverter` | `string?` | `parameters[0]?.ToString()`. |
| `IntConverter` | `int` | `int`, `double`, `float`, invariant numeric string, or any `IConvertible`. |
| `BoolConverter` | `bool` | `bool`, parseable string, or `int` (`0` is false). |

### Example

```csharp
var transition = Transition<MyViewModel>.Create()
    .Effect(TransitionEffects.Theme)
    .Property(vm => vm.Accent, "#FF38BDF8");
// Source: source
```
