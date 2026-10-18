# 弱引用类型 — 前置条件

## 1. 支持的目标框架

目标框架来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 的 `<TargetFrameworks>`：

```xml
<TargetFrameworks>netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0</TargetFrameworks>
```

因此四个弱引用类型可在 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ / .NET 8+，以及任何能引用 `netstandard2.0` 库的平台上使用。源码只是基于 `WeakReference<T>` 与 `ConditionalWeakTable<TKey, TValue>` 的普通集合；唯一的条件编译是 `#if NET` 下给 `WeakCache` 的 `TCacheKey` 参数加的裁剪器注解（`Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs` 第 1-4 行与第 21-24 行）。

**预期结果：** 最后一页的快速开始控制台程序以 `net10.0` 为目标（与测试项目 `VeloxDev.Core.Test` 相同）。这是*经过测试*的配置，不是最低要求——库本身支持上面列出的更老目标。

## 2. SDK / 运行时

弱引用类型不需要源生成器，也不需要运行时服务，因此*使用*它们只需要所选目标框架对应的 SDK。最后一页的示例以 `net10.0` 为目标，因此需要 .NET 10 SDK；库的其它目标只需匹配的工具链。本快速开始复现的构建与测试记录由 .NET 10 SDK 针对 `VeloxDev.Core.Test`（`net10.0`）产生。

**预期结果：** `dotnet --list-sdks` 列出你将用于构建的 SDK；要运行完整示例，其中必须包含 10.x。

## 3. 包管理器

NuGet / `dotnet` CLI。后续页面中的所有示例都使用 `dotnet` 命令与 `.csproj`。

**预期结果：** `dotnet` 解析到一个能构建项目目标框架的 SDK（`net10.0` 示例需要 10.x）。

## 4. 必需服务

无。这些类型就是 `VeloxDev.Core` 里的普通 .NET 集合：不需要数据库、网络、消息总线，也——与其它 VeloxDev 功能不同——不需要平台适配器。一个普通控制台宿主就足以观察回收与 GC 行为。

**预期结果：** 你可以只用一个空文件夹和一个文本编辑器完成本快速开始的余下部分。

## 5. 行为证据在哪里

弱引用类型**没有专用 GUI demo**（`Examples/` 只为 Workflow、MVVM、Theme、Transition、AOP 与 Tickable 提供演示）。权威行为证据是 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 下的 MSTest 套件：

- `WeakDelegateTests.cs` — 订阅/调用、移除、克隆、组合委托缓存、“订阅像普通事件一样保活处理器”这一性质，以及空处理器容忍。
- `WeakQueueTests.cs` — FIFO 顺序、peek 不移除、`Clear`、`EnqueueRange`、空值守卫、枚举与 `TrimExcess`。
- `WeakStackTests.cs` — LIFO 顺序、peek 不移除、`Clear`、`PushRange`、空值守卫、枚举与 `TrimExcess`。
- `WeakCacheTests.cs` — 增/改/查、覆盖、移除、`ForeachCache`，以及清理触发的驱逐记账。

这些测试钉住顺序与 API 行为；只有 `ASubscriptionKeepsItsHandlerAliveLikeAnOrdinaryEvent` 断言了 GC 结果（强缓存性质），没有任何测试断言以弱方式添加的条目真的会被回收。最后一页的可运行程序为四个类型都复现了*GC 后回收*行为（测试为何避开这一点，见 GC 行为页）。

**预期结果：** 读完本页后，你知道该功能是无界面的、不需要外部环境，并且由测试而非 demo 验证。
