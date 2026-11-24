# Transition and theme bridges

The Avalonia adapter contributes the platform half of the transition pipeline and the runtime-theme value converters. Their member-level API belongs to the Transition Animation and Runtime Themes features; this page lists the types this assembly supplies.

## Namespaces

- `VeloxDev.TransitionSystem` — the transition pipeline closure.
- `VeloxDev.Adapters.NativeSamplers` — the Avalonia samplers.
- `VeloxDev.DynamicTheme` — the theme value converters.

All are in assembly `VeloxDev.Avalonia`.

## Transition system

| Type | Role |
| --- | --- |
| `Transition` | Non-generic transition declaration base. |
| `Transition<T>` | Typed declaration closed over a target type. |
| `TransitionEffect` / `TransitionEffects` | Effect declaration and predefined effects. |
| `TransitionInterpreter` | Applies a declaration to an Avalonia target. |
| `TransitionScheduler<TTarget>` | Drives frames on the Avalonia dispatcher. |
| `Interpolator` | Sampler dispatch. |
| `UIThreadInspector` | Reports UI-thread affinity. |
| `State` | Captured animatable state. |

### Native samplers

`BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `BoxShadowsSampler`, `GridLengthSampler`, `PointSampler`, `PixelPointSampler`, `PixelRectSampler`, `PixelSizeSampler`, `RelativePointSampler`, `RelativeRectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler`.

## Theme converters

| Type | Converts |
| --- | --- |
| `BrushConverter` | Theme value → `IBrush` |
| `ColorConverter` | Theme value → `Color` |
| `CornerRadiusConverter` | Theme value → `CornerRadius` |
| `DoubleConverter` | Theme value → `double` |
| `ObjectConverter` | Theme value → `object` |
| `PointConverter` | Theme value → `Point` |
| `ThicknessConverter` | Theme value → `Thickness` |

```csharp
using Avalonia.Controls.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**Expected result:** a transition or theme declaration written once against Core runs on Avalonia through these closures. The Avalonia-only samplers are the box-shadow, grid-length, pixel and relative-coordinate sets; WPF ships a different list.
