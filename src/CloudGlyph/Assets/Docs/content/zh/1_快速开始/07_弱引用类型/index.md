# 弱引用类型 — 快速开始

**weak-types** 特性提供四个与框架无关的集合类型，它们通过*弱引用*持有内容，因此条目永远不会让自己的目标存活。它们用来防止 .NET 中最经典的泄漏：长期存活的发布者、事件源或缓存，通过强引用把早就该结束生命周期的订阅者与键一直保活。

四个类型都位于 `VeloxDev.Core` 包内的 `VeloxDev.WeakTypes` 命名空间（源码目录 `Src/Core/VeloxDev.Core/WeakTypes/`），没有 UI 适配器、没有运行时依赖，且都是 `sealed`：

- `WeakDelegate<TDelegate>`（`where TDelegate : Delegate`）—— 一个类似事件的多处理器汇，把每个处理器存为 `WeakReference<Delegate>`。订阅者一旦被回收便自动从列表中消失，发布者不会因它而继续存活某个已死的监听者。读取走无锁的已缓存组合委托。
- `WeakQueue<T>`（`where T : class`）—— `WeakReference<T>` 条目的 FIFO 缓冲；访问时剪除已死条目。
- `WeakStack<T>`（`where T : class`）—— `WeakQueue<T>` 的 LIFO 对应物。
- `WeakCache<TTargetKey, TCacheKey>`（`where TTargetKey : class`、`where TCacheKey : class`）—— 建立在 `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>` 上的“按目标键”键值表。值随目标键一起消亡，而不是反过来把键保活。

每个类型都通过内部锁保证线程安全，成员形状贴近其强引用版的 `System.Collections.Generic` 对应物，并由 `Src/Core/VeloxDev.Core.Test/WeakTypes/` 下的 MSTest 套件覆盖（`WeakDelegateTests.cs`、`WeakQueueTests.cs`、`WeakStackTests.cs`、`WeakCacheTests.cs`）。本特性**没有专用 GUI 示例** —— 测试是主要的行为证据，最后一页那个可运行的程序以无头方式跑遍全部四个类型。

`VeloxDev.Core` 包多目标 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`；除此之外无需安装任何东西。

## 快速开始 — 子页面

本特性的快速入门拆分为下列页面（逐步导向最后一页那个可运行的单文件程序）：

- [00 前置条件](00_前置条件/) — 支持目标、SDK/运行时，以及行为证据所在位置
- [01 安装依赖](01_安装依赖/) — 从 NuGet 添加 `VeloxDev.Core`，或在本仓库中项目引用它
- [02 选择集合类型](02_选择集合类型/) — 哪个类型适合哪种场景（泄漏、FIFO/LIFO 缓冲、按目标键存值）
- [03 弱委托订阅](03_弱委托订阅/) — 事件式弱订阅：`AddHandler` / `RemoveHandler` / `GetInvocationList` / `Invoke` / `Clone`
- [04 弱队列](04_弱队列/) — 对临时工作项做 FIFO 处理
- [05 弱栈](05_弱栈/) — 不能把对象保活的 LIFO 撤销/回退栈
- [06 弱缓存](06_弱缓存/) — 随键消亡的“按目标键”值
- [07 GC行为与注意](07_GC行为与注意/) — “弱”到底意味着什么、访问时清扫，以及 Debug/Release 下的注意事项
- [08 验证与完整代码](08_验证与完整代码/) — 测试、可运行的单文件程序、记录到的输出、运行声明
