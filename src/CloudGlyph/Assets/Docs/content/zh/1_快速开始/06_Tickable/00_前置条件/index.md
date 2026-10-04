# 00 · 前置条件

## 支持的目标

以下取自库自身声明的 `TargetFrameworks`，而不是取自演示恰好跑在哪个框架上。`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 声明：

```text
netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0
```

任何能消费其中之一的工程都可以使用本特性。演示（`Examples/Tickable/WPF/Demo/Demo.csproj`）目标为 `net10.0-windows` 且 `<UseWPF>true</UseWPF>` —— 那只是一个**被测过**的配置，不是最低要求。

| 项目 | 要求 |
|---|---|
| 库的目标框架 | `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0` |
| 包版本 | `VeloxDev.Core` 10.0.0 |
| 生成器包 | `VeloxDev.Core.Generator` 10.0.0（仅作分析器，运行期不引用） |
| SDK / 运行时 | 能构建上述任一目标框架的 SDK 即可；本指南的走查使用 .NET 10 SDK 构建 `net10.0` |
| IDE / 编辑器 | 可选 —— 生成器在 `dotnet build` 内部运行 |
| 所需服务 | **无。** 不需要 UI 适配器、不需要服务宿主、不需要配置文件 |

## 唯一的硬性要求：`partial`

源生成器把它的那一半写进另一个文件，所以你标记的类必须声明为 `partial`。这是编译期要求，报错也在编译期 —— 没有任何需要配置的东西。

```csharp
[Tickable]
public partial class MyBehaviour   // <- `partial` 是必需的
{
}
```

## 不要求 UI 线程

两个泵运行在各自的后台线程上（异步模式下是 `async` 任务）。控制台 `Main`、单元测试、服务宿主与 WPF 窗口都是同样合法的宿主。GUI 宿主**不会**自动获得线程封送：钩子运行在泵线程上，任何触碰 UI 的动作都必须由你交回 UI 线程 —— 要么通过 `TickManager.ExecuteOnMainThread`，要么发布状态让 UI 线程轮询（WPF 演示走的是后者，见 `Examples/Tickable/WPF/Demo/MainWindow.xaml.cs`）。

## 浏览器与 iOS 的平台说明

当 `OperatingSystem.IsBrowser()` 或 `OperatingSystem.IsIOS()` 为真时，`TickManager.UseAsyncLoop` 默认为 `true`，因为这些运行时无法启动专门的 `Thread`。在 `net5.0` 及以后的目标上，其他运行时常量为 `false`（原生线程）；而在 `netstandard2.0`、`netframework4.6.1`、`netcoreapp3.0` 目标上并不存在 `OperatingSystem` API，所以那里的初始化也回退为 `true`。你可以通过该属性全局覆盖，或用 `SetUseAsyncLoop` 按通道覆盖。

**预期结果：** 你能说出自己要构建的目标框架，并且手上有支持它的 SDK。此时还没有安装任何东西。
