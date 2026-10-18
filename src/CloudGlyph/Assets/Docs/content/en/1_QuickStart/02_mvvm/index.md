# MVVM — Quick Start

The **mvvm** feature is VeloxDev's view-model layer. Two Roslyn incremental generators in the analyzer-only package `VeloxDev.Core.Generator` (`VeloxDev.Generators.MVVM` and `VeloxDev.Generators.Command`) turn a plain `partial` class into a full MVVM view-model at compile time: no base class, no interface to declare, no service registration.

- `[VeloxProperty]` on a private field or a C# 13 `partial` property produces a public observable property, `INotifyPropertyChanging` / `INotifyPropertyChanged` plumbing when nothing else supplies it, and the `partial void On{Name}Changing(old, new)` / `On{Name}Changed(old, new)` hooks you implement.
- `[VeloxCommand]` on a method produces a lazily created `IVeloxCommand` property (`VeloxDev.MVVM.IVeloxCommand : System.Windows.Input.ICommand`, so it binds in WPF and Avalonia). The command has a FIFO queue with a concurrency cap, an optional per-execution `CancellationToken`, an optional executability predicate, eight lifecycle events, and — for typed signatures — an awaitable result.
- Collection-typed property members are subscribed lazily through `ObservableCollectionTracker`, with generated `partial` hooks `OnItemAddedTo{Name}`, `OnItemRemovedFrom{Name}`, `OnItemMovedIn{Name}`, `OnItemsResetIn{Name}` and an overridable `OnCollectionChanged<T>`.

All runtime types live in namespace `VeloxDev.MVVM` inside `VeloxDev.Core` (target frameworks `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`). The runtime has no third-party dependency and no platform adapter. Demos: `Examples/MVVM/WPF/Demo` and `Examples/MVVM/Avalonia/Demo`; tests: `Src/Core/VeloxDev.Core.Test/MVVM/`.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — supported targets, SDK and compiler levels, required services
- [01 Install](01_install/index.md) — NuGet or project reference, analyzer wiring, the single `using`
- [02 Define Properties](02_define-properties/index.md) — `[VeloxProperty]` forms, emitted setter and hooks, notification-infrastructure detection
- [03 Define Commands](03_define-commands/index.md) — `[VeloxCommand]` signatures, naming, validation, typed commands, generic methods
- [04 Observe Collections](04_observe-collections/index.md) — lazy subscription and the per-action hooks
- [05 Concurrency and Lifecycle](05_concurrency-and-lifecycle/index.md) — queue, cancellation, eight events, lock/interrupt/clear, `EventContext`
- [06 Await and Status](06_await-and-status/index.md) — `ExecuteAndWaitAsync`, `CommandCompletion`, status properties, typed results
- [07 Verify and Complete Code](07_verify-and-complete-code/index.md) — demos, tests, the single runnable program, run declaration
