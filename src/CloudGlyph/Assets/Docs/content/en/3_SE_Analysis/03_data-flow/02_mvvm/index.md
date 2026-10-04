# Data Flow — MVVM

The MVVM feature has two runtime surfaces plus a compile-time step that feeds both: the source generator produces observable properties and lazy `IVeloxCommand` properties on a `partial` class, and `VeloxCommand` executes the annotated methods with a capacity-bounded queue and lifecycle events.

`VeloxCommand` itself is UI-agnostic — it schedules and serializes invocations with a `SemaphoreSlim` and a queue, and raises events on the calling context unless `EventContext` is set. When a WPF or Avalonia `Button` is bound to a generated command, the framework calls `Execute` / `ExecuteAsync` on the UI thread, so property-change notifications are raised there and the binding engine can update synchronously.

## Sub-pages

| Page | Covers |
|---|---|
| [Property and collection flow](00_property-and-collection-flow/index.md) | generator output into `INotifyPropertyChanging` / `INotifyPropertyChanged`; the collection path through `ObservableCollectionTracker` |
| [Command lifecycle](01_command-lifecycle/index.md) | the execution pipeline: immediate run, queueing, refusal under lock, interrupt and clear, the `canValidate` gate |
| [Command await](02_command-await/index.md) | the `ExecuteAndWaitAsync` path, and this design's one deliberate difference from `ExecuteAsync` |

## Common participants

| Participant | Source |
|---|---|
| `VeloxDev.Generators.MVVM` / `.Command` | `Src/Generators/VeloxDev.Core.Generator/{MVVM.cs, Command.cs}` |
| generated partial (`*_MVVM.g.cs`, `*_Commands.g.cs`) | emitted per class, `Writers/{MVVMWriter.cs, CommandWriter.cs}` |
| `IVeloxCommand` / `VeloxCommand` | `Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs`, `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` |
| `ObservableCollectionTracker` | `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` |
| user method / property hooks | `Examples/MVVM/*/.../MainWindowViewModel.cs` |

> Source references: `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` (`ExecuteCore` 474, `ExecuteCoreAsync` 533, `OnExecutionCompletedAsync` 582, `TryStartPendingAsync` 794, `InterruptAsync` 642, `ClearAsync` 686, `ExecuteAndWaitAsync` 452), `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory` 394), `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.
