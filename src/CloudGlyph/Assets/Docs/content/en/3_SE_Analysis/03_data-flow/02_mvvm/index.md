# Data Flow — MVVM

The feature has two runtime surfaces plus a compile-time step that feeds both: the source generators produce observable properties and lazy command properties on a `partial` class, and `CommandPipeline<TParam, TResult>` executes the annotated methods with a capacity-bounded queue and lifecycle events.

The runtime is UI-agnostic — it schedules and serializes invocations with a `SemaphoreSlim` and a queue, and raises events on the calling context unless `EventContext` is set. When a WPF or Avalonia `Button` is bound to a generated command, the framework calls `Execute` / `ExecuteAsync` on the UI thread, so notifications are raised there and the binding engine updates synchronously.

## Sub-pages

| Page | Covers |
| --- | --- |
| [Property and collection flow](00_property-and-collection-flow/index.md) | generator output into `INotifyPropertyChanging` / `INotifyPropertyChanged`; the collection path through `ObservableCollectionTracker` |
| [Command lifecycle](01_command-lifecycle/index.md) | immediate run, queueing, refusal under lock, interrupt and clear, the `canValidate` gate |
| [Command await](02_command-await/index.md) | the `ExecuteAndWaitAsync` path, its sink, and the typed result channel |

## Common participants

| Participant | Source |
| --- | --- |
| `VeloxDev.Generators.MVVM` / `.Command` | `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs}` |
| generated partial (`*_MVVM.g.cs`, `*_Commands.g.cs`) | emitted per class, `Writers/{MVVMWriter.cs, CommandWriter.cs}` |
| `IVeloxCommand` / `CommandPipeline<TParam, TResult>` / `VeloxCommand` | `Src/Core/VeloxDev.Core/Interfaces/MVVM/`, `Src/Core/VeloxDev.Core/MVVM/` |
| `ObservableCollectionTracker` | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` |
| user method / property hooks | `Examples/MVVM/*/.../MainWindowViewModel.cs` |

> Source references: `Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs` (`ExecuteCore`, `ExecuteCoreAsync`, `OnExecutionCompletedAsync`, `TryStartPendingAsync`, `InterruptAsync`, `ClearAsync`, `ExecuteAndWaitAsync`), `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory`), `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.
