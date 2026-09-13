# Dynamic Theme — Quick Start

## Overview

**Dynamic Theme** brings **runtime theme switching with animated transitions** to a VeloxDev-based editor or application. You map each themed property on a control or view-model to one value per theme with `[ThemeConfig]`, then flip between themes at runtime — smoothly through `ThemeManager.Transition<T>(effect)`, which runs the whole switch as an animation on the TransitionSystem engine, or instantly through `ThemeManager.Jump<T>()`, which writes the target values synchronously with no timeline and no effect.

The feature ships in two layers:

- **Engine core** (`VeloxDev.Core`) — the framework-agnostic theme model under the `VeloxDev.DynamicTheme` namespace: `ThemeManager` (static `Current`, `StartModel`, `SetPlatformInterpolator`, `SetCurrent<T>`, `Register`/`Unregister`, `Transition<T>`, `Jump<T>`), the shared `ThemeCache`, the `[ThemeConfig]` attribute (one converter + 2–7 themes, 6 generic arities), the marker interface `ITheme` with the built-in `Dark` and `Light` themes, `IThemeObject` (the source-generator contract) and `IThemeValueConverter`. A switch is driven by the interpolation engine that also lives in `VeloxDev.Core` (TransitionSystem), so every target of one switch shares a single `ITimeSourceControl`.
- **Platform Adapter layer** (the Platform Adapters packages, e.g. `VeloxDev.WPF`, `VeloxDev.Avalonia`) — the per-framework **theme value converters** (`BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`) that translate `[ThemeConfig]` context arguments into real UI values, plus the `Interpolator` subclass and the `TransitionEffects` presets used for animated switching.

Applying themed UI values requires the adapter for your GUI framework — it supplies the converters and the platform `Interpolator`. Both shipped demo families cover **WPF** and **Avalonia**: a minimal one (`Examples/Theme/WPF Trimmed/Demo`, `Examples/Theme/Avalonia Trimmed/Demo`) that a reader can reproduce line by line, and a scale one (`Examples/Theme/WPF/Demo`, `Examples/Theme/Avalonia/Demo`) that drives the same system over a thousand elements and adds a headless benchmark.

The engine contract is pinned by `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`, and the fact that a switch runs on the transition system by `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeTransitionTests.cs`.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — supported target frameworks, SDK/workloads, the demos and the tests
- [01 Install & Add Dependency](01_install/index.md) — `VeloxDev.Core` (brings the source generator) plus the platform adapter
- [02 Declare & Register](02_declare-and-register/index.md) — theme classes, `[ThemeConfig]` + converters, turning a class into an `IThemeObject`
- [03 Switch at Runtime](03_switch-at-runtime/index.md) — interpolator setup, `Transition` / `Jump` / `SetCurrent`, callbacks, controlling a switch, runtime overrides
- [04 Verify & Complete Code](04_verify-and-complete-code/index.md) — verify with the minimal and scale demos and with both test files, the single runnable program, the run declaration
