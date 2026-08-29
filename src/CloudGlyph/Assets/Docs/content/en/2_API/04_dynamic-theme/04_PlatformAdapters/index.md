# API — Dynamic Theme · Platform Adapters

The platform adapters (`VeloxDev.WPF` / `VeloxDev.Avalonia`) provide the concrete `Interpolator`, the transition effects, and the theme value converters. All types below live in namespace `VeloxDev.TransitionSystem` (interpolator / effects) or `VeloxDev.DynamicTheme` (value converters).

> Evidence: source `Src/Adapters/VeloxDev.WPF/PlatformAdapters/*`, `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/*`; demos `Examples/Theme/WPF/Demo`, `Examples/Theme/Avalonia/Demo`.

## Namespace: `VeloxDev.TransitionSystem`

### Class: `Interpolator` (adapter)

WPF: `public class Interpolator : InterpolatorCore`
Avalonia: `public class Interpolator : InterpolatorCore`

The adapter `Interpolator` extends the non-generic `InterpolatorCore` (the generic `InterpolatorCore<InterpolatorOutput, DispatcherPriority>` tiers were removed with the frame-sequence model). The static constructor registers platform samplers:

| Adapter | Registered property types |
|---|---|
| WPF (`VeloxDev.WPF`) | `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D` |
| Avalonia (`VeloxDev.Avalonia`) | `IBrush`, `ITransform`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows`, `GridLength` |

**Notes:**
- Each registered type maps to an `ISampleable, ISampler` implementation (e.g. `BrushSampler`, `ThicknessSampler`) in `NativeInterpolators` (`ConcurrentDictionary<Type, ISampleable>`).
- This is the instance passed to `ThemeManager.SetPlatformInterpolator<T>(T)`.

### Class: `TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>`

| Member | Value |
|---|---|
| `Priority` | `override DispatcherPriority Priority { get; set; } = DispatcherPriority.Render` |

**Notes:**
- Inherits `FPS` (default 60), `Duration`, `IsAutoReverse`, `LoopTime`, `Ease`, lifecycle events, and `Clone()` from `TransitionEffectCore`.

### Static Class: `TransitionEffects`

| Member | Value |
|---|---|
| `Empty` | `Duration = TimeSpan.Zero` |
| `Theme` | `Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `Duration = TimeSpan.FromSeconds(0.32)` |

**Notes:**
- `TransitionEffects.Theme` is the effect used by the theme demos for animated switches.

## Namespace: `VeloxDev.DynamicTheme`

### Value Converters

All implement `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`. Both adapters ship the same seven converters; the WPF implementations are in `Src/Adapters/VeloxDev.WPF/PlatformAdapters/ThemeValueConverters.cs`, the Avalonia ones in `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/ThemeValueConverters.cs`.

| Converter | Purpose | Accepted parameters |
|---|---|---|
| `DoubleConverter` | `double` value | `double`, `int`, `float`, or parseable `string` (invariant culture). |
| `PointConverter` | `Point` value | `"x,y"` string, or `[x, y]` numbers. |
| `ThicknessConverter` | `Thickness` value | `"uniform"`, `"h,v"`, `"l,t,r,b"` strings, or 1/2/4 numeric parameters. |
| `CornerRadiusConverter` | `CornerRadius` value | `"uniform"`, `"tl,tr,br,bl"` strings, or 1/4 numeric parameters. |
| `ColorConverter` | `Color` value | color-name/HEX string, ARGB `int`, or A/R/G/B components. |
| `BrushConverter` | `Brush` value | existing `Brush`, resource key, color string, or delegated `ColorConverter` result. |
| `ObjectConverter` | any `targetType` | single resource-key string; falls back to the platform type converter (`TypeDescriptor`/`TypeUtilities`). |

**Notes:**
- Converters are the strategy (`TConverter`) referenced by `ThemeConfigAttribute<TConverter, ...>`.
- `ObjectConverter` is used by the Avalonia demo; the WPF demo uses `BrushConverter`.
- WPF converters consult `Application.Current.Resources` (and merged dictionaries) for resource-key lookups; Avalonia converters use `Application.Current.TryFindResource`.
