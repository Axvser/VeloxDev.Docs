# MVVM — API Reference

The MVVM feature lets you author view-models without an MVVM base class and without hand-written property boilerplate. `VeloxPropertyAttribute` marks fields or `partial` properties that the MVVM source generator rewrites into `INotifyPropertyChanging` / `INotifyPropertyChanged`-backed properties; `VeloxCommandAttribute` marks methods that the Command source generator exposes as `IVeloxCommand` instances with async execution, cancellation, queueing and a full lifecycle.

The runtime types live in `VeloxDev.Core`, namespace `VeloxDev.MVVM`, under `Src/Core/VeloxDev.Core/MVVM` (the interfaces under `Src/Core/VeloxDev.Core/Interfaces/MVVM`). The generators ship in the analyzer package `VeloxDev.Core.Generator` (`Src/Generators/VeloxDev.Core.Generator`), which `VeloxDev.Core` references transitively.

- Examples: `Examples/MVVM/WPF/Demo`, `Examples/MVVM/Avalonia/Demo`
- Tests: `Src/Core/VeloxDev.Core.Test/MVVM/` (20 files)

## Runtime types — namespace `VeloxDev.MVVM`

| Page | Type | Kind |
|---|---|---|
| [VeloxPropertyAttribute](00_VeloxPropertyAttribute/index.md) | `VeloxPropertyAttribute` | attribute |
| [VeloxCommandAttribute](01_VeloxCommandAttribute/index.md) | `VeloxCommandAttribute` | attribute |
| [IVeloxCommand](02_IVeloxCommand/index.md) | `IVeloxCommand` | interface (`: ICommand`) |
| [IVeloxCommandCompletion](03_IVeloxCommandCompletion/index.md) | `IVeloxCommandCompletion` | interface |
| [IVeloxCommandStatus](04_IVeloxCommandStatus/index.md) | `IVeloxCommandStatus` | interface |
| [VeloxCommand](05_VeloxCommand/index.md) | `VeloxCommand` | sealed class (+ 4 sub-pages) |
| [VeloxCommandExtensions](06_VeloxCommandExtensions/index.md) | `VeloxCommandExtensions` | static class |
| [CommandEventType](07_CommandEventType/index.md) | `CommandEventType` | enum |
| [CommandEventHandler](08_CommandEventHandler/index.md) | `CommandEventHandler` | delegate |
| [CommandEventArgs](09_CommandEventArgs/index.md) | `CommandEventArgs` | sealed class |
| [CommandOutcome](10_CommandOutcome/index.md) | `CommandOutcome` | enum |
| [CommandCompletion](11_CommandCompletion/index.md) | `CommandCompletion` | readonly struct |
| [ObservableCollectionTracker](12_ObservableCollectionTracker/index.md) | `ObservableCollectionTracker` | static class |

`05_VeloxCommand` is split into four sub-pages — `00_constructors`, `01_execution`, `02_control`, `03_status-events-and-disposal` — because the type's full public surface does not fit one focused page.

## Source generators — `VeloxDev.Core.Generator`

| Page | Generator class | Emits |
|---|---|---|
| [MVVM generator](13_MVVM/index.md) | `VeloxDev.Generators.MVVM` | notification properties from `[VeloxProperty]` members, plus any missing property-notification infrastructure |
| [Command generator](14_Command/index.md) | `VeloxDev.Generators.Command` | lazy `IVeloxCommand` properties from `[VeloxCommand]` methods |

The generator diagnostic `VELOXCMD001` (`VeloxDev.Generators.Diagnostics.UnsupportedCommandSignature`) is documented on the `14_Command` page.

## Public-surface notes

- `CommandEventArgs.Cts`, `TakeCts()`, `Completion`, `TryMarkCancelReported()` and `Complete()` are **`internal`**; they are listed where they are declared but are not usable from consumer code.
- `CommandOutcome.Refused` has no `CommandEventType` counterpart.
- `VeloxCommand.CreateTaskOnlyWithValueTaskParameter` and `CreateTaskOnlyWithValueTaskCancellationToken` exist only under `#if !NETSTANDARD2_0 && !NETFRAMEWORK`.
