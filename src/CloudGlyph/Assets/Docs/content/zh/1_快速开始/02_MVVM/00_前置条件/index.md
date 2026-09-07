# MVVM — 前置条件

MVVM 层是纯粹的编译期 + .NET 运行时代码：源生成器产出通知机制，运行时类型是 `netstandard2.0` 程序集里的普通类/接口。它自身没有 GUI，所以下面的一切既能在无头控制台宿主里用，也能在 WPF/Avalonia 桌面演示里用。

## 1. 支持目标与工具链

- **支持目标**（来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`）：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`，`LangVersion` 设为 `latest`。该包可被 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 以及任何更新的运行时使用。
- **源生成器**（程序集 `VeloxDev.Core.Generator`）本身是 `netstandard2.0` 的 Roslyn 组件。其 csproj 引用 `Microsoft.CodeAnalysis.CSharp` 4.3.1 —— 兼容 Visual Studio 2022 17.3+ / .NET SDK 6.0.4xx 及更高版本。
- **语言级别：**
  - **字段**写法 `[VeloxProperty] private int _count;` 与 `[VeloxCommand]` 方法写法只用 `partial` 方法与 `partial` 类 —— 自 C# 9 / .NET 5 起可用，因此能在上面列出的每个目标上编译。
  - **`partial` 属性**写法 `[VeloxProperty] public partial int Count { get; set; }` 需要 C# 13（.NET 9+ SDK，或 `LangVersion` ≥ 13 / `latest`）。真实代码在用（例如 `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs`），它是可选写法。
- **包管理器：** NuGet / `dotnet` CLI。
- **演示配置（被验证过，非必需）：** `Examples/MVVM/WPF/Demo` 面向 `net9.0-windows`（WPF），`Examples/MVVM/Avalonia/Demo` 面向 `net9.0`（Avalonia）。

**预期结果：** `dotnet --version` 打印至少 6.0.4xx 的 SDK（想用 `partial` 属性写法需要 9.0+）；NuGet 源可达。

## 2. 你必须提供的服务

无。没有数据库、没有消息总线、没有 DI 容器、没有原生互操作、没有配置文件。该特性甚至不要求 UI 线程 —— 它只是一个你可以从任何地方调用的普通库。

**预期结果：** 不需要任何外部服务；一个 `partial` 类加这些特性就是全部输入面。

## 3. 无需平台适配器

由于生成的命令属性类型是 `IVeloxCommand : System.Windows.Input.ICommand`，XAML 的 `Command="{Binding ...}"` 直接用宿主框架自身的命令系统绑定即可。WPF 与 Avalonia 演示在没有**任何适配器包**的情况下使用该特性 —— 这与 Transition/Theme 特性不同（它们需要每种平台的适配器，见 `08_平台适配器` 特性）。除非你想在其上叠加带动画的命令/主题层，否则 MVVM 永远不会用到 platform-adapters 特性。

**预期结果：** MVVM 演示只需项目引用 `VeloxDev.Core` 即可构建（见下一页）；`Demo.csproj` 里不会出现 `VeloxDev.WPF` / `VeloxDev.Avalonia` 引用。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。支持目标来自 `VeloxDev.Core.csproj` 与生成器 csproj；演示配置来自 `Examples/MVVM/*/Demo/Demo.csproj`。
