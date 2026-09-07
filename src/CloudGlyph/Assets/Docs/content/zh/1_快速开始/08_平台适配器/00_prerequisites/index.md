# 平台适配器 — 前置条件

下面的支持目标取自各适配器**声明在 `.csproj`** 的内容（`Src/Adapters/<包名>/<包名>.csproj`）及其框架依赖——不是来自演示。演示只能证明某一种*运行过*的配置，绝不等于最低支持版本。

## 目标框架

| 适配器包 | `.csproj` 中的 `TargetFramework(s)` | 框架依赖 |
|---|---|---|
| `VeloxDev.WPF` | `netframework4.6.1`；`net5.0-windows`；`netcoreapp3.0` | `<UseWPF>true</UseWPF>` |
| `VeloxDev.WinForms` | `netframework4.6.1`；`net5.0-windows`；`netcoreapp3.0` | `<UseWindowsForms>true</UseWindowsForms>` |
| `VeloxDev.Avalonia` | `netstandard2.0`；`net6.0` | Avalonia `11.1.0` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0`；`net10.0-windows10.0.19041.0` | Windows App SDK（`UseWinUI`），最低 `10.0.17763.0` |
| `VeloxDev.MAUI` | `net10.0`；`net10.0-windows10.0.19041.0` | .NET MAUI 工作负载（`UseMaui`）、`Microsoft.Maui.Controls` |
| `VeloxDev.Razor` | `net6.0` | `Microsoft.AspNetCore.App`（Razor SDK） |
| `VeloxDev.Jalium` | `net10.0` | `Jalium.UI.Controls` |

补充说明：

- `VeloxDev.MAUI` 使用平台中立的 `net10.0` 程序集，外加 `net10.0-windows10.0.19041.0` Windows TFM（`#if WINDOWS` 类型，例如基于 WinUI 的连线/覆盖路径，只存在于 Windows 资产里）。Windows 的 `SupportedOSPlatformVersion` 是 `10.0.17763.0`。
- `VeloxDev.WinUI` 额外声明默认 `RuntimeIdentifier` 为 `win-x64`（还有 `win-arm64` / `win-x86`），并引用 `Microsoft.WindowsAppSDK`。
- `VeloxDev.Jalium` 平台中立（`net10.0`）——适配器只用跨平台的 Jalium 内核，因此可同时服务 Windows、Linux 与 Android 的使用方。

## SDK / 运行时

- 能构建所选 **GUI 工作负载** 的 .NET SDK：Windows 桌面 TFM 需要 Windows SDK（`net5.0-windows` / `netcoreapp3.0` / `net9.0-windows` …），WinUI 需要 Windows App SDK 工作负载，MAUI 需要 `maui` 工作负载，Razor 需要 Razor SDK（`Microsoft.NET.Sdk.Razor`）。Avalonia 与 Jalium 只要有对应目标 SDK 即可构建。
- 本快速开始的 WPF 脚手架目标是 `net9.0-windows`——一种*被验证过*的配置（仓库内演示构建 `net9.0-windows` / `net10.0`），不是硬性要求。
- **包管理器：** NuGet + `dotnet` CLI（`dotnet new install`、`dotnet add package`、`dotnet build`）。

## 所需服务

无。要*看到*工作流，需要一个应用宿主——WPF / WinForms / WinUI / Avalonia 窗口、MAUI 应用、Blazor 电路（Razor）或 Jalium 窗口——负责显示生成的视图，并把一个 `IWorkflowTreeViewModel` 作为 `DataContext` 提供给它。

## 证据说明

WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor 与 Jalium 在 `Examples/Workflow/<平台>` 下都有工作流演示（各自带 `Trimmed` 变体），`Examples/Transition/*` 与 `Examples/Theme/*` 下还有过渡/主题演示。由于本编写环境无法启动 GUI，以下内容全部为静态核验（见「完整代码」页的运行声明）。
