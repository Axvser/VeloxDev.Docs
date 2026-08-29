# Dynamic Theme — API Reference

The Dynamic Theme feature provides runtime theme switching with animated transitions. The public surface is split across the core `VeloxDev.DynamicTheme` namespace (state, switching, storage, configuration, contracts), the backing TransitionSystem engine (`VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`), and the platform adapters (`VeloxDev.WPF` / `VeloxDev.Avalonia`).

> Evidence: Demo projects `Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo` (Priority 1), tests `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` (Priority 2). Signatures verified against `Src/Core/VeloxDev.Core/DynamicTheme/*`, `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/*`, `Src/Core/VeloxDev.Core/TransitionSystem/*`, and `Src/Adapters/*/PlatformAdapters/*`.

## Namespace / Package Overview

| Namespace | Contents |
|---|---|
| `VeloxDev.DynamicTheme` | `ThemeManager`, `ThemeCache` (+ nested `InstanceCache`), `ThemeConfigAttribute<TConverter, TTheme...>`, `StartModel`, `Dark`, `Light`, `ITheme`, `IThemeObject`, `IThemeValueConverter` |
| `VeloxDev.TransitionSystem` (backing engine) | `InterpolatorCore` (declared in `VeloxDev.TransitionSystem.Abstractions`), `ISampler`, `ISampleable`, `ITransitionEffectCore`, `IEaseCalculator`, `Eases` |
| Platform adapters (`VeloxDev.WPF` / `VeloxDev.Avalonia`) | `Interpolator`, `TransitionEffect`, `TransitionEffects`, value converters (`DoubleConverter`, `PointConverter`, `ThicknessConverter`, `CornerRadiusConverter`, `ColorConverter`, `BrushConverter`, `ObjectConverter`) |

## Pages

| Page | Contents |
|---|---|
| `00 ThemeManager` | `ThemeManager` (all static members), enum `StartModel`, classes `Dark` / `Light` |
| `01 ThemeCache` | `ThemeCache` (all static members), nested class `InstanceCache` |
| `02 ThemeConfigAttribute` | `ThemeConfigAttribute<TConverter, TTheme...>` (6 arities), interfaces `ITheme`, `IThemeObject`, `IThemeValueConverter` |
| `03 TransitionSystem` | Backing engine: `InterpolatorCore` static members, `ISampler`, `ISampleable`, `ITransitionEffectCore`, `IEaseCalculator`, `Eases` |
| `04 PlatformAdapters` | `Interpolator`, `TransitionEffect`, `TransitionEffects`, and the value converters |

## Key Types at a Glance

- **`ThemeManager`** — static entry point. `Current`, `StartModel`, `SetPlatformInterpolator<T>`, `SetCurrent<T>`, `Register` / `Unregister`, `Transition<T>` / `Transition(Type, ITransitionEffectCore)`, `Jump<T>` / `Jump(Type)`.
- **`ThemeCache`** — central store of theme property values. Static default values per type plus runtime overrides per instance (`InstanceCache`), with a converter registry.
- **`ThemeConfigAttribute<TConverter, TTheme1..TTheme7>`** — 6 arities mapping one property to one value per theme.
- **`StartModel`** — `[Flags]` enum (`Reflect = 1`, `Cache = 2`) selecting the animation start value source.
- **`ITheme` / `IThemeObject` / `IThemeValueConverter`** — marker interface, generated theme-object contract, and the value-conversion strategy.
- **Backing engine** — `InterpolatorCore.NativeInterpolators` registry (`ConcurrentDictionary<Type, ISampleable>`), `ISampler`/`ISampleable`, `ITransitionEffectCore`, `IEaseCalculator`, `Eases`.
- **Platform adapters** — `Interpolator`, `TransitionEffect` (`Priority = DispatcherPriority.Render`), `TransitionEffects` (`Empty` / `Theme` / `Hover`), and the value converters.
