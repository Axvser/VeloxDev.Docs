# MVVM — 快速开始

**mvvm** 特性是 VeloxDev 的视图模型层。分析器包 `VeloxDev.Core.Generator` 中的两个 Roslyn 源生成器（生成器类为 `VeloxDev.Generators.MVVM` 与 `VeloxDev.Generators.Command`）在编译期把一个普通的 `partial` 类变成完整的 MVVM 视图模型。不需要继承基类、不需要声明接口、不需要注册服务 —— 你只需标注成员，编译器把其余部分写进 `.g.cs` 文件。

- 在私有字段（或 C# 13 的 `partial` 属性）上加 `[VeloxProperty]`，会把它展开为公开可观察属性。当基类没有提供通知基础时，生成器会补上 `INotifyPropertyChanging` / `INotifyPropertyChanged`、两个事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)`，并声明 `partial void On<名称>Changing(old, new)` / `partial void On<名称>Changed(old, new)` 钩子供你在类的另一半实现。
- 在方法上加 `[VeloxCommand]`，会把它展开为懒加载的 `IVeloxCommand` 属性（`VeloxDev.MVVM.IVeloxCommand : System.Windows.Input.ICommand`，因此可被 WPF、Avalonia 绑定）。命令以异步方式运行，带 FIFO 队列（并发容量，默认 `1`）、可选的每次执行 `CancellationToken` 支持、可选的可执行性谓词，以及完整的生命周期事件流。
- 集合属性（任何 `INotifyCollectionChanged`，例如 `ObservableCollection<T>`）经由 `VeloxDev.MVVM.ObservableCollectionTracker` 获得懒加载、去重的订阅，并生成 `partial void OnItemAddedTo<名称>`、`OnItemRemovedFrom<名称>`、`OnItemMovedIn<名称>`、`OnItemsResetIn<名称>` 钩子，外加可重写的 `OnCollectionChanged<T>`。

在 `ICommand` 之外，运行时还回答 `ICommand` 回答不了的三个问题：**单次调用是怎么结束的**（`ExecuteAndWaitAsync` → `CommandCompletion` / `CommandOutcome`）、**命令当前是否繁忙或积压**（`IsBusy` / `ActiveCount` / `PendingCount`）、以及**订阅者在哪个线程上运行**（`EventContext`）。

所有运行时类型都在 `VeloxDev.MVVM` 命名空间下：`VeloxPropertyAttribute`、`VeloxCommandAttribute`、`VeloxCommand`、`IVeloxCommand`、`IVeloxCommandCompletion`、`IVeloxCommandStatus`、`VeloxCommandExtensions`、`CommandEventArgs`、`CommandEventHandler`、`CommandEventType`、`CommandOutcome`、`CommandCompletion`、`ObservableCollectionTracker`。运行时是纯 .NET（`netstandard2.0` 及以上），**无第三方依赖、无配置文件、无平台适配器** —— 因为命令实现了 .NET `ICommand`，XAML 绑定不需要任何额外的东西。GUI 演示提供 WPF（`Examples/MVVM/WPF/Demo`）与 Avalonia（`Examples/MVVM/Avalonia/Demo`）两个版本。

## 快速开始 — 子页面

本特性的快速入门拆分为下列页面，逐步导向最后一页那个可运行的单文件控制台程序。

- [00 前置条件](00_前置条件/index.md) — 支持目标、SDK/运行时，以及“无需服务 / 无需适配器”说明
- [01 安装依赖](01_安装依赖/index.md) — 从 NuGet 添加 `VeloxDev.Core`，或在本仓库中项目引用它
- [02 定义可观察属性](02_定义可观察属性/index.md) — `[VeloxProperty]` 的字段与 `partial` 属性两种写法、生成的钩子、通知基础设施
- [03 定义命令](03_定义命令/index.md) — `[VeloxCommand]` 方法形态、自动命名、可执行性谓词、懒加载命令属性
- [04 观察集合变化](04_观察集合变化/index.md) — `ObservableCollectionTracker` 与生成的集合钩子
- [05 并发取消与生命周期](05_并发取消与生命周期/index.md) — 队列/并发容量、每次运行的取消、八个生命周期事件、interrupt/clear/lock、`EventContext`
- [06 等待与状态](06_等待与状态/index.md) — `ExecuteAndWaitAsync`、`CommandCompletion` / `CommandOutcome`、`IsBusy` / `ActiveCount` / `PendingCount`
- [07 验证与完整代码](07_验证与完整代码/index.md) — 覆盖该特性的演示与测试、可运行的单文件程序、运行声明
