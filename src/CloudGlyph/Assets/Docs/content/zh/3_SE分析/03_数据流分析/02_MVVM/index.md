# 数据流分析 — MVVM

MVVM 特性有两个运行时面，外加一个同时喂养两者的编译期步骤：源生成器在 `partial` 类上产出可观察属性与懒加载 `IVeloxCommand` 属性，而 `VeloxCommand` 以容量受限的队列与生命周期事件执行被标注的方法。

`VeloxCommand` 本身与 UI 无关 —— 它用 `SemaphoreSlim` 和队列调度、串行化调用，并在调用方上下文上触发事件（除非设置了 `EventContext`）。当 WPF 或 Avalonia 的 `Button` 绑定到生成的命令时，框架在 UI 线程调用 `Execute` / `ExecuteAsync`，因此属性变更通知也在那里触发，绑定引擎可以同步更新。

## 子页面

| 页面 | 内容 |
|---|---|
| [属性与集合流](00_属性与集合流/index.md) | 生成器产出进入 `INotifyPropertyChanging` / `INotifyPropertyChanged`；集合路径经由 `ObservableCollectionTracker` |
| [命令生命周期](01_命令生命周期/index.md) | 执行管线：立即运行、排队、锁定下拒绝、中断与清空、`canValidate` 闸门 |
| [命令等待](02_命令等待/index.md) | `ExecuteAndWaitAsync` 路径，以及该设计相对 `ExecuteAsync` 唯一刻意保留的差别 |

## 公共参与者

| 参与者 | 源码 |
|---|---|
| `VeloxDev.Generators.MVVM` / `.Command` | `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs}` |
| 生成的 partial（`*_MVVM.g.cs`、`*_Commands.g.cs`） | 按类产出，`Writers/{MVVMWriter.cs, CommandWriter.cs}` |
| `IVeloxCommand` / `VeloxCommand` | `Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`、`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` |
| `ObservableCollectionTracker` | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` |
| 用户方法 / 属性钩子 | `Examples/MVVM/*/.../MainWindowViewModel.cs` |

> 来源：`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`（`ExecuteCore` 474、`ExecuteCoreAsync` 533、`OnExecutionCompletedAsync` 582、`TryStartPendingAsync` 794、`InterruptAsync` 642、`ClearAsync` 686、`ExecuteAndWaitAsync` 452）、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory` 394）、`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。
