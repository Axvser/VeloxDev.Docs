# 前置条件

## 支持的目标

来源：`Src/Adapters/VeloxDev.WinUI/VeloxDev.WinUI.csproj`。

| 属性 | 声明的值 |
|---|---|
| `TargetFrameworks` | `net8.0-windows10.0.19041.0;net10.0-windows10.0.19041.0` |
| `TargetPlatformMinVersion` | `10.0.17763.0` |
| `UseWinUI` | `true` |
| `Microsoft.WindowsAppSDK` | `1.6.241114003`（适配器依赖） |
| `VeloxDev.Core` 依赖 | `12.3.0` |
| 包版本 | `12.3.0` |

裁剪版 demo 目标是 `net10.0-windows10.0.19041.0`，引用 `Microsoft.WindowsAppSDK` `1.8.251003001`；那是**测过**的配置，不是最低要求。本页使用 `net8.0-windows10.0.19041.0`。

## 工具

- **.NET SDK 8.0 或更高**，以及 **Windows App SDK** 构建工具（`UseWinUI`）。
- **Windows 10 版本 1809（build 17763）或更高** —— 声明的平台最低版本。
- 匹配的 **`win-x64`（或对应）运行时标识符**。demo 固定 `win-x64`；只有要发布其他架构时才添加别的 RID。
- 不需要数据库、服务、API 密钥或网络。

## 添加包

```powershell
dotnet add package VeloxDev.WinUI --version 12.3.0
dotnet add package Microsoft.WindowsAppSDK --version 1.6.241114003
dotnet add package Microsoft.Windows.SDK.BuildTools --version 10.0.26100.6584
```

**预期结果：** 命令退出 `0`；项目文件列出三者，`VeloxDev.Core` 被传递还原。

适配器包把 Core 生成器作为分析器依赖带上，所以 `[WorkflowBuilder.*]` 与 `[VeloxProperty]` 会生成 `InitializeWorkflow()` 与标准命令。

## 工程设置

```xml
<PropertyGroup>
  <OutputType>WinExe</OutputType>
  <TargetFramework>net8.0-windows10.0.19041.0</TargetFramework>
  <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
  <RootNamespace>MyApp</RootNamespace>
  <RuntimeIdentifier>win-x64</RuntimeIdentifier>
  <UseWinUI>true</UseWinUI>
  <WindowsPackageType>None</WindowsPackageType>
  <EnableMsixTooling>true</EnableMsixTooling>
  <Nullable>enable</Nullable>
  <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
</PropertyGroup>
```

`WindowsPackageType=None` 产出非打包应用。WinUI 工程模板会提供 `app.manifest`，声明 Windows 10 兼容与 `PerMonitorV2` DPI 感知；完整文件集里给了一份最小副本。

**预期结果：** 写入任何工作流类型之前 `dotnet build` 就能成功，输出里出现 `MyApp.exe`。
