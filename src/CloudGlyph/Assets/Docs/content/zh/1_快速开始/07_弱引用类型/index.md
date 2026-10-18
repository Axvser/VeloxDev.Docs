# 弱引用类型 — 快速开始

**弱引用类型**功能提供四个与 UI 无关的容器：它们通过*弱引用*持有内容，因此条目不会让其目标常驻内存。它们要解决的是 .NET 中经典的泄漏场景：一个长寿命的发布者、事件源或缓存，在短寿命的订阅者或键早已用完很久之后，仍通过强引用把它们留住。

四个类型都位于 `VeloxDev.Core` 包（源目录 `Src/Core/VeloxDev.Core/WeakTypes/`）中的 `VeloxDev.WeakTypes` 命名空间，不依赖任何 UI 适配器或外部服务，且都是 `sealed`：

- `WeakDelegate<TDelegate>`（`where TDelegate : Delegate`）——类事件的多处理器容器。每个处理器以 `WeakReference<Delegate>` 存入列表，存活处理器由 `Delegate.Combine` 合成一个缓存在 `volatile` 字段中的组合委托；读取该缓存不加锁。该缓存是**强引用**：并入缓存的处理器在下次重建把它排除之前一直被保活。以 `CanUpdateCache: false` 添加的处理器在添加时不会进入缓存；若它在下次重建前被 GC 回收，重建时即被丢弃（若届时仍存活，重建会把它并入新的强缓存并使其再次被 root）。
- `WeakQueue<T>`（`where T : class`）——由 `WeakReference<T>` 条目构成的 FIFO 缓冲区；已回收条目在访问时被剪除。
- `WeakStack<T>`（`where T : class`）——`WeakQueue<T>` 的 LIFO 对应物。
- `WeakCache<TTargetKey, TCacheKey>`（`where TTargetKey : class`，`where TCacheKey : class`）——基于 `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>` 的按目标键/值映射；值随目标键一起消亡，而不是把键留住。

四个类型都通过内部锁保证线程安全，形状与其强引用版 `System.Collections.Generic` 对应物一致，并由 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 中的 MSTest 套件验证（`WeakDelegateTests.cs`、`WeakQueueTests.cs`、`WeakStackTests.cs`、`WeakCacheTests.cs`）。本功能**没有专用 GUI demo**——测试是主要行为证据，最后一页的可运行程序以无界面方式覆盖四个类型。

`VeloxDev.Core` 包（`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 中 `Version` 为 `10.0.0`）多目标为 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0`；除此之外无需安装任何东西。

## 快速开始子页面

本功能的快速开始拆分为以下页面（它们逐步汇成最后一页的单个可运行程序）：

- [前置条件](00_前置条件/index.md) — 支持的目标、SDK/运行时，以及行为证据放在哪里
- [安装](01_安装/index.md) — 从 NuGet 添加 `VeloxDev.Core`，或在本仓库内使用项目引用
- [选择容器](02_选择容器/index.md) — 四种类型各适合什么场景（泄漏、FIFO/LIFO 缓冲、按目标存放的值）
- [弱委托](03_弱委托/index.md) — 类事件的弱订阅：`AddHandler` / `RemoveHandler` / `GetInvocationList` / `Invoke` / `Clone`
- [弱队列](04_弱队列/index.md) — 对短命工作项的 FIFO 处理
- [弱栈](05_弱栈/index.md) — 不能保活条目的 LIFO（撤销/重做式）栈
- [弱缓存](06_弱缓存/index.md) — 随目标键一起消亡的按目标存放值
- [GC 行为](07_GC行为/index.md) — “弱”究竟意味着什么、访问时清扫，以及 Debug/Release 的注意事项
- [验证与完整代码](08_验证与完整代码/index.md) — 测试、单个可运行程序、记录输出与运行声明
