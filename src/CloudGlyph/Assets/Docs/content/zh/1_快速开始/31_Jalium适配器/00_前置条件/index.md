# 前置条件与安装

## 支持目标

适配器只有一个目标框架 `net10.0`，依赖 `Jalium.UI.Controls` **26.10.8** —— 最低的平台中立包。它只使用跨平台的控件、媒体与互操作表面，因此可服务 Windows、Linux 与 Android 宿主。

- .NET SDK 10.0。
- 本快速开始使用 Jalium 桌面宿主：`net10.0-windows` 加 `Jalium.UI.Desktop` 26.10.9。该包提供应用宿主、窗口与构建属性；它是 demo 依赖，不是适配器的要求。
- 不需要数据库、服务或 API 密钥。

`26.10.8` 是硬底线：`26.10.7` 缺少 `Dispatcher.MainDispatcher`，更早的包缺少 `DispatcherPriority`。使用者可以升级。

## 包

| 包 | 本仓库声明的版本 | 作用 |
| --- | --- | --- |
| `VeloxDev.Jalium` | 12.3.0 | 适配器 |
| `VeloxDev.Core` | 12.3.0 | 模型与画布契约，传递引入 |
| `Jalium.UI.Controls` | 26.10.8（底线） | 平台中立的控件、媒体、互操作 |
| `Jalium.UI.Desktop` | 26.10.9 | demo 使用的桌面应用宿主 |
| `VeloxDev.Jalium.Templates` | 12.0.0 | 七个 `dotnet new` 条目模板 |

## 工程文件

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net10.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="VeloxDev.Jalium" Version="12.3.0" />
    <PackageReference Include="Jalium.UI.Desktop" Version="26.10.9" />
  </ItemGroup>
</Project>
```

跨平台宿主目标为 `net10.0`，引用 `Jalium.UI.Controls` 而不是 `Jalium.UI.Desktop`；适配器本身不变。

## 安装

```powershell
dotnet new console -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.Jalium
dotnet add package Jalium.UI.Desktop
dotnet new install VeloxDev.Jalium.Templates
```

桌面 demo 的 `Program.cs` 是一个普通 `AppBuilder` 入口；控制台模板的 `Main` 会在[表面与宿主](../01_表面与宿主/index.md)替换。

**预期结果：** 包还原成功，且

```powershell
dotnet new list jalium-v
```

列出 `jalium-v-tree`、`jalium-v-node`、`jalium-v-slot`、`jalium-v-link`、`jalium-v-selector`、`jalium-v-decorator`、`jalium-v-minimap`。

## 首次构建前先生成

树标记按类型引用了 `NodeView`、`LinkView`、`TemplateSelector`、`GridDecorator` 与 `MinimapOverlay`；节点标记引用 `SlotView`。只生成一部分会以 `CS0246` 失败。按[表面与宿主](../01_表面与宿主/index.md)一次生成全部七个。

若重复注册使 `dotnet new install` 以非零码退出，先运行 `dotnet new uninstall VeloxDev.Jalium.Templates`。
