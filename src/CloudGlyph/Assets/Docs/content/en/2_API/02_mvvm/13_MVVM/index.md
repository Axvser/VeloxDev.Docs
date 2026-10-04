# MVVM — MVVM generator

`VeloxDev.Generators.MVVM` is the Roslyn incremental generator that turns `[VeloxProperty]` members into change-notifying properties. Sources: `Src/Generators/VeloxDev.Core.Generator/MVVM.cs`, `Writers/MVVMWriter.cs`, `Base/Analizer.cs`, `Base/ICodeWriter.cs`, `Writers/WriterBase.cs`.

## Class: `MVVM`

**Signature**

```csharp
[Generator(LanguageNames.CSharp)]
public class MVVM : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(
            Analizer.Filters.Targets(context).Combine(context.CompilationProvider),
            GenerateSource);
    }

    public void GenerateSource(SourceProductionContext context, (ImmutableArray<Analizer.Filters.GeneratorTarget> Targets, Compilation Compilation) input)
    {
        foreach (var (syntax, symbol) in Analizer.Filters.Resolve(input.Targets, input.Compilation))
        {
            var writer = new MVVMWriter();
            writer.Initialize(syntax, symbol);

            if (writer.CanWrite())
            {
                context.AddSource(
                    writer.GetFileName(),
                    SourceText.From(writer.Write(), Encoding.UTF8));
            }
        }
    }
}
```

The generator ships in the analyzer package `VeloxDev.Core.Generator` (`netstandard2.0`, Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1), referenced transitively by `VeloxDev.Core`.

##### Methods

| Member | Signature | Description |
|---|---|---|
| `Initialize` | `void Initialize(IncrementalGeneratorInitializationContext context)` | Registers the combined provider. |
| `GenerateSource` | `void GenerateSource(SourceProductionContext context, (ImmutableArray<GeneratorTarget> Targets, Compilation Compilation) input)` | Resolves each target and, when the writer says it has something to emit, adds one source file. |

## Pipeline

1. **`Analizer.Filters.Targets(context)`** (`Base/Analizer.cs`, line 107) registers one `ForAttributeWithMetadataName` syntax provider per entry in `TriggerAttributes` (line 82) — `VeloxDev.MVVM.VeloxPropertyAttribute` is one of them — and concatenates them into a single deduplicated `ImmutableArray<GeneratorTarget>`. A `GeneratorTarget` deliberately carries *no* `ISymbol`: a transform's output is cached per syntax node, so a captured symbol would go stale. Only classes carrying a trigger attribute reach a writer at all.
2. **`Analizer.Filters.Resolve(targets, compilation)`** (line 142) re-resolves the symbol against the *current* compilation and yields `(ClassDeclarationSyntax, INamedTypeSymbol)` pairs, skipping trees that are no longer part of the compilation.
3. **`MVVMWriter.Initialize`** (`Writers/MVVMWriter.cs`) reads the class: `ConfigurePropertyNotificationInfrastructure` (line 198), `ReadMVVMConfig` (line 91) for `[VeloxProperty]` fields, `ReadAutoProperties` (line 117) for `[VeloxProperty]` partial properties. `DetectSetterMode` (line 42) decides which notification API the generated setters call.
4. **`CanWrite`** (line 845) is `MVVMProperties.Count > 0 || AutoProperties.Count > 0 || IsWorkflowComponent`.
5. **`GetFileName`** (line 847) returns `{ClassName}_{Namespace_With_Underscores}_MVVM.g.cs`.

## What it emits

For each relevant class the writer generates only the members the class does not already provide:

- The `PropertyChanging` / `PropertyChanged` events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, and — when nothing supplies them — the `INotifyPropertyChanging` / `INotifyPropertyChanged` interfaces.
- For each annotated field: a public property with a guarded setter that raises the notifications and invokes the `partial void On{Name}Changing(old, value)` / `On{Name}Changed(old, value)` hooks (`MVVMPropertyFactory.GetSetterBodyLines`, `Base/Analizer.cs` line 466; field naming from `MVVMFieldAnalizer.GetPropertyNameFromFieldName`, line 256).
- For each annotated `partial` property: a backing field plus the full getter/setter.
- For collection-typed members (`INotifyCollectionChanged`): a getter-side lazy subscription through `ObservableCollectionTracker`, a private `On{Name}CollectionChanged` handler forwarding to `OnCollectionChanged<T>`, and the `partial` hooks `OnItemAddedTo{Name}` / `OnItemRemovedFrom{Name}` / `OnItemMovedIn{Name}` / `OnItemsResetIn{Name}` (`MVVMPropertyFactory.GenerateCollectionMembers`, line 754).
- Workflow-component lifecycle integration when the class is part of the Workflow system.

Both generators consume the **same** `Filters.Targets` provider, so the MVVM generator also sees classes that carry only `[VeloxCommand]` — it simply has nothing to write for them, and `CanWrite` returns `false`.

## Host-framework adaptation

`MVVMWriter.DetectSetterMode` inspects the class hierarchy and, instead of raising events itself, delegates the generated setter to the host MVVM framework's native notification API when one is detected:

| Framework | Detection | Delegated call |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | `SetProperty(ref T, T, string)` present | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | implements `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | `NotifyOfPropertyChange(string)` present | `NotifyOfPropertyChange(string propertyName)` |

The user-facing contract is the attribute, documented on the `00_VeloxPropertyAttribute` page.

## Example — the emitted file for a real class

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs
namespace QuickStart.Mvvm;

public partial class CounterViewModel : global::System.ComponentModel.INotifyPropertyChanging, global::System.ComponentModel.INotifyPropertyChanged
{
public event global::System.ComponentModel.PropertyChangingEventHandler? PropertyChanging;
public event global::System.ComponentModel.PropertyChangedEventHandler? PropertyChanged;
public virtual void OnPropertyChanging(string propertyName)
{
    PropertyChanging?.Invoke(this, new global::System.ComponentModel.PropertyChangingEventArgs(propertyName));
}
public virtual void OnPropertyChanged(string propertyName)
{
    PropertyChanged?.Invoke(this, new global::System.ComponentModel.PropertyChangedEventArgs(propertyName));
}
    protected virtual void OnCollectionChanged<T>(string propertyName, global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e, global::System.Collections.Generic.IEnumerable<T>? oldItems, global::System.Collections.Generic.IEnumerable<T>? newItems)
    {
    }
    // then: one property plus its partial hooks per [VeloxProperty] member
}
```
