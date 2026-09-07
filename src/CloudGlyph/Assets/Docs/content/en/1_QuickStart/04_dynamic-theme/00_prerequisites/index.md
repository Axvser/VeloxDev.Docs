# Dynamic Theme — Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj` `<TargetFrameworks>`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`. The theme engine (`ThemeManager`, `ThemeCache`, `[ThemeConfig]`, `ITheme`, ...) is consumable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **Per-framework adapter targets** (from each adapter csproj) — add the adapter matching your GUI framework to obtain the theme value converters and the platform `Interpolator`:
    - `VeloxDev.WPF`: `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - `VeloxDev.Avalonia`: `netstandard2.0` / `net6.0`
- **SDK / runtime:** a .NET SDK able to build the target you pick; WPF needs `<UseWPF>true</UseWPF>` on a Windows TFM. The in-repo demos build against `net9.0-windows` (WPF) and `net9.0` (Avalonia) — *tested* configurations, not requirements.
- **Package manager:** NuGet via the `dotnet` CLI or Visual Studio (`dotnet add package ...`).
- **Required services:** no database, key or external service. To *see* a theme switch you need a running GUI host (a WPF/Avalonia window). Animated switching additionally needs the platform `Interpolator` installed once through `ThemeManager.SetPlatformInterpolator` (see [Switch at Runtime](../03_switch-at-runtime/index.md)); instant `Jump<T>` switching does not need it.

**Evidence for the examples.** This Quick Start mirrors the shipped demos and the unit test:

| Source | Target framework | What it shows |
|---|---|---|
| `Examples/Theme/WPF/Demo` | `net9.0-windows` | a `Window` mapped with `[ThemeConfig<BrushConverter, Light, Dark>]` on `Background`/`Foreground`, toggled with `Transition<Light/Dark>(TransitionEffects.Theme)` |
| `Examples/Theme/Avalonia/Demo` | `net9.0` | the same scenario with `[ThemeConfig<ObjectConverter, Dark, Light>]` (theme order `Dark, Light`) |
| `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` | `net10.0` (test project) | default `ThemeManager.Current` is `Dark`; `StartModel` defaults to `Cache`; 2-theme `[ThemeConfig]` construction |
