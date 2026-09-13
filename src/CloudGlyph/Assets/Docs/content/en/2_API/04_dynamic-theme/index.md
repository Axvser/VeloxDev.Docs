# Dynamic Theme — API Reference

The dynamic-theme feature switches an app between theme types (`Dark` / `Light` / custom) at runtime and animates every themed property through the TransitionSystem sampling engine. The public surface is split across the core `VeloxDev.DynamicTheme` namespace, the theme source generator, the backing transition engine, and the platform adapters.

> Evidence: demos `Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo` (Priority 1), tests `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` and `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeTransitionTests.cs` (Priority 2). Signatures verified against `Src/Core/VeloxDev.Core/DynamicTheme/**`, `Src/Core/VeloxDev.Core/TransitionSystem/**`, `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/**`, the theme generator `Src/Generators/VeloxDev.Core.Generator/Theme.cs`, and the adapter theme files under `Src/Adapters/**`.

## Public Surface

| Area | Namespace / location | Contents |
|---|---|---|
| Core contracts | `VeloxDev.DynamicTheme` (in `VeloxDev.Core`) | `ThemeManager`, `ThemeCache` (+ nested `InstanceCache`), `ThemeConfigAttribute<TConverter, TTheme...>`, enum `StartModel`, `Dark`, `Light`, `ITheme`, `IThemeObject`, `IThemeValueConverter` |
| Source generator | `VeloxDev.Generators.Theme` | Emits the partial `IThemeObject` implementation for a class carrying `[ThemeConfig<...>]` |
| Backing engine | `VeloxDev.TransitionSystem` / `.Abstractions` / `VeloxDev.Timing` | `InterpolatorCore`, `TransitionSchedulerCore`, `TimeSourceCore` (the default `ITimeSourceControl`), `TransitionCore`, `ISampler`, `ISampleable`, `ITransitionProperty` / `TransitionProperty`, `ITransitionEffectCore`, `IEaseCalculator`, `Eases` |
| Platform adapters | `VeloxDev.WPF` / `VeloxDev.Avalonia` (and `MAUI` / `WinUI` / `WinForms` / `Razor`) | Adapter `Interpolator`, `TransitionEffect` / `TransitionEffects`, theme value converters (`DoubleConverter`, `PointConverter`, `ThicknessConverter`, `CornerRadiusConverter`, `ColorConverter`, `BrushConverter`, `ObjectConverter`) |

## Key Types at a Glance

- **`ThemeManager`** — static entry point. `Current`, `StartModel`, `SetPlatformInterpolator<T>`, `SetCurrent<T>`, `Register` / `Unregister`, `Transition<T>` / `Transition(Type, ITransitionEffectCore)` (`async void`, run on the transition system), `Jump<T>` / `Jump(Type)` (synchronous, applies end values with no animation).
- **`ThemeCache`** — central store of theme property values: static defaults per type plus runtime overrides per instance (`InstanceCache`), with a shared converter registry.
- **`ThemeConfigAttribute<TConverter, TTheme1..TThemeN>`** — six arities (2 to 7 theme types) mapping one property to one value per theme.
- **`StartModel`** — `[Flags]` enum (`Reflect = 1`, `Cache = 2`) selecting the animation start-value source.
- **`ITheme` / `IThemeObject` / `IThemeValueConverter`** — theme marker, the generated theme-object contract, and the value-conversion strategy.
- **Backing engine** — the static sampler registry `InterpolatorCore.NativeInterpolators` (`ConcurrentDictionary<Type, ISampler>`), the platform seam `InterpolatorCore.CreateScheduler` / `TransitionSchedulerCore` / the shared `ITimeSourceControl`, the sampling contracts `ISampler`/`ISampleable`, the property contract `TransitionProperty`, and the effect/ease contracts `ITransitionEffectCore` / `IEaseCalculator` / `Eases`.
- **Platform adapters** — the adapter `Interpolator`, the effect presets `TransitionEffects` (`Empty` / `Theme` / `Hover`), and the theme value converters.

## Pages

- [00 ThemeManager](00_ThemeManager/index.md) — `ThemeManager` (all static members), enum `StartModel`, marker classes `Dark` / `Light`.
- [01 ThemeCache](01_ThemeCache/index.md) — `ThemeCache` (all static members) and nested class `InstanceCache`.
- [02 ThemeConfigAttribute](02_ThemeConfigAttribute/index.md) — `ThemeConfigAttribute<TConverter, TTheme...>` (six arities) and the contracts `ITheme`, `IThemeObject`, `IThemeValueConverter`.
- [03 TransitionSystem](03_TransitionSystem/index.md) — the engine surface the theme feature drives: sampler resolution, the property and effect contracts.
- [04 PlatformAdapters](04_PlatformAdapters/index.md) — the adapter-provided `Interpolator`, `TransitionEffect` / `TransitionEffects`, and the theme value converters.

## Related Features

- The transition feature (`2_API/03_transition`) documents the full animation engine that `ThemeManager` drives.
- Per-framework platform wiring lives in its own feature tree (`2_API/08_platform-adapters`).
