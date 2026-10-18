# 数据流 — MVVM

该功能有两个运行面，外加一个同时喂养二者的编译期步骤：源生成器在 `partial` 类上产出可观察属性与懒加载命令属性，`CommandPipeline<TParam, TResult>` 则以有界队列和生命周期事件执行被标注的方法。

运行时与 UI 无关 —— 它用 `SemaphoreSlim` 与队列调度、串行化调用，并在调用上下文上触发事件，除非设置了 `EventContext`。当 WPF 或 Avalonia 的 `Button` 绑定到生成的命令时，框架在 UI 线程调用 `Execute` / `ExecuteAsync`，因此通知也在那里触发，绑定引擎同步更新。

## 子页面

| 页面 | 内容 |
| --- | --- |
| [属性与集合流](00_属性与集合流/index.md) | 生成器输出如何进入 `INotifyPropertyChanging` / `INotifyPropertyChanged`；集合经 `ObservableCollectionTracker` 的路径 |
| [命令生命周期](01_命令生命周期/index.md) | 立即运行、排队、锁下拒绝、中断与清空、`canValidate` 闸门 |
| [命令等待](02_命令等待/index.md) | `ExecuteAndWaitAsync` 路径、它的 sink，以及强类型结果通道 |

## 共同参与者

| 参与者 | 源码 |
| --- | --- |
| `VeloxDev.Generators.MVVM` / `.Command` | `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs}` |
| 生成的 partial（`*_MVVM.g.cs`、`*_Commands.g.cs`） | 每个类一份，`Writers/{MVVMWriter.cs, CommandWriter.cs}` |
| `IVeloxCommand` / `CommandPipeline<TParam, TResult>` / `VeloxCommand` | `Src/Core/VeloxDev.Core/Interfaces/MVVM/`、`Src/Core/VeloxDev.Core/MVVM/` |
| `ObservableCollectionTracker` | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` |
| 用户方法 / 属性钩子 | `Examples/MVVM/*/.../MainWindowViewModel.cs` |

> 源码参考：`Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs`（`ExecuteCore`、`ExecuteCoreAsync`、`OnExecutionCompletedAsync`、`TryStartPendingAsync`、`InterruptAsync`、`ClearAsync`、`ExecuteAndWaitAsync`）、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory`）、`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。
