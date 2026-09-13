# MVVM — Quick Start

The **mvvm** feature is the view-model layer of VeloxDev: two Roslyn source generators (in assembly `VeloxDev.Core.Generator`, generator classes `VeloxDev.Generators.MVVM` and `VeloxDev.Generators.Command`) turn a plain `partial` class into a full MVVM view-model at compile time. There is no base class to inherit, no interface to declare and no service registration — you annotate members and the compiler writes the rest into `.g.cs` files.

- `[VeloxProperty]` on a private field (or a `partial` property) expands it into a public observable property. When no base class already provides the plumbing, the generator adds the `INotifyPropertyChanging` / `INotifyPropertyChanged` interfaces, the events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, and declares `partial void On<Name>Changing(old, new)` / `partial void On<Name>Changed(old, new)` hooks you can implement in your own part of the class.
- `[VeloxCommand]` on a method expands it into a lazily created `IVeloxCommand` property (`VeloxDev.MVVM.IVeloxCommand : System.Windows.Input.ICommand`, so it binds in WPF and Avalonia). Commands run asynchronously with a FIFO queue (a semaphore capacity, default `1`), per-execution `CancellationToken` support, an optional executability predicate, and a complete lifecycle-event stream (`Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`).
- Collection properties (any `INotifyCollectionChanged`, e.g. `ObservableCollection<T>`) get lazy, duplicate-free subscription via `VeloxDev.MVVM.ObservableCollectionTracker` and generated `partial void OnItemAddedTo<Name>`, `OnItemRemovedFrom<Name>`, `OnItemMovedIn<Name>`, `OnItemsResetIn<Name>` hooks, plus an overridable `OnCollectionChanged<T>`.

All types live in namespace `VeloxDev.MVVM` (`VeloxPropertyAttribute`, `VeloxCommandAttribute`, `VeloxCommand`, `IVeloxCommand`, `CommandEventArgs`, `CommandEventHandler`, `CommandEventType`, `ObservableCollectionTracker`). The runtime is plain .NET (`netstandard2.0`) with **no third-party dependency, no configuration file, and no platform adapter** — because the command type implements the .NET `ICommand`, a XAML binding needs nothing else. GUI demos are provided for WPF (`Examples/MVVM/WPF/Demo`) and Avalonia (`Examples/MVVM/Avalonia/Demo`).

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages (they build toward the single runnable program on the last page):

- [00 Prerequisites](00_prerequisites/) — supported targets, SDK/runtime, and the "no services / no adapter" note
- [01 Install & Add a Reference](01_install/) — add `VeloxDev.Core` from NuGet or project-reference it from this repo
- [02 Define Observable Properties](02_define-properties/) — `[VeloxProperty]` field and `partial`-property forms, generated hooks, notification infrastructure
- [03 Define Commands](03_define-commands/) — `[VeloxCommand]` method forms, auto-naming, executability predicates, lazy command properties
- [04 Observe Collection Changes](04_observe-collections/) — `ObservableCollectionTracker` and the generated collection hooks
- [05 Concurrency, Cancellation & Lifecycle](05_concurrency-and-lifecycle/) — queue/semaphore, per-run cancellation, lifecycle events, interrupt/clear/lock
- [06 Verify & Complete Code](06_verify-and-complete-code/) — demos and tests that exercise the feature, the single runnable program, and the run declaration
