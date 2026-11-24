# Transition and theme bridges

The MAUI adapter contributes the platform half of the transition pipeline and the runtime-theme value converters. Their member-level API belongs to the Transition Animation and Runtime Themes features; this page lists the types this assembly supplies.

## Namespaces

- `VeloxDev.TransitionSystem` — the transition pipeline closure.
- `VeloxDev.Adapters.NativeSamplers` — the MAUI samplers.
- `VeloxDev.DynamicTheme` — the theme value converters.

All are in assembly `VeloxDev.MAUI`.

## Transition system

| Type | Role |
| --- | --- |
| `Transition` | Non-generic transition declaration base. |
| `Transition<T>` | Typed declaration closed over a target type. |
| `TransitionEffect` / `TransitionEffects` | Effect declaration and predefined effects. |
| `TransitionInterpreter` | Applies a declaration to a MAUI target; `partial` here. |
| `TransitionScheduler` | Drives frames on the MAUI dispatcher (not generic on this adapter). |
| `Interpolator` | Sampler dispatch. |
| `UIThreadInspector` | Reports UI-thread affinity. |
| `State` | Captured animatable state. |

### Native samplers

`BrushSampler`, `ColorSampler`, `CornerRadiusSampler`, `PointSampler`, `PointFSampler`, `RectSampler`, `RectFSampler`, `SizeSampler`, `SizeFSampler`, `ShadowSampler`, `ThicknessSampler`, `TransformSampler`.

The `…F` samplers work in `Microsoft.Maui.Graphics` floating-point structs; `ShadowSampler` is MAUI-only.

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
using Microsoft.Maui.Controls.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**Expected result:** a declaration written once against Core runs on MAUI through these closures. Its distinctive samplers are the `…F` floating-point set and `ShadowSampler`.
