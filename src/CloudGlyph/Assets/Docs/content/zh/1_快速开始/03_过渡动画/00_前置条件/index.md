# Transition — 前置条件

- **支持目标**（来自 `VeloxDev.Core.csproj` 的 `<TargetFrameworks>`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`。引擎核心可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **各框架适配器目标**（来自各适配器 csproj）——动画 UI 绑定属性时添加与你 GUI 框架匹配的适配器：
    - `VeloxDev.WPF` / `VeloxDev.WinForms`：`netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - `VeloxDev.Avalonia`：`netstandard2.0` / `net6.0`
    - `VeloxDev.WinUI`：`net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0`
    - `VeloxDev.MAUI`：`net10.0`（外加 MAUI 工作负载加入的平台 TFM，如 `net10.0-windows10.0.19041.0`）
    - `VeloxDev.Razor`（Blazor）：`net6.0`
- **SDK / 运行时：** 能构建所选目标的 .NET SDK —— 引擎核心无需特殊工作负载；WPF / WinForms / WinUI / MAUI / Razor 目标需要对应的 GUI 工作负载（如 `<UseWPF>true</UseWPF>`、Windows App SDK、MAUI 工作负载、Razor SDK）。仓库内示例面向 `net9.0` / `net10.0` 构建 —— *被验证过*的配置，并非要求。
- **包管理器：** 通过 `dotnet` CLI 或 Visual Studio 使用 NuGet（`dotnet add package ...`）。
- **所需服务：** 无 —— 没有数据库、密钥或外部服务。要看 UI 动画需要一个运行中的应用宿主（WPF/Avalonia/WinUI/WinForms 窗口、MAUI 应用或 Blazor 回路）；纯值插值可无界面运行。

**示例的证据。** 本快速入门所参照的示例位于 `Examples/Transition/`：

| 示例 | 目标框架 | 动画对象 |
|---|---|---|
| `WPF/Demo` | `net9.0-windows` | 三个 `Rectangle` —— 嵌套 `TranslateTransform.X`、变换集合、`Fill` |
| `Avalonia/Demo` | `net9.0` | 三个 `Rectangle` —— 与 WPF 相同的场景组 |
| `WinUI/Demo` | `net8.0-windows10.0.19041.0` | `Rectangle` —— `RenderTransform`、`Projection`、渐变 `Fill` |
| `WinForms/Demo` | `netframework4.7.1` | 三个 `Panel`/`Control` —— `Location`、`Size`、`BackColor` |
| `MAUI/Demo` | `net10.0-*` | MAUI `Rectangle` —— `TranslationX/Y`、`RotationX/Y`、`Scale`、`Fill` |
| `Blazor/Demo` | `net10.0`（服务器 + WASM 客户端） | 普通 `BoxModel` 视图模型，经 `INotifyPropertyChanged` 重渲染 |
| `Jalium/Demo` | `net10.0-windows` | Jalium 桌面 `Rectangle` |

引擎层契约另由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 锁定（`EasesTests`、`InterpolatorCoreTests`、`SamplerSetTests`、`SamplingLoopTests`、`TransitionEffectCoreTests` …）。
