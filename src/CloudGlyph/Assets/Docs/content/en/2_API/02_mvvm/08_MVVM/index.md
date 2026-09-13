# MVVM — MVVM generator

`VeloxDev.Generators.MVVM` is the Roslyn source generator that turns `[VeloxProperty]` members into change-notifying properties. Sources: `Src/Generators/VeloxDev.Core.Generator/MVVM.cs`, `Writers/MVVMWriter.cs`, `Base/Analizer.cs`.

```csharp
[Generator(LanguageNames.CSharp)]
public class MVVM : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(Analizer.Filters.FilterContext(context), GenerateSource);
    }
}
```

The generator ships in the analyzer package `VeloxDev.Core.Generator` (version `9.0.0`, `netstandard2.0`, Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1), referenced transitively by `VeloxDev.Core`.

## Pipeline

1. `Analizer.Filters.FilterContext` collects every `partial` class declaration in the compilation.
2. For each class `MVVMWriter` decides whether anything must be emitted (`CanWrite` is true when the class carries `[VeloxProperty]` fields or `partial` properties, or is a Workflow component).
3. When it writes, it emits one source file per class named `{ClassName}_{Namespace}_MVVM.g.cs` (namespace dots replaced by `_`; `Global` for the global namespace).

## What it emits

For each relevant class the writer generates only the members the class does not already provide:

- The `PropertyChanging` / `PropertyChanged` events, the `OnPropertyChanging(string)` / `OnPropertyChanged(string)` methods, and — when needed — the `INotifyPropertyChanging` / `INotifyPropertyChanged` interfaces, unless a base class or host framework already supplies them.
- For each annotated field: a public property with a guarded setter that raises the notifications and invokes the `partial void On{Name}Changing(old, value)` / `On{Name}Changed(old, value)` hooks.
- For each annotated `partial` property: a backing field plus the full getter/setter.
- For collection-typed members (`INotifyCollectionChanged`): a getter-side lazy subscription through `ObservableCollectionTracker`, a private `On{Name}CollectionChanged` handler forwarding to `OnCollectionChanged<T>`, and the `partial` hooks `OnItemAddedTo{Name}` / `OnItemRemovedFrom{Name}` / `OnItemMovedIn{Name}` / `OnItemsResetIn{Name}`.
- Workflow-component lifecycle integration when the class is part of the Workflow system.

## Host-framework adaptation

`MVVMWriter.DetectSetterMode` inspects the class hierarchy and, instead of raising events itself, delegates the generated setter to the host MVVM framework's native notification API when one is detected:

| Framework | Detection | Delegated call |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | `SetProperty(ref T, T, string)` present | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | implements `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | `NotifyOfPropertyChange(string)` present | `NotifyOfPropertyChange(string propertyName)` |

The user-facing contract is the attribute, documented in [VeloxPropertyAttribute](../00_VeloxPropertyAttribute/index.md).
