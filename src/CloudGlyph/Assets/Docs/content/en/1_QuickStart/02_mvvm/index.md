# MVVM — Quick Start

The **mvvm** feature is the view-model layer of VeloxDev. Two Roslyn source generators in the analyzer package `VeloxDev.Core.Generator` (generator classes `VeloxDev.Generators.MVVM` and `VeloxDev.Generators.Command`) turn a plain `partial` class into a full MVVM view-model at compile time. There is no base class to inherit, no interface to declare and no service registration — you annotate members and the compiler writes the rest into `.g.cs` files.

- `[VeloxProperty]` on a private field (or a C# 13 `partial` property) expands it into a public observable property. When no base class already supplies the plumbing, the generator adds `INotifyPropertyChanging` / `INotifyPropertyChanged`, the two events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, and declares the `partial void On<Name>Changing(old, new)` / `partial void On<Name>Changed(old, new)` hooks you implement in your own part of the class.
- `[VeloxCommand]` on a method expands it into a lazily created `IVeloxCommand` property (`VeloxDev.MVVM.IVeloxCommand : System.Windows.Input.ICommand`, so it binds in WPF and Avalonia). Commands run asynchronously with a FIFO queue (a concurrency capacity, default `1`), optional per-execution `CancellationToken` support, an optional executability predicate, and a complete lifecycle-event stream.
- Collection properties (any `INotifyCollectionChanged`, e.g. `ObservableCollection<T>`) get lazy, duplicate-free subscription via `VeloxDev.MVVM.ObservableCollectionTracker` plus generated `partial void OnItemAddedTo<Name>`, `OnItemRemovedFrom<Name>`, `OnItemMovedIn<Name>`, `OnItemsResetIn<Name>` hooks and an overridable `OnCollectionChanged<T>`.

Beyond `ICommand`, the runtime answers three questions the interface cannot: **how a single call ended** (`ExecuteAndWaitAsync` → `CommandCompletion` / `CommandOutcome`), **whether the command is busy or backed up** (`IsBusy` / `ActiveCount` / `PendingCount`), and **which thread subscribers run on** (`EventContext`).

All runtime types live in namespace `VeloxDev.MVVM`: `VeloxPropertyAttribute`, `VeloxCommandAttribute`, `VeloxCommand`, `IVeloxCommand`, `IVeloxCommandCompletion`, `IVeloxCommandStatus`, `VeloxCommandExtensions`, `CommandEventArgs`, `CommandEventHandler`, `CommandEventType`, `CommandOutcome`, `CommandCompletion`, `ObservableCollectionTracker`. The runtime is plain .NET (`netstandard2.0` and up) with **no third-party dependency, no configuration file and no platform adapter** — because a command implements the .NET `ICommand`, a XAML binding needs nothing else. GUI demos ship for WPF (`Examples/MVVM/WPF/Demo`) and Avalonia (`Examples/MVVM/Avalonia/Demo`).

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages. They build toward the single runnable console program on the last page.

- [00 Prerequisites](00_prerequisites/index.md) — supported targets, SDK/runtime, and the "no services / no adapter" note
- [01 Install](01_install/index.md) — add `VeloxDev.Core` from NuGet or project-reference it from this repository
- [02 Define Properties](02_define-properties/index.md) — `[VeloxProperty]` field and `partial`-property forms, generated hooks, notification infrastructure
- [03 Define Commands](03_define-commands/index.md) — `[VeloxCommand]` method forms, auto-naming, executability predicates, lazy command properties
- [04 Observe Collections](04_observe-collections/index.md) — `ObservableCollectionTracker` and the generated collection hooks
- [05 Concurrency and Lifecycle](05_concurrency-and-lifecycle/index.md) — queue/concurrency cap, per-run cancellation, the eight lifecycle events, interrupt/clear/lock, `EventContext`
- [06 Await and Status](06_await-and-status/index.md) — `ExecuteAndWaitAsync`, `CommandCompletion` / `CommandOutcome`, `IsBusy` / `ActiveCount` / `PendingCount`
- [07 Verify and Complete Code](07_verify-and-complete-code/index.md) — the demos and tests that exercise the feature, the single runnable program, and the run declaration
