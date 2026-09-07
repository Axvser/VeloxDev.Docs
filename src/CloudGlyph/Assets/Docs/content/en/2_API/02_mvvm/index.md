# MVVM — API Reference

The MVVM feature lets you author view-models without a MVVM base class and without hand-written property boilerplate. `VeloxPropertyAttribute` marks fields or `partial` properties that the MVVM source generator rewrites into `INotifyPropertyChanging` / `INotifyPropertyChanged`-backed properties; `VeloxCommandAttribute` marks methods that the Command source generator exposes as `IVeloxCommand` instances with async execution, cancellation, queueing and a full lifecycle.

The runtime types live in `VeloxDev.Core`, in `namespace VeloxDev.MVVM`, under `Src/Core/VeloxDev.Core/MVVM` (the command interface under `Src/Core/VeloxDev.Core/Interfaces/MVVM`). The two generators ship in the analyzer package `VeloxDev.Core.Generator` (`Src/Generators/VeloxDev.Core.Generator`), which `VeloxDev.Core` references transitively.

- Examples: `Examples/MVVM/WPF/Demo`, `Examples/MVVM/Avalonia/Demo`
- Tests: `Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`

## Runtime types — namespace `VeloxDev.MVVM`

- [VeloxPropertyAttribute](00_VeloxPropertyAttribute/index.md) — generates a change-notifying property from a field or a `partial` property.
- [VeloxCommandAttribute](01_VeloxCommandAttribute/index.md) — generates an `IVeloxCommand` property from a method.
- [IVeloxCommand](02_IVeloxCommand/index.md) — the command contract: lifecycle events, async execution, and lock / interrupt / queue controls.
- [VeloxCommand](03_VeloxCommand/index.md) — the sealed runtime implementation, its constructors and static factories.
- [CommandEventType](04_CommandEventType/index.md) — the per-execution lifecycle states.
- [CommandEventHandler](05_CommandEventHandler/index.md) — the delegate raised for each lifecycle event.
- [CommandEventArgs](06_CommandEventArgs/index.md) — the payload carried by every lifecycle event.
- [ObservableCollectionTracker](07_ObservableCollectionTracker/index.md) — weak subscription helper used by generated collection-property getters.

## Source generators — `VeloxDev.Core.Generator` (namespace `VeloxDev.Generators`)

- [MVVM generator](08_MVVM/index.md) — emits notification properties from `[VeloxProperty]` members, plus any missing property-notification infrastructure.
- [Command generator](09_Command/index.md) — emits lazy `IVeloxCommand` properties from `[VeloxCommand]` methods.
