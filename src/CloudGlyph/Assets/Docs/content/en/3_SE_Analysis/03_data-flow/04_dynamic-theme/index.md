# Data Flow — Dynamic Theme

The Dynamic Theme data flow splits into three phases: registering a theme-aware view and converting its `[ThemeConfig]` declarations into concrete values, switching the current theme (animated or instant) through a shared sampler pipeline, and overriding single properties at runtime.

## Pages

| Page | Flow covered |
|---|---|
| [Registration](00_registration/index.md) | `InitializeTheme()` → `ThemeCache.RegisterType` + `ThemeManager.Register` + apply current theme; the converter pipeline that turns attribute arguments into concrete values |
| [Switching](01_switching/index.md) | `Transition<T>` animated switch and `Jump<T>` instant switch, sharing `PrepareSamplers` + `ExecuteTransition`; guard conditions and edge paths |
| [Runtime Overrides](02_runtime-overrides/index.md) | `SetThemeValue<T>` / `RestoreThemeValue<T>` and how active (dynamic) values override static ones |

> Key source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`, `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`, `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.
