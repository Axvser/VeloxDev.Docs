# 前置条件

## 支持的目标

这些来自库声明的 `TargetFrameworks`，不是示例碰巧运行的那一档。`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 声明：

```text
netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0
```

任何能消费其中一档的项目都能使用本特性。示例（`Examples/Tickable/WPF/Demo/Demo.csproj`）目标为 `net10.0-windows` 并启用 `<UseWPF>true</UseWPF>` —— 那只是一条*实测过*的配置，不是最低要求。

| 项目 | 要求 |
|---|---|
| 库目标框架 | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` |
| 包版本 | `VeloxDev.Core` 10.0.0 |
| 生成器包 | `VeloxDev.Core.Generator` 10.0.0（仅分析器，运行时不引用） |
| SDK / 运行时 | 能构建上述任一目标框架的 SDK；本文使用 .NET 10 SDK |
| 生成器编译器 | Roslyn 4.8+ —— 生成器针对 `Microsoft.CodeAnalysis.CSharp` 4.8.0 编译，请使用 .NET 8 SDK 或更高版本（或 VS 2022 17.8+）。低于 Roslyn 4.0 时包的 `.targets` 会发出 `VELOXCFG0001` |
| IDE / 编辑器 | 可选 —— 生成器在 `dotnet build` 中运行 |
| 外部服务 | **无。** 不需要 UI 适配器、服务宿主或配置文件 |

## 唯一的硬性要求：`partial`

源生成器把类的一半写进另一个文件，所以被标记的类必须声明为 `partial`。这是编译期要求，无需任何配置。

```csharp
[Tickable]
public partial class MyBehaviour   // <- `partial` 是必需的
{
}
```

## 不需要 UI 线程

两条泵运行在各自的后台线程上（异步循环模式下是 `async` 任务）。控制台 `Main`、单元测试、服务宿主与 WPF 窗口都是合法宿主。GUI 宿主**不会**自动获得封送：钩子运行在泵线程上，任何触碰 UI 的操作都必须由你交回 UI 线程 —— 要么通过 `TickManager.ExecuteOnMainThread`（它指向通道的 update 线程，不是 UI 线程），要么发布状态让 UI 线程轮询，WPF 示例采用后者（`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs`）。

## 浏览器与 iOS 的平台说明

`TickManager.UseAsyncLoop` 按构建目标初始化（`TickManager.cs` 第 1008-1013 行）：

```csharp
public static bool UseAsyncLoop { get; set; } =
#if NET5_0_OR_GREATER
    OperatingSystem.IsBrowser() || OperatingSystem.IsIOS();
#else
    true;
#endif
```

在 `net5.0` 及以上的目标上，只有进程运行于浏览器或 iOS 时它才初始为 `true`，其余运行时为 `false`（原生线程）。在 `netstandard2.0`、`netframework4.6.1` 与 `netcoreapp3.0` 上 `OperatingSystem` API 不可用，初始化器回退为 `true`。因此一个运行在桌面 .NET 上的 `netstandard2.0` 消费者默认拿到异步循环，除非显式设置该属性。可通过全局属性或按通道的 `SetUseAsyncLoop` 覆盖。

**预期结果：** 你能说出要构建的目标框架，并且本机有支持它的 SDK。此时尚未安装任何东西。
