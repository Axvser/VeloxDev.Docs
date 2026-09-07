# API — Dynamic Theme · Platform Adapters

The platform adapters supply the runtime pieces a theme switch needs on a concrete UI framework: the theme **value converters** (in namespace `VeloxDev.DynamicTheme`) that turn raw `[ThemeConfig]` parameters into platform values, and the **transition types** (in namespace `VeloxDev.TransitionSystem`) — the adapter `Interpolator`, `TransitionEffect`, and the `TransitionEffects` presets. This page covers the adapters exercised by the theme demos (`VeloxDev.WPF`, `VeloxDev.Avalonia`) and summarizes the converter sets shipped by the remaining adapters.

> Evidence: source under `Src/Adapters/VeloxDev.WPF/PlatformAdapters/**` and `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/**`; demos `Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo`.

## Namespace: `VeloxDev.TransitionSystem` — switch helpers

### Class: `Interpolator` (adapter)

`public class Interpolator : InterpolatorCore`

The adapter subclass of `InterpolatorCore` whose static constructor registers the framework's samplers (each mapped to an `ISampler` implementation, e.g. `BrushSampler`). This is the instance passed to `ThemeManager.SetPlatformInterpolator`:

```csharp
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

| Adapter | Registered property types |
|---|---|
| WPF (`VeloxDev.WPF`) | `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D` |
| Avalonia (`VeloxDev.Avalonia`) | `IBrush`, `ITransform`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows`, `GridLength` |

### Class: `TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>`

Adapter effect that overrides `Priority` to `DispatcherPriority.Render`. Inherits `FPS` (60), `Duration`, `IsAutoReverse`, `LoopTime`, `Ease`, lifecycle events, and `Clone()` from the engine base.

### Static Class: `TransitionEffects`

| Member | Value |
|---|---|
| `Empty` | `TransitionEffect` with `Duration = TimeSpan.Zero` |
| `Theme` | `TransitionEffect` with `Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `TransitionEffect` with `Duration = TimeSpan.FromSeconds(0.32)` |

**Notes:**
- `TransitionEffects.Theme` is the effect both theme demos pass to `ThemeManager.Transition<T>` for an animated switch.
- `ThemeManager.Jump<T>` performs an instantaneous switch and needs no effect.

## Namespace: `VeloxDev.DynamicTheme` — theme value converters

All converters implement `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`. They are defined in the adapter assemblies (referencing the core interface) under the same `VeloxDev.DynamicTheme` namespace, so a decorated class references them by unqualified name alongside `ThemeManager`. WPF implementations live in `Src/Adapters/VeloxDev.WPF/PlatformAdapters/ThemeValueConverters.cs`, Avalonia's in `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/ThemeValueConverters.cs`.

| Converter | Purpose | Accepted parameters (WPF / Avalonia) |
|---|---|---|
| `DoubleConverter` | `double` value | `double` / `int` / `float`, or an invariant-parseable `string`. |
| `PointConverter` | platform `Point` | `"x,y"` string (WPF splits, Avalonia calls `Point.Parse`), or `[x, y]` numbers. |
| `ThicknessConverter` | platform `Thickness` | uniform / `"h,v"` / `"l,t,r,b"` strings, or 1 / 2 / 4 numeric parameters. |
| `CornerRadiusConverter` | platform `CornerRadius` | uniform / `"tl,tr,br,bl"` strings, or 1 / 4 numeric parameters. |
| `ColorConverter` | platform `Color` | color-name/HEX string, ARGB `int`, or A/R/G/B components. |
| `BrushConverter` | platform brush | an existing brush (`Brush` in WPF, `IBrush` in Avalonia), a resource key, a color string, or a delegated `ColorConverter` result wrapped in a solid brush. |
| `ObjectConverter` | any `targetType` | a single resource-key string; falls back to the platform type converter (`TypeDescriptor` / `TypeUtilities`). |

**Notes:**
- WPF targets `System.Windows` / `System.Windows.Media` types and resolves string colors through `System.Windows.Media.BrushConverter`; resource lookups go through a shared internal `ThemeResourceLookup` helper that walks `Application.Current.Resources` and its merged dictionaries.
- Avalonia targets Avalonia types (`IBrush`, `Point`, ...), parses strings through the platform types' native parsers (`Point.Parse`, `Color.TryParse`, ...), prefers `Avalonia.Utilities.TypeUtilities.TryConvert`, and looks resources up via `Application.Current.TryFindResource`.
- The WPF demo annotates properties with `[ThemeConfig<BrushConverter, Light, Dark>(...)]`; the Avalonia demo uses `ObjectConverter` with `[ThemeConfig<ObjectConverter, Dark, Light>(...)]`.
- Converters are the `TConverter` strategy referenced by `ThemeConfigAttribute<TConverter, ...>` and are instantiated by the theme generator when a theme registers.

### Converters in the other adapters

The remaining framework adapters re-export the same pattern in their own `ThemeValueConverters.cs` files (all namespace `VeloxDev.DynamicTheme`): `VeloxDev.MAUI` and `VeloxDev.WinUI` ship the same seven converters; `VeloxDev.WinForms` ships thirteen (`DoubleConverter`, `IntConverter`, `FloatConverter`, `PointConverter`, `PointFConverter`, `SizeConverter`, `SizeFConverter`, `RectangleConverter`, `RectangleFConverter`, `PaddingConverter`, `ColorConverter`, `FontConverter`, `ObjectConverter`); `VeloxDev.Razor` ships four (`DoubleConverter`, `StringConverter`, `IntConverter`, `BoolConverter`). `VeloxDev.Jalium` ships no DynamicTheme layer. These adapter layers are *inferred* from source — they are not exercised by the WPF/Avalonia demos or tests.

## Related

- The per-framework `Transition`/`State`/`UIThreadInspector` shapes belong to the transition feature's adapter-provided section (`2_API/03_transition`), and the full adapter catalogue to the Platform Adapters feature (`2_API/08_platform-adapters`).
