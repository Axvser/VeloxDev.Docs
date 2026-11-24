# Runtime Themes

`VeloxDev.DynamicTheme` declares themed properties, stores the value of each property for each theme, and switches the active theme either instantly or through the transition engine. The declaration is generated: a `[ThemeConfig<…>]` attribute on a partial class makes the generator emit `InitializeTheme`, `SetThemeValue`, `RestoreThemeValue`, the two lifecycle hooks and the two cache accessors.

Theme values are converted once by the platform's `IThemeValueConverter`. A switch then samples the pooled converted values; it does not re-run the converter.

## Type groups

| Group | Types | Page |
|---|---|---|
| Declaration and storage | `ThemeConfigAttribute<…>`, `ITheme`, `IThemeObject`, `IThemeValueConverter`, `Light`, `Dark`, `ThemeCache`, generated members | [Declaration and types](00_declaration-and-types/index.md) |
| Switching | `ThemeManager`, `StartModel` | [Theme manager](01_theme-manager/index.md) |
| Platform converters | `BrushConverter`, `ColorConverter`, `ObjectConverter` and the per-platform converter sets | [Platform converters](02_platform-converters/index.md) |

## Switching models

- `ThemeManager.Transition<T>(effect)` animates every registered object to theme `T` over a shared timeline.
- `ThemeManager.Jump<T>()` writes every end value at once and needs neither an interpolator nor an effect.
- `ThemeManager.SetCurrent<T>()` changes `ThemeManager.Current` without touching any registered object.

The current theme defaults to `Dark`. `ThemeManager.Current` is assigned internally by the transition and jump paths, so a landed switch is what advances it.

See [Runtime Themes quick start](../../1_QuickStart/13_runtime-themes/index.md) for a runnable window.

## Requirements

- The generated members need `VeloxDev.Core.Generator`.
- Animated switching needs an adapter's transition surface and one call to `ThemeManager.SetPlatformInterpolator(new Interpolator())`; without it a switch still lands, but jumps.
- `[ThemeConfig]` requires the class to be `partial`; the generator emits nothing for a non-partial class.
