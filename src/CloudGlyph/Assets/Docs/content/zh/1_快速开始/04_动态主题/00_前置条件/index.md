# 动态主题 — 前置条件

- **支持目标**（来自 `VeloxDev.Core.csproj` 的 `<TargetFrameworks>`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`。主题引擎（`ThemeManager`、`ThemeCache`、`[ThemeConfig]`、`ITheme` 等）可在 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+ 中使用。
- **各框架适配器目标**（来自各适配器 csproj）—— 添加与你 GUI 框架匹配的适配器，以获得主题值转换器与平台 `Interpolator`：
    - `VeloxDev.WPF`：`netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - `VeloxDev.Avalonia`：`netstandard2.0` / `net6.0`
- **SDK / 运行时：** 能构建所选目标的 .NET SDK；WPF 需要在 Windows TFM 上开启 `<UseWPF>true</UseWPF>`。仓库内示例以 `net9.0-windows`（WPF）与 `net9.0`（Avalonia）构建 —— *被验证过*的配置，并非要求。
- **包管理器：** 通过 `dotnet` CLI 或 Visual Studio 使用 NuGet（`dotnet add package ...`）。
- **必需服务：** 无数据库、密钥或外部服务。要*看到*主题切换，需要一个正在运行的 GUI 宿主（WPF/Avalonia 窗口）。带动画的切换还需通过 `ThemeManager.SetPlatformInterpolator` 一次性安装平台 `Interpolator`（见[运行时切换](../03_运行时切换/index.md)）；即时 `Jump<T>` 切换则不需要。

**示例证据。** 本快速入门对照下列官方示例与单元测试：

| 来源 | 目标框架 | 展示内容 |
|---|---|---|
| `Examples/Theme/WPF/Demo` | `net9.0-windows` | 用 `[ThemeConfig<BrushConverter, Light, Dark>]` 映射 `Background`/`Foreground` 的 `Window`，通过 `Transition<Light/Dark>(TransitionEffects.Theme)` 切换 |
| `Examples/Theme/Avalonia/Demo` | `net9.0` | 同样的场景，用 `[ThemeConfig<ObjectConverter, Dark, Light>]`（主题顺序 `Dark, Light`） |
| `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` | `net10.0`（测试工程） | `ThemeManager.Current` 默认是 `Dark`；`StartModel` 默认是 `Cache`；2 主题 `[ThemeConfig]` 可构造 |
