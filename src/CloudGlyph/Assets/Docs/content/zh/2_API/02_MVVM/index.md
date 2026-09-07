# MVVM — API 参考

MVVM 功能让你无需 MVVM 基类、也无需手写属性样板代码即可编写视图模型：`VeloxPropertyAttribute` 标记字段或 `partial` 属性，MVVM 源生成器将其改写成支持 `INotifyPropertyChanging` / `INotifyPropertyChanged` 的属性；`VeloxCommandAttribute` 标记方法，Command 源生成器将其暴露为带异步执行、取消、排队与完整生命周期的 `IVeloxCommand` 实例。

运行时类型位于 `VeloxDev.Core` 的 `namespace VeloxDev.MVVM` 中，源码在 `Src/Core/VeloxDev.Core/MVVM`（命令接口在 `Src/Core/VeloxDev.Core/Interfaces/MVVM`）。两个生成器随分析器包 `VeloxDev.Core.Generator`（`Src/Generators/VeloxDev.Core.Generator`）发布，由 `VeloxDev.Core` 传递引用。

- 示例：`Examples/MVVM/WPF/Demo`、`Examples/MVVM/Avalonia/Demo`
- 测试：`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`

## 运行时类型 — 命名空间 `VeloxDev.MVVM`

- [VeloxPropertyAttribute](00_VeloxPropertyAttribute/index.md) — 从字段或 `partial` 属性生成可通知属性。
- [VeloxCommandAttribute](01_VeloxCommandAttribute/index.md) — 从方法生成 `IVeloxCommand` 属性。
- [IVeloxCommand](02_IVeloxCommand/index.md) — 命令契约：生命周期事件、异步执行、锁 / 中断 / 队列控制。
- [VeloxCommand](03_VeloxCommand/index.md) — 密封的运行时实现，及其构造函数与静态工厂。
- [CommandEventType](04_CommandEventType/index.md) — 单次执行的生命周期状态。
- [CommandEventHandler](05_CommandEventHandler/index.md) — 每个生命周期事件触发的委托。
- [CommandEventArgs](06_CommandEventArgs/index.md) — 每个生命周期事件携带的负载。
- [ObservableCollectionTracker](07_ObservableCollectionTracker/index.md) — 生成集合属性 getter 使用的弱订阅辅助类。

## 源生成器 — `VeloxDev.Core.Generator`（命名空间 `VeloxDev.Generators`）

- [MVVM 生成器](08_MVVM/index.md) — 从 `[VeloxProperty]` 成员生成通知属性，并补齐缺失的属性通知基础设施。
- [Command 生成器](09_Command/index.md) — 从 `[VeloxCommand]` 方法生成懒加载的 `IVeloxCommand` 属性。
