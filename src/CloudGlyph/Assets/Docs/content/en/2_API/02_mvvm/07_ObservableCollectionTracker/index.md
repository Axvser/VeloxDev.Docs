# MVVM — `ObservableCollectionTracker`

Weak-reference subscription helper so `CollectionChanged` stays subscribed even when the backing field is initialized directly (`= []`), bypassing the generated setter.

**Signatures** (`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`, lines 15-56):

```csharp
public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)
public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)
```

- **Notes:** Uses a `ConditionalWeakTable<object, Entry>` keyed by collection identity, so entries vanish when the collection is collected — no leak. Handlers are deduplicated by `(Method, Target)` identity (`MethodTargetEqualityComparer`, lines 96-114), not by delegate reference: generated getters pass a method group (e.g. `OnItemsCollectionChanged`), which produces a fresh delegate instance on every access; comparing by reference would re-subscribe on every getter access and grow the invocation list without bound. The generated getter calls `EnsureSubscribed` on every access but only truly subscribes once (`Base/Analizer.cs`, `GenerateGetter`, lines 444-464).
- **Example:** the demo's `[VeloxProperty] private ObservableCollection<string> _items = [];` (`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, line 30) relies on the getter-side `EnsureSubscribed` call because the initializer assigns the field directly.

## Namespace `VeloxDev.Generators`

Source-generator internals (assembly `VeloxDev.Core.Generator`, package version `7.0.0`, target `netstandard2.0`, Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1).

| Item | Detail |
|---|---|
| Package | `VeloxDev.Core.Generator` `7.0.0`, referenced transitively by `VeloxDev.Core` |
| Assembly namespace | `VeloxDev.Generators` |
| MVVM generator | `VeloxDev.Generators.MVVM : IIncrementalGenerator` (`MVVM.cs`, lines 12-13) |
| Command generator | `VeloxDev.Generators.Command : IIncrementalGenerator` (`Command.cs`, lines 12-13) |
| Class filter | `Analizer.Filters.FilterContext` — only `partial` class declarations (`Base/Analizer.cs`, lines 13-24) |
| Property writer | `Writers/MVVMWriter.cs` + `Base/Analizer.cs` (`MVVMPropertyFactory`, lines 208-729) |
| Command writer | `Writers/CommandWriter.cs` |
| MVVM output name | `{ClassName}_{Namespace}_MVVM.g.cs` (namespace dots replaced with `_`; `Global` when in the global namespace) — `MVVMWriter.cs`, lines 847-854 |
| Command output name | `{ClassName}_{Namespace}_Commands.g.cs` — `CommandWriter.cs`, lines 121-130 |
