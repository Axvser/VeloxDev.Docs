# MVVM — 前置条件

MVVM 层是纯粹的“编译期 + .NET 运行时”代码：源生成器产出通知基础设施，运行时类型则是 `netstandard2.0` 程序集里的普通类与接口。该特性自身没有 GUI，因此下面的一切既能用于 WPF / Avalonia 桌面演示，也能用于无界面的控制台宿主。

## 1. 支持目标与工具链

- **支持目标**（声明于 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`）：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0`，`LangVersion` 为 `latest`。因此该包可用于 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 以及更新的运行时。
- **源生成器**（`Src/Generators/VeloxDev.Core.Generator/VeloxDev.Core.Generator.csproj`）：`TargetFramework` 为 `netstandard2.0`，`IsRoslynComponent` 为 true，`Microsoft.CodeAnalysis.CSharp` **4.3.1**（private assets）。也就是说，Visual Studio 2022 17.3+ 或 .NET SDK 6.0.4xx 及以后都能运行它。生成器包声明的版本是 `10.0.0`；`VeloxDev.Core` 是 `10.0.0`。
- **编译器语言级别** —— 两种标注写法要求不同：
  - **字段**写法 `[VeloxProperty] private int _count;` 与 `[VeloxCommand]` 的方法写法只用 `partial` 方法与 `partial` 类 —— 自 C# 9 起可用，在所有列出的目标上都能编译。
  - **`partial` 属性**写法 `[VeloxProperty] public partial string Greeting { get; set; }` 需要 C# 13（.NET 9+ SDK，或 `LangVersion` ≥ 13 / `latest`）。该写法是可选的。
  - 演示中使用的集合表达式（`= []`）需要 C# 12。
- **包管理器**：NuGet 或 `dotnet` CLI。
- **演示配置（实测，非要求）**：`Examples/MVVM/WPF/Demo` 目标为 `net9.0-windows`（`<UseWPF>true</UseWPF>`）；`Examples/MVVM/Avalonia/Demo` 目标为 `net9.0`，Avalonia `11.3.0`。

**预期结果：** `dotnet --version` 输出至少 6.0.4xx 的 SDK（若要用 `partial` 属性写法或集合表达式初始化器，则需要 9.0+），且 NuGet 源可访问。

## 2. 需要你提供的服务

没有。没有数据库、没有消息总线、没有 DI 容器、没有原生互操作、没有配置文件。该特性甚至不要求 UI 线程 —— 它就是一个可以从任何地方调用的普通库。

**预期结果：** 不需要任何外部服务；一个 `partial` 类加上两个特性就是全部输入。

## 3. 不需要平台适配器

由于生成的命令属性类型是 `IVeloxCommand : System.Windows.Input.ICommand`，XAML 的 `Command="{Binding ...}"` 直接使用宿主框架自己的命令系统绑定。WPF 与 Avalonia 演示在**没有任何适配器包**的情况下使用本特性 —— 这与过渡动画、动态主题特性不同，后者确实需要各平台的适配器。除非你想在它之上叠加带动画的命令层或主题层，否则 MVVM 永远不碰平台适配器特性。

**预期结果：** MVVM 演示只要引用 `VeloxDev.Core`（以及为生成器准备的 analyzer 引用）即可构建；`Demo.csproj` 中不会出现 `VeloxDev.WPF` / `VeloxDev.Avalonia` 引用。

## 运行声明

- ✅ 2026-10-01 已部分执行。本特性实际运行过编译：

  ```text
  dotnet build Examples/MVVM/WPF/Demo/Demo.csproj -c Debug
    VeloxDev.Core.Generator -> ...\netstandard2.0\VeloxDev.Core.Generator.dll
    VeloxDev.Core           -> ...\net5.0\VeloxDev.Core.dll
    Demo                    -> ...\net9.0-windows\Demo.dll
  已成功生成。0 个警告 0 个错误

  dotnet build Examples/MVVM/Avalonia/Demo/Demo.csproj -c Debug
    Demo -> ...\net9.0\Demo.dll
  已成功生成。0 个警告 0 个错误
  ```

- 上面的目标框架与版本号是从 `VeloxDev.Core.csproj`、`VeloxDev.Core.Generator.csproj` 与两个 `Demo.csproj` 中读出的，不是从“构建成功”反推的。GUI 窗口本身未启动；可见行为的验证在快速开始的最后一页。
