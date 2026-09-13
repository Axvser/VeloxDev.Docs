# Data Flow — Dynamic Theme

The Dynamic Theme data flow splits into three phases: registering a theme-aware view and converting its `[ThemeConfig]` declarations into concrete values, switching the current theme (animated through the platform's scheduler, or instant), and overriding single properties at runtime.

## Pages

| Page | Flow covered |
|---|---|
| [Registration](00_registration/index.md) | `InitializeTheme()` → `ThemeCache.RegisterType` + `ThemeManager.Register` + apply current theme; the converter pipeline that turns attribute arguments into concrete values |
| [Switching](01_switching/index.md) | `Transition<T>` prepares grouped entries and runs them on one shared `ITimeSourceControl` via `InterpolatorCore.CreateScheduler`; `Jump<T>` applies every end value directly. Guard conditions, degradation and cancellation paths |
| [Runtime Overrides](02_runtime-overrides/index.md) | `SetThemeValue<T>` / `RestoreThemeValue<T>` and how active (dynamic) values override static ones |

> Key source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`, `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`, `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.
