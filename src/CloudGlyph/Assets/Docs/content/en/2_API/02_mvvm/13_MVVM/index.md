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

            foreach (var diagnostic in writer.Diagnostics)
            {
                context.ReportDiagnostic(diagnostic);
            }

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

The generator ships in the analyzer package `VeloxDev.Core.Generator` (`netstandard2.0`, `Microsoft.CodeAnalysis.CSharp` 4.8.0), referenced by `VeloxDev.Core`.

##### Methods

| Member | Signature | Description |
| --- | --- | --- |
| `Initialize` | `void Initialize(IncrementalGeneratorInitializationContext context)` | Registers the combined provider. |
| `GenerateSource` | `void GenerateSource(SourceProductionContext, (ImmutableArray<GeneratorTarget>, Compilation))` | Reports diagnostics, resolves each target, and adds one source file when the writer has something to emit. |

## Pipeline

1. **`Analizer.Filters.Targets`** registers one `ForAttributeWithMetadataName` provider per `TriggerAttributes` entry — `VeloxDev.MVVM.VeloxPropertyAttribute` among them — and deduplicates by type key. A `GeneratorTarget` carries no `ISymbol`, so a cached transform cannot hold a stale symbol.
2. **`Analizer.Filters.Resolve`** re-resolves each symbol against the current compilation.
3. **`MVVMWriter.Initialize`** calls `ConfigurePropertyNotificationInfrastructure`, `ReadMVVMConfig` (fields), `ReadAutoProperties` (`partial` properties) and `DetectSetterMode`.
4. **`CanWrite`** is `MVVMProperties.Count > 0 || AutoProperties.Count > 0 || IsWorkflowComponent`.
5. **`GetFileName`** returns `{ClassName}_{Namespace_With_Underscores}_MVVM.g.cs`.

## What it emits

Only members the class does not already provide:

- `PropertyChanging` / `PropertyChanged`, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, and — when nothing supplies them — `INotifyPropertyChanging` / `INotifyPropertyChanged`.
- For each annotated field: a public property with the guarded setter, and the `partial void On{Name}Changing(old, new)` / `On{Name}Changed(old, new)` hooks.
- For each annotated `partial` property: a backing field (unless an accessible conventional field exists) plus the accessors, preserving the declared accessibility.
- For collection-typed members: the getter-side `ObservableCollectionTracker.EnsureSubscribed`, the setter-side `Unsubscribe`, a private `On{Name}CollectionChanged` handler, and `OnItemAddedTo{Name}` / `OnItemRemovedFrom{Name}` / `OnItemMovedIn{Name}` / `OnItemsResetIn{Name}`.
- Workflow-component lifecycle integration when the class belongs to the Workflow system.

## Diagnostics

| Id | Severity | Condition |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | conflicting property declaration (duplicate derived name, or an existing field that cannot back the property) |
| `VELOX_MVVM_PROP002` | Warning | the field name yields no valid identifier |
| `VELOX_MVVM_PROP003` | Warning | the annotated property is not `partial` |
| `VELOX_LANGVERSION001` | Warning | the project's `LangVersion` is below what the generated code needs |

Diagnostics are reported whether or not a file is written, so a refused declaration never disappears silently.

## Host-framework adaptation

`MVVMWriter.DetectSetterMode` inspects the class hierarchy and delegates the generated setter to the host framework's notifier when one is detected:

| Framework | Detection | Delegated call |
| --- | --- | --- |
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | a base with `SetProperty(ref T, T, string)` | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | implements `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | `NotifyOfPropertyChange(string)` present | `NotifyOfPropertyChange(string propertyName)` |

## Example — the emitted file for a real class

```csharp
// Source: generated — {Class}_{Namespace}_MVVM.g.cs
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

    // then: one property plus its partial hooks per [VeloxProperty] member
}
```
