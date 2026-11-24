# Platform Adapter Types

Each adapter supplies the same role set over its own framework: a fluent `Transition<T>`, a `State`, an `Interpolator` with the platform's samplers, a `TransitionEffect` and `TransitionEffects`, and the scheduler/interpreter/host trio. The public shapes below are the WPF adapter; the other six adapters mirror the names and the fluent surface.

## VeloxDev.TransitionSystem (every adapter)

### Class: Transition (non-generic)

The non-generic entry type, deriving from `TransitionCore`. Its static members (`Pause`, `Resume`, `SetRate`, `Seek`, `Exit`, `Position`, `Cycle`, `IsPaused`, `Rate`) address any target without naming its type.

**Signature:** `public class Transition : TransitionCore`

### Class: Transition<T> (generic)

**Signature:**
`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, DispatcherPriority> where T : class`

`DispatcherPriority` is the WPF priority type; Avalonia, WinUI and MAUI use their own dispatcher priority type, and the other adapters supply their own.

| Member | Signature | Description |
|---|---|---|
| `Create` | `static Transition<T> Create()` | Starts an empty chain. |
| `Effect` | `Transition<T> Effect(Action<TransitionEffect> effectSetter)` | Configures the effect through a setter. |
| `Effect` | `Transition<T> Effect(TransitionEffect effect)` | Uses the given effect. |
| `Property<TValue>` | `Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null)` | Sets one property's end value; options are passed to the sampler. |

The WPF adapter adds closed overloads for the framework's value types so a lambda binds without an explicit cast. The list below is the WPF set; each adapter declares the equivalents its framework needs.

| Value type | Notes |
|---|---|
| `double`, `int`, `float`, `decimal` | Primitive samplers |
| `Point`, `Size`, `Rect`, `Vector`, `Color`, `Thickness`, `CornerRadius` | WPF value types |
| `Point3D`, `Vector3D` | 3D value types |
| `Brush?`, `DropShadowEffect?`, `Transform?` | Reference types with dedicated samplers |
| `Transform` collection | Overload takes `ICollection<Transform>`; one element is assigned directly to preserve its runtime type, several are wrapped in a `TransformGroup` |
| `System.Drawing.Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF` | `System.Drawing` equivalents |
| `System.Numerics.Vector2`, `Vector3`, `Vector4`, `Quaternion` | Excluded on `netstandard2.0` |

`interpolationOptions` is stored per property and passed unchanged to `ISampler.InsertFrame`.

### Class: State

`public class State : StateCore` — the adapter's concrete frame state.

### Class: Interpolator

The adapter's sampler registry, deriving from `InterpolatorCore`.

**Signature:** `public class Interpolator : InterpolatorCore`

Its static constructor registers the platform samplers. WPF registers `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `Effect` (not `DropShadowEffect`, so a property declared as `Effect` resolves), `Point3D` and `Vector3D`. It overrides `CreateScheduler` to return the platform scheduler when the effect is typed for that platform's priority.

### Class: TransitionEffect

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>` — WPF's effect, with `Priority` defaulting to `DispatcherPriority.Render`.

### Class: TransitionEffects

Shared effect instances.

**Signature:** `public static class TransitionEffects`

| Member | Type | Value |
|---|---|---|
| `Empty` | `static TransitionEffect { get; set; }` | `Duration = 0` |
| `Theme` | `static TransitionEffect { get; set; }` | `Duration = 0.46 s` |
| `Hover` | `static TransitionEffect { get; set; }` | `Duration = 0.32 s` |

These are read per frame; do not mutate one while a switch using it is running.

### Class: TransitionInterpreter

`public class TransitionInterpreter : TransitionInterpreterCore<TransitionEffect, DispatcherPriority>`

### Class: TransitionScheduler

`public class TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>`

### Class: UIThreadInspector

`public class UIThreadInspector : TransitionHostBase<DispatcherPriority>` — the host that maps a target to its Dispatcher and posts work back.

## Adapter availability

All seven adapters declare `Transition`, `Transition<T>`, `State`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `TransitionInterpreter`, `TransitionScheduler` and `UIThreadInspector`.

| Adapter | Platform sampler types (namespace `VeloxDev.Adapters.NativeSamplers`) |
|---|---|
| WPF | `BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `DropShadowEffectSampler`, `Point3DSampler`, `PointSampler`, `RectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler`, `Vector3DSampler`, `VectorSampler` |
| Avalonia | `BoxShadowsSampler`, `BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `GridLengthSampler`, `PixelPointSampler`, `PixelRectSampler`, `PixelSizeSampler`, `PointSampler`, `RelativePointSampler`, `RelativeRectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler` |
| WinUI | `BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `GridLengthSampler`, `PointSampler`, `ProjectionSampler`, `RectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler` |
| MAUI | `BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `PointFSampler`, `PointSampler`, `RectFSampler`, `RectSampler`, `ShadowSampler`, `SizeFSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler` |
| WinForms | `BrushSampler`, `MatrixSampler`, `NullableRectangleFSampler`, `PaddingSampler`, `ThicknessSampler`, `Transform3DSampler` |
| Razor | `StringSampler` |
| Jalium | `BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `PointSampler`, `RectSampler`, `SizeSampler`, `ThicknessSampler`, `Transform3DSampler`, `TransformSampler` |

## Example

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle { RenderTransform = new TranslateTransform() };

Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.4d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(TransitionEffects.Hover)
    .Execute(box);

Transition.SetRate(box, 0.5d);
```

See [Transition Animation quick start](../../../1_QuickStart/12_transition-animation/index.md) for a complete window.
