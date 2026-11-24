# Transition and theme bridges

The WinUI adapter contributes the platform half of the transition pipeline and the runtime-theme value converters. Their member-level API belongs to the Transition Animation and Runtime Themes features; this page lists the types this assembly supplies.

## Namespaces

- `VeloxDev.TransitionSystem` — the transition pipeline closure.
- `VeloxDev.Adapters.NativeSamplers` — the WinUI samplers.
- `VeloxDev.DynamicTheme` — the theme value converters.

All are in assembly `VeloxDev.WinUI`.

## Transition system

| Type | Role |
| --- | --- |
| `Transition` | Non-generic transition declaration base. |
| `Transition<T>` | Typed declaration closed over a target type. |
| `TransitionEffect` / `TransitionEffects` | Effect declaration and predefined effects (a class, not a static class on this adapter). |
| `TransitionInterpreter` | Applies a declaration to a WinUI target; `partial` here. |
| `TransitionScheduler<TTarget>` | Drives frames on the WinUI dispatcher. |
| `Interpolator` | Sampler dispatch. |
| `UIThreadInspector` | Reports UI-thread affinity. |
| `State` | Captured animatable state. |

### Native samplers

`BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `GridLengthSampler`, `PointSampler`, `ProjectionSampler`, `RectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler`.

## Theme converters

| Type | Converts |
| --- | --- |
| `BrushConverter` | Theme value → `Brush` |
| `ColorConverter` | Theme value → `Color` |
| `CornerRadiusConverter` | Theme value → `CornerRadius` |
| `DoubleConverter` | Theme value → `double` |
| `ObjectConverter` | Theme value → `object` |
| `PointConverter` | Theme value → `Point` |
| `ThicknessConverter` | Theme value → `Thickness` |

```csharp
using Microsoft.UI.Xaml.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**Expected result:** the WinUI assembly supplies these types so a declaration written against Core runs on WinUI. Its distinctive samplers are `GridLengthSampler` and `ProjectionSampler`; the projection sampler is what animates the `Projection` needed by WinUI composition effects.
