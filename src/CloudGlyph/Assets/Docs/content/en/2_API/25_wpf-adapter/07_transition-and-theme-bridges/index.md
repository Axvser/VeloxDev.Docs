# Transition and theme bridges

The WPF adapter also carries the platform half of two Core systems: the transition pipeline and the runtime-theme value converters. Their member-level API belongs to the Transition Animation and Runtime Themes features; this page lists the types the WPF assembly contributes, so an adapter reader can find them without digging through the project.

## Namespaces

- `VeloxDev.TransitionSystem` — the transition pipeline closure.
- `VeloxDev.Adapters.NativeSamplers` — the WPF samplers.
- `VeloxDev.DynamicTheme` — the theme value converters.

All are in assembly `VeloxDev.WPF`.

## Transition system

| Type | Role |
| --- | --- |
| `Transition` | Non-generic transition declaration base. |
| `Transition<T>` | Typed declaration closed over a target type. |
| `TransitionEffect` / `TransitionEffects` | Effect declaration and the predefined effect set. |
| `TransitionInterpreter` | Applies a declaration to a WPF target. |
| `TransitionScheduler` | Drives frames on the WPF dispatcher. |
| `Interpolator` | The WPF sampler dispatch. |
| `UIThreadInspector` | Reports whether the calling thread is the UI thread. |
| `State` | Captured animatable state. |

### Native samplers

`BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `DropShadowEffectSampler`, `PointSampler`, `Point3DSampler`, `RectSampler`, `SizeSampler`, `ThicknessSampler`, `TransformSampler`, `VectorSampler`, `Vector3DSampler`.

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
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**Expected result:** the WPF assembly supplies these types so a transition or theme declaration written once in Core runs on WPF without a second platform wrapper. The sampler differences are the WPF-only `DropShadowEffectSampler`, `Point3DSampler`, `VectorSampler` and `Vector3DSampler`; other adapters ship a different set.
