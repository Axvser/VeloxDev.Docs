# 弱引用类型 — 前置条件

## 1. 支持目标

支持的目标框架来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 的 `<TargetFrameworks>` 元素：

```xml
<TargetFrameworks>netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0</TargetFrameworks>
```

因此四个弱类型可从 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 以及任何能引用 `netstandard2.0` 库的平台使用。它们内部没有任何平台相关代码 —— 只是建立在 `WeakReference<T>` 与 `ConditionalWeakTable<TKey, TValue>` 之上的普通集合。

**预期结果：** 最后一页的快速入门控制台程序以 `net10.0` 为目标（与测试项目 `VeloxDev.Core.Test` 的目标一致）。那是*被验证过*的配置，并非最低要求 —— 库本身支持上面列出的更老目标。

## 2. SDK / 运行时

弱类型不需要源生成器、也不需要运行时服务，因此**消费**它们只需要目标框架所对应的 SDK。本快速入门中所有构建与运行记录使用 .NET SDK 9.0 / 10.0 工具链。

**预期结果：** `dotnet --list-sdks` 显示你将要使用的 SDK（SDK 9.0+ 工具链即可）。

## 3. 包管理器

NuGet / `dotnet` CLI。后续页面所有示例都使用 `dotnet` 命令与 `.csproj`。

**预期结果：** `dotnet` 解析到 SDK 9.0+ 工具链。

## 4. 所需服务

无。这些类型是 `VeloxDev.Core` 里的纯 .NET 集合；不需要数据库、网络、消息总线，也不需要 —— 与 VeloxDev 其它特性不同 —— 任何平台适配器。一个纯控制台宿主足以观察集合与 GC 行为。

**预期结果：** 你可以用一个空文件夹和文本编辑器走完本快速入门其余部分。

## 5. 行为证据所在位置

弱类型**没有专用 GUI 示例**（`Examples/` 树里只有 Workflow、MVVM、Theme、Transition、AOP 与 MonoBehaviour 的示例）。权威的行为证据是 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 下的 MSTest 套件：

- `WeakDelegateTests.cs` —— 订阅/调用、移除、克隆、组合委托缓存与 null 处理器的容忍。
- `WeakQueueTests.cs` —— FIFO 顺序、窥视不移除、`Clear`、`EnqueueRange`、null 防护、枚举与 `TrimExcess`。
- `WeakStackTests.cs` —— LIFO 顺序、窥视不移除、`Clear`、`PushRange`、null 防护、枚举与 `TrimExcess`。
- `WeakCacheTests.cs` —— 增改读、覆盖写、移除、`ForeachCache`，以及触发清理的簿记。

最后一页那个可运行的程序复现了单元测试刻意不去断言的“GC 后回收”行为（原因见 [GC行为与注意](../07_GC行为与注意/) 页）。

**预期结果：** 读完本页你知道该特性无头、无需外部搭建，并由测试而非示例来验证。
