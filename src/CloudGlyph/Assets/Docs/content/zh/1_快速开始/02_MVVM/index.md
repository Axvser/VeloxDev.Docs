# MVVM — 快速开始

**mvvm** 是 VeloxDev 的视图模型层。仅分析器包 `VeloxDev.Core.Generator` 中的两个 Roslyn 增量生成器（`VeloxDev.Generators.MVVM` 与 `VeloxDev.Generators.Command`）在编译期把一个普通 `partial` 类变成完整的 MVVM 视图模型：无需基类、无需声明接口、无需注册服务。

- 字段或 C# 13 `partial` 属性上的 `[VeloxProperty]` 会生成公开的可观察属性；当类中还没有通知基础设施时，还会生成 `INotifyPropertyChanging` / `INotifyPropertyChanged` 以及 `partial void On{Name}Changing(old, new)` / `On{Name}Changed(old, new)` 钩子。
- 方法上的 `[VeloxCommand]` 会生成懒加载的命令属性（`VeloxDev.MVVM.IVeloxCommand : System.Windows.Input.ICommand`，可直接在 WPF / Avalonia 中绑定）。命令带 FIFO 队列与并发上限、可选的每次执行 `CancellationToken`、可选的 `CanExecute` 校验、八个生命周期事件；强类型签名还提供可等待的返回值通道。
- 集合类型的属性成员通过 `ObservableCollectionTracker` 惰性订阅，并生成 `OnItemAddedTo{Name}`、`OnItemRemovedFrom{Name}`、`OnItemMovedIn{Name}`、`OnItemsResetIn{Name}` 四个 `partial` 钩子，以及可重写的 `OnCollectionChanged<T>`。

所有运行时类型位于 `VeloxDev.Core` 的 `VeloxDev.MVVM` 命名空间，目标框架为 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`。运行时没有第三方依赖，也不需要平台适配器。示例：`Examples/MVVM/WPF/Demo` 与 `Examples/MVVM/Avalonia/Demo`；测试：`Src/Core/VeloxDev.Core.Test/MVVM/`。

## 快速开始 — 子页面

- [00 前置条件](00_前置条件/index.md) —— 支持的目标框架、SDK 与编译器版本、所需服务
- [01 安装](01_安装/index.md) —— NuGet 或项目引用、分析器接线、唯一的 `using`
- [02 定义属性](02_定义属性/index.md) —— `[VeloxProperty]` 两种形态、生成的 setter 与钩子、通知基础设施探测
- [03 定义命令](03_定义命令/index.md) —— `[VeloxCommand]` 支持的签名、命名、校验、强类型命令、泛型方法
- [04 观察集合](04_观察集合/index.md) —— 惰性订阅与按动作分发的钩子
- [05 并发与生命周期](05_并发与生命周期/index.md) —— 队列、取消、八个事件、锁 / 中断 / 清空、`EventContext`
- [06 等待与状态](06_等待与状态/index.md) —— `ExecuteAndWaitAsync`、`CommandCompletion`、状态属性、强类型结果
- [07 验证与完整代码](07_验证与完整代码/index.md) —— 示例、测试、单个可运行程序与运行声明
