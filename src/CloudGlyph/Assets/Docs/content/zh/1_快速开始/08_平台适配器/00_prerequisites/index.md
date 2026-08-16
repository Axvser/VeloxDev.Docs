# 平台适配器 — 前置条件

- **支持目标**（来自各适配器 csproj）：
    - WPF / WinForms（`VeloxDev.WPF.csproj`、`VeloxDev.WinForms.csproj`）：`netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`
    - Avalonia（`VeloxDev.Avalonia.csproj`）：`netstandard2.0` / `net6.0`
    - WinUI（`VeloxDev.WinUI.csproj`）：`net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0`
    - MAUI（`VeloxDev.MAUI.csproj`）：`net10.0`（移动端 TFM）
    - Razor（`VeloxDev.Razor.csproj`）：`net6.0`
- **SDK / 运行时：** 能构建所选 GUI 工作负载的 .NET SDK（WPF/WinForms 需 Windows TFM；WinUI 需 Windows App SDK；MAUI 需 MAUI 工作负载；Razor 需 Razor SDK）。仓库内示例面向 `net9.0` / `net10.0` —— *被验证过*的配置，并非要求。
- **包管理器：** NuGet / `dotnet` CLI（`dotnet new install`、`dotnet add package`、`dotnet build`）。
- **必需服务：** 在 SDK 中安装所选框架的 GUI 工作负载（如 `Microsoft.NET.Sdk` 加 `<UseWPF>true</UseWPF>`、WinUI 的 Windows App SDK、MAUI 工作负载或 Razor SDK）；要*看到* UI 需要一个运行中的应用宿主 —— WPF/Avalonia/WinUI/WinForms 窗口或 Blazor 连接。
