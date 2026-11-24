# 前置条件

## 支持的目标

来源：`Src/Adapters/VeloxDev.MAUI/VeloxDev.MAUI.csproj`。

| 属性 | 声明的值 |
|---|---|
| `TargetFrameworks` | `net10.0;net10.0-windows10.0.19041.0` |
| `UseMaui` | `true` |
| `MauiVersion` | `10.0.20` |
| `Microsoft.WindowsAppSDK`（Windows TFM） | `1.7.250909003` |
| Windows `SupportedOSPlatformVersion` | `10.0.17763.0` |
| `VeloxDev.Core` 依赖 | `12.3.0` |
| 包版本 | `12.3.0` |

裁剪版 demo 目标是 `net10.0-android`，并在宿主 OS 允许时加上 `net10.0-ios`、`net10.0-maccatalyst` 与 `net10.0-windows10.0.19041.0`。本页只构建 Windows TFM；适配器也提供平台中立的 `net10.0` 资产。

Windows TFM 必须至少是 `net10.0-windows10.0.19041.0`：MAUI 10.0.x 只为该平台版本（以及 20348）提供 Windows 资产。更低的 TFM 会静默回落到平台中立程序集，丢掉适配器 `#if WINDOWS` 代码需要的 Windows 专用类型。

## 工具

- **.NET SDK 10.0 或更高**，因为适配器目标 `net10.0`。
- **.NET MAUI 工作负载**（`dotnet workload install maui`）。Windows 目标还需要 Windows App SDK 运行时。
- **Windows 10 版本 1809（build 17763）或更高**，用于 Windows TFM。
- 不需要数据库、服务、API 密钥或网络。

## 添加包

```powershell
dotnet add package VeloxDev.MAUI --version 12.3.0
dotnet add package Microsoft.Maui.Controls --version 10.0.20
```

Windows TFM 还需要 Windows App SDK：

```xml
<ItemGroup Condition="$([MSBuild]::GetTargetPlatformIdentifier('$(TargetFramework)')) == 'windows'">
  <PackageReference Include="Microsoft.WindowsAppSDK" Version="1.7.250909003" />
</ItemGroup>
```

**预期结果：** 命令退出 `0`；项目列出 `VeloxDev.MAUI`、`Microsoft.Maui.Controls`，Windows 下还有 `Microsoft.WindowsAppSDK`；`VeloxDev.Core` 被传递还原。

## 工程设置

```xml
<PropertyGroup>
  <TargetFramework>net10.0-windows10.0.19041.0</TargetFramework>
  <OutputType>Exe</OutputType>
  <RootNamespace>MyApp</RootNamespace>
  <UseMaui>true</UseMaui>
  <SingleProject>true</SingleProject>
  <ImplicitUsings>enable</ImplicitUsings>
  <Nullable>enable</Nullable>
  <MauiVersion>10.0.20</MauiVersion>
  <SupportedOSPlatformVersion>10.0.17763.0</SupportedOSPlatformVersion>
  <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
</PropertyGroup>
```

**预期结果：** 写入工作流类型之前 `dotnet build` 就能成功，并产出一个 Windows 应用。
