# 前置条件

契约住在 `VeloxDev.Core` 里，本身不依赖任何 GUI。只有在你想挂上一家适配器、观察表面时才需要 GUI；一致性套件用 WPF 做最小的可运行例子。

## 支持的目标

以下来自项目文件，不是某次 demo 运行。demo 只能证明一套**测过**的配置，永远不定义最低支持范围。

| 程序集 | 声明的 `TargetFrameworks` | 来源 |
|---|---|---|
| `VeloxDev.Core` | `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0` | `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` |
| `VeloxDev.WPF` | `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows` | `Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj` |
| `VeloxDev.Avalonia` | `netstandard2.0;net6.0;net8.0` | `Src/Adapters/VeloxDev.Avalonia/VeloxDev.Avalonia.csproj` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0;net10.0-windows10.0.19041.0` | `Src/Adapters/VeloxDev.WinUI/VeloxDev.WinUI.csproj` |
| `VeloxDev.MAUI` | `net10.0;net10.0-windows10.0.19041.0` | `Src/Adapters/VeloxDev.MAUI/VeloxDev.MAUI.csproj` |

## 工具

- **.NET SDK 8.0 或更高。** WPF 无头套件目标是 `net8.0-windows`。
- **WPF 套件需要 Windows。** 其他无头套件也需要各自平台的桌面工具链；WinUI 与 MAUI 有 demo，但没有无头套件（见[一致性验证](../03_一致性验证/index.md)）。
- **MSTest 4.0.2** 与 **coverlet.collector 6.0.4** —— 无头测试工程声明的版本。

## 包与引用

只需要契约类型的应用：

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
```

**预期结果：** 命令退出码为 `0`，项目文件里出现 `VeloxDev.Core`。

一致性套件**不是 NuGet 包**。`Src/Test/Headless/VeloxDev.AdapterTestKit/VeloxDev.AdapterTestKit.csproj` 声明了 `<IsPackable>false</IsPackable>`，所以一致性测试要以工程引用的方式使用它：

```xml
<ItemGroup>
  <ProjectReference Include="..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  <ProjectReference Include="..\..\Src\Adapters\VeloxDev.WPF\VeloxDev.WPF.csproj" />
  <ProjectReference Include="..\..\Src\Test\Headless\VeloxDev.AdapterTestKit\VeloxDev.AdapterTestKit.csproj" />
</ItemGroup>
```

**预期结果：** 测试工程还原时，三条引用都能解析。

## 进入下一页之前

- 一个目标框架被所选适配器支持的测试或应用工程。
- `VeloxDev.Core` 可达 —— 直接引用，或通过某个适配器包传递。
- 不需要服务、数据库、密钥或网络。

**预期结果：** 在写入任何表面代码之前，`dotnet build` 空工程就能成功。
