# MVVM — API 参考

MVVM 功能让你无需 MVVM 基类、也无需手写属性样板代码即可编写视图模型：`VeloxPropertyAttribute` 标记字段或 `partial` 属性，MVVM 源生成器将其改写成支持 `INotifyPropertyChanging` / `INotifyPropertyChanged` 的属性；`VeloxCommandAttribute` 标记方法，Command 源生成器将其暴露为带异步执行、取消、排队与完整生命周期的 `IVeloxCommand` 实例。

运行时类型位于 `VeloxDev.Core` 的 `namespace VeloxDev.MVVM` 中，源码在 `Src/Core/VeloxDev.Core/MVVM`（接口在 `Src/Core/VeloxDev.Core/Interfaces/MVVM`）。两个生成器随分析器包 `VeloxDev.Core.Generator`（`Src/Generators/VeloxDev.Core.Generator`）发布，由 `VeloxDev.Core` 传递引用。

- 示例：`Examples/MVVM/WPF/Demo`、`Examples/MVVM/Avalonia/Demo`
- 测试：`Src/Core/VeloxDev.Core.Test/MVVM/`（20 个文件）

## 运行时类型 — 命名空间 `VeloxDev.MVVM`

| 页面 | 类型 | 种类 |
|---|---|---|
| [VeloxPropertyAttribute](00_VeloxPropertyAttribute/index.md) | `VeloxPropertyAttribute` | 特性 |
| [VeloxCommandAttribute](01_VeloxCommandAttribute/index.md) | `VeloxCommandAttribute` | 特性 |
| [IVeloxCommand](02_IVeloxCommand/index.md) | `IVeloxCommand` | 接口（`: ICommand`） |
| [IVeloxCommandCompletion](03_IVeloxCommandCompletion/index.md) | `IVeloxCommandCompletion` | 接口 |
| [IVeloxCommandStatus](04_IVeloxCommandStatus/index.md) | `IVeloxCommandStatus` | 接口 |
| [VeloxCommand](05_VeloxCommand/index.md) | `VeloxCommand` | 密封类（含 4 个子页） |
| [VeloxCommandExtensions](06_VeloxCommandExtensions/index.md) | `VeloxCommandExtensions` | 静态类 |
| [CommandEventType](07_CommandEventType/index.md) | `CommandEventType` | 枚举 |
| [CommandEventHandler](08_CommandEventHandler/index.md) | `CommandEventHandler` | 委托 |
| [CommandEventArgs](09_CommandEventArgs/index.md) | `CommandEventArgs` | 密封类 |
| [CommandOutcome](10_CommandOutcome/index.md) | `CommandOutcome` | 枚举 |
| [CommandCompletion](11_CommandCompletion/index.md) | `CommandCompletion` | readonly 结构体 |
| [ObservableCollectionTracker](12_ObservableCollectionTracker/index.md) | `ObservableCollectionTracker` | 静态类 |

`05_VeloxCommand` 拆为四个子页 —— `00_构造`、`01_执行`、`02_控制`、`03_状态事件与释放` —— 因为该类型的完整公开面放不进一个聚焦的单页。

## 源生成器 — `VeloxDev.Core.Generator`

| 页面 | 生成器类 | 产出 |
|---|---|---|
| [MVVM 生成器](13_MVVM/index.md) | `VeloxDev.Generators.MVVM` | 从 `[VeloxProperty]` 成员生成通知属性，并补齐缺失的属性通知基础设施 |
| [Command 生成器](14_Command/index.md) | `VeloxDev.Generators.Command` | 从 `[VeloxCommand]` 方法生成懒加载的 `IVeloxCommand` 属性 |

生成器诊断 `VELOXCMD001`（`VeloxDev.Generators.Diagnostics.UnsupportedCommandSignature`）记录在 `14_Command` 页。

## 公开面注意事项

- `CommandEventArgs.Cts`、`TakeCts()`、`Completion`、`TryMarkCancelReported()` 与 `Complete()` 是 **`internal`**；它们在声明处被列出，但消费方代码无法使用。
- `CommandOutcome.Refused` 没有对应的 `CommandEventType`。
- `VeloxCommand.CreateTaskOnlyWithValueTaskParameter` 与 `CreateTaskOnlyWithValueTaskCancellationToken` 只在 `#if !NETSTANDARD2_0 && !NETFRAMEWORK` 下存在。
