# MVVM — API Reference

The MVVM feature lets you author view-models without an MVVM base class and without hand-written property boilerplate. `VeloxPropertyAttribute` marks fields or `partial` properties that the MVVM generator rewrites into `INotifyPropertyChanging` / `INotifyPropertyChanged`-backed properties; `VeloxCommandAttribute` marks methods that the Command generator exposes as command instances with async execution, cancellation, queueing and a lifecycle.

Runtime types live in `VeloxDev.Core`, namespace `VeloxDev.MVVM`, under `Src/Core/VeloxDev.Core/MVVM` (interfaces under `Src/Core/VeloxDev.Core/Interfaces/MVVM`). The generators ship in the analyzer package `VeloxDev.Core.Generator` (`Src/Generators/VeloxDev.Core.Generator`).

- Examples: `Examples/MVVM/WPF/Demo`, `Examples/MVVM/Avalonia/Demo`, `Examples/MVVM/Common/Lib`
- Tests: `Src/Core/VeloxDev.Core.Test/MVVM/`

## Runtime types — namespace `VeloxDev.MVVM`

| Page | Type | Kind |
| --- | --- | --- |
| [VeloxPropertyAttribute](00_VeloxPropertyAttribute/index.md) | `VeloxPropertyAttribute` | attribute |
| [VeloxCommandAttribute](01_VeloxCommandAttribute/index.md) | `VeloxCommandAttribute` | sealed attribute |
| [IVeloxCommand](02_IVeloxCommand/index.md) | `IVeloxCommand` | interface (`: ICommand`) |
| [IVeloxCommandCompletion](03_IVeloxCommandCompletion/index.md) | `IVeloxCommandCompletion` | interface |
| [IVeloxCommandStatus](04_IVeloxCommandStatus/index.md) | `IVeloxCommandStatus` | interface |
| [VeloxCommand](05_VeloxCommand/index.md) | `VeloxCommand` | class (+ 4 sub-pages) |
| [VeloxCommandExtensions](06_VeloxCommandExtensions/index.md) | `VeloxCommandExtensions` | static class |
| [CommandEventType](07_CommandEventType/index.md) | `CommandEventType` | enum |
| [CommandEventHandler](08_CommandEventHandler/index.md) | `CommandEventHandler`, `CommandEventHandler<TParam, TResult>` | delegates |
| [CommandEventArgs](09_CommandEventArgs/index.md) | `CommandEventArgs` | class |
| [CommandOutcome](10_CommandOutcome/index.md) | `CommandOutcome` | enum |
| [CommandCompletion](11_CommandCompletion/index.md) | `CommandCompletion` | readonly struct |
| [ObservableCollectionTracker](12_ObservableCollectionTracker/index.md) | `ObservableCollectionTracker` | static class |
| [IVeloxCommandResult](15_IVeloxCommandResult/index.md) | `IVeloxCommandResult` | interface |
| [Typed commands](16_typed-commands/index.md) | `IVeloxCommand<TParam, TResult>`, `IVeloxCommandEvents<TParam, TResult>`, `CommandPipeline<TParam, TResult>`, `VeloxCommand<TParam, TResult>`, `CommandEventArgs<TParam, TResult>` | interfaces, base class, classes |

`05_VeloxCommand` is split into four sub-pages — `00_constructors`, `01_execution`, `02_control`, `03_status-events-and-disposal` — because the type's full public surface does not fit one focused page.

## Source generators — `VeloxDev.Core.Generator`

| Page | Generator class | Emits |
| --- | --- | --- |
| [MVVM generator](13_MVVM/index.md) | `VeloxDev.Generators.MVVM` | notification properties from `[VeloxProperty]` members, plus any missing property-notification infrastructure |
| [Command generator](14_Command/index.md) | `VeloxDev.Generators.Command` | lazy command properties and generic command accessors from `[VeloxCommand]` methods |

Diagnostics: `VELOX_MVVM_CMD001` (unsupported command signature), `VELOX_MVVM_PROP001`–`VELOX_MVVM_PROP003` (conflicting, unusable, or non-partial property declarations), and `VELOX_LANGVERSION001` (the project's language version is below what the generated code needs). They are documented on the generator pages.

## Public-surface notes

- `CommandEventArgs.Cts`, `TakeCts()`, `Completion`, `TryMarkCancelReported()` and `Complete()` are **`internal`**.
- `CommandOutcome.Refused` has no `CommandEventType` counterpart.
- `VeloxCommand.CreateTaskOnlyWithValueTaskParameter` and `CreateTaskOnlyWithValueTaskCancellationToken` exist only under `#if !NETSTANDARD2_0 && !NETFRAMEWORK`.
- `CommandPipeline<TParam, TResult>` is public and abstract; `VeloxCommand` and the arity family derive from it. Most consumers use `VeloxCommand` or a generated property and never name it.
