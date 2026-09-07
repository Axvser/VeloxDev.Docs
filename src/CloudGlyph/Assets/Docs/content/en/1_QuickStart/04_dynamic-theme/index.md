# Dynamic Theme — Quick Start

## Dynamic Theme

### Overview

**Dynamic Theme** brings **runtime theme switching with animated transitions** to a VeloxDev-based editor or application. You map each themed property on a control or view-model to one value per theme with `[ThemeConfig]`, then flip between themes at runtime — smoothly through `ThemeManager.Transition<T>(effect)` (interpolated frame by frame by the TransitionSystem engine) or instantly through `ThemeManager.Jump<T>()`.

The feature ships in two layers:

- **Engine core** (`VeloxDev.Core`) — the framework-agnostic theme model under the `VeloxDev.DynamicTheme` namespace: `ThemeManager` (static `Current`, `StartModel`, `SetPlatformInterpolator`, `SetCurrent<T>`, `Register`/`Unregister`, `Transition<T>`, `Jump<T>`), the shared `ThemeCache`, the `[ThemeConfig]` attribute (one converter + 2–7 themes, 6 generic arities), the marker interface `ITheme` with the built-in `Dark` and `Light` themes, `IThemeObject` (the source-generator contract) and `IThemeValueConverter`. The interpolation engine that drives theme animations also lives in `VeloxDev.Core` (TransitionSystem).
- **Platform Adapter layer** (the Platform Adapters packages, e.g. `VeloxDev.WPF`, `VeloxDev.Avalonia`) — the per-framework **theme value converters** (`BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`) that translate `[ThemeConfig]` context arguments into real UI values, plus the `Interpolator` subclass and the `TransitionEffects` presets used for animated switching.

Applying themed UI values requires the adapter for your GUI framework — it supplies the converters and the platform `Interpolator`. The two shipped demos cover **WPF** and **Avalonia**.

The authoritative examples live under `Examples/Theme/{WPF,Avalonia}/Demo`, and the engine contract is pinned by `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — supported target frameworks, SDK/workloads, the demos and the test
- [01 Install & Add Dependency](01_install/index.md) — `VeloxDev.Core` (brings the source generator) plus the platform adapter
- [02 Declare & Register](02_declare-and-register/index.md) — theme classes, `[ThemeConfig]` + converters, turning a class into an `IThemeObject`
- [03 Switch at Runtime](03_switch-at-runtime/index.md) — interpolator setup, `Transition` / `Jump` / `SetCurrent`, callbacks, runtime overrides, UI-thread note
- [04 Verify & Complete Code](04_verify-and-complete-code/index.md) — verify with demos and tests, the single runnable program, the run declaration
