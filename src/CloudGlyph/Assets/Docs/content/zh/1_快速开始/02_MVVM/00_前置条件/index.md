# MVVM — 前置条件

MVVM 层由编译期生成与普通 .NET 运行时代码组成，自身没有 GUI，因此同一份视图模型既能跑在无头控制台宿主里，也能跑在 WPF / Avalonia 示例中。

## 1. 支持的目标与工具链

- **运行时目标** —— 由 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 声明：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`，`LangVersion` 为 `latest`。因此可从 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 及更新运行时消费。
- **生成器** —— `Src/Generators/VeloxDev.Core.Generator/VeloxDev.Core.Generator.csproj` 目标为 `netstandard2.0`，`IsRoslynComponent` 为 true，引用 `Microsoft.CodeAnalysis.CSharp` **4.8.0**（私有资产）。这正是 .NET 8 SDK 自带的编译器版本，因此 .NET SDK 8.0+ 都能运行它。生成器包版本为 `10.0.0`，与 `VeloxDev.Core` 相同。
- **编译语言级别** —— 两种标注形态的要求不同：
  - 字段形态 `[VeloxProperty] private int _count;` 与全部 `[VeloxCommand]` 形态只需要 `partial` 类 / 方法：C# 9。
  - `partial` 属性形态 `[VeloxProperty] public partial string Greeting { get; set; }` 需要 C# 13（.NET 9+ SDK，或 `LangVersion` ≥ 13）。
  - 示例中的集合表达式（`= []`）需要 C# 12。
- **包管理器** —— NuGet 或 `dotnet` CLI。
- **示例配置（已测试，非最低要求）** —— `Examples/MVVM/WPF/Demo` 目标为 `net9.0-windows`、`<UseWPF>true</UseWPF>`；`Examples/MVVM/Avalonia/Demo` 目标为 `net9.0`、Avalonia `11.3.0`。

**预期结果：** `dotnet --version` 输出 8.0.x 或更高；`dotnet nuget list source` 中至少有一个可访问的源。

## 2. 需要你提供的服务

无。没有数据库、消息总线、DI 容器、原生互操作或配置文件；该功能也不要求 UI 线程。

**预期结果：** 一个 `partial` 类加上特性就是全部输入面。

## 3. 不需要平台适配器

生成的命令属性是 `IVeloxCommand`，而它派生自 `System.Windows.Input.ICommand`，因此 XAML 的 `Command="{Binding ...}"` 直接走宿主框架自己的命令系统。两个示例都只引用了 `VeloxDev.Core`（外加分析器），其 `.csproj` 中没有 `VeloxDev.WPF` 或 `VeloxDev.Avalonia`。

**预期结果：** `Demo.csproj` 中只有对 `VeloxDev.Core` 的项目引用，以及下一页给出的生成器接线。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `VeloxDev.Core.csproj`、`VeloxDev.Core.Generator.csproj` 与两个 `Demo.csproj` 做了静态核对。框架与版本结论来自这些文件；未启动 GUI 窗口。
