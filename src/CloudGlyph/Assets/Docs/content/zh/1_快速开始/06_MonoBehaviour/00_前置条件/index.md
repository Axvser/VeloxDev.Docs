# MonoBehaviour — 前置条件

## 1. 支持目标

支持的目标框架来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 的 `<TargetFrameworks>` 元素：

```xml
<TargetFrameworks>netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0</TargetFrameworks>
```

因此运行时可从 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 以及任何能引用 `netstandard2.0` 库的平台使用。

**预期结果：** 本特性中的快速入门控制台程序以 `net10.0` 为目标；附带的 WPF 示例以 `net10.0-windows` 为目标。那些是*被验证过*的配置，并非最低要求 —— 库本身支持上面列出的更老目标。

## 2. SDK / 运行时

`[MonoBehaviour]` 特性依赖 Roslyn 源生成器，因此需要带 Roslyn 4.x 的 .NET SDK。本快速入门中所有构建与运行记录使用 SDK 9.0/10.0。

**消费**包时，只需要目标框架所对应的 SDK。**在本仓库内构建**时，还需 `netframework4.6.1` 的引用程序集（在构建 `net4x` 目标时以 `Microsoft.NETFramework.ReferenceAssemblies` 包自动还原）。

**预期结果：** `dotnet --list-sdks` 显示你将要使用的 SDK。

## 3. 包管理器

NuGet / `dotnet` CLI。后续页面所有示例都使用 `dotnet` 命令与 `.csproj`。

**预期结果：** `dotnet` 解析到 SDK 9.0+ 工具链。

## 4. 所需服务

无。帧循环完全运行在 `MonoBehaviourManager` 内部的线程上；不需要数据库、网络、消息总线，也不需要平台适配器。一个纯控制台宿主足以观察循环，这也是本页所有示例都用控制台程序的原因。

**预期结果：** 你可以用一个空文件夹和文本编辑器走完本快速入门其余部分。

## 5. 预先说明：并发

通道的两个泵运行在不同线程上（桌面默认原生 `Thread`；没有 `Thread` 的平台用 `async` 任务，见[运行与配置循环](../03_运行与配置循环/)页）。因此 `Update` 与 `FixedUpdate` 等钩子彼此并发执行。示例用 `System.Threading.Interlocked` 维护计数器，保证无论如何交错打印的数值都正确。

**预期结果：** 读完本页你知道该特性是一个无头、基于线程的帧循环，不需要任何外部搭建。
