# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`) marks a member that the MVVM source generator turns into a change-notifying property supporting `INotifyPropertyChanging` and `INotifyPropertyChanged`.

**Signature**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **Targets:** `Field` or `Property`.
- **Flags:** `AllowMultiple = false`, `Inherited = false`. Not sealed.
- **Notes:** The attribute carries no parameters; every behavior is decided by the generator (`VeloxDev.Generators.MVVM`, see [MVVM](../08_MVVM/index.md)) from the annotated member and its containing class.

## Field form (Demo-verified)

A private backing field is expanded into a public property. The property name is derived by removing a leading `_` and upper-casing the next character (`MVVMFieldAnalizer.GetPropertyNameFromFieldName`, `Base/Analizer.cs`): `_index` → `Index`, `_selectedItem` → `SelectedItem`.

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 25-29:

```csharp
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
```

Because the property is generated, the view-model does not need to inherit a MVVM base class nor declare a notification interface — the generator adds whatever the class does not already provide (events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)` methods, or the two `INotifyPropertyChanged` interfaces).

## `partial` property form (*inferred*)

A `partial` property annotated with `[VeloxProperty]` is completed by the generator (`MVVMWriter.ReadAutoProperties`): it synthesizes a private backing field named `_{<first letter lower-cased>}` and the full getter/setter. No Demo exercises this form; it is *inferred from the generator source*.

## Generated behavior shared by both forms

For each annotated member the generator emits a property whose setter:

1. returns when `Object.Equals(backingField, value)` (no change);
2. raises the changing notification `OnPropertyChanging(string)` (base- or generator-provided);
3. invokes the per-property hook `partial void On{Name}Changing(T oldValue, T newValue)`;
4. assigns the backing field;
5. invokes `partial void On{Name}Changed(T oldValue, T newValue)`;
6. raises the changed notification `OnPropertyChanged(string)`.

When the member type implements `INotifyCollectionChanged` (for example `ObservableCollection<T>`), the getter additionally lazily subscribes through `ObservableCollectionTracker` (see [ObservableCollectionTracker](../07_ObservableCollectionTracker/index.md)) and per-action `partial` hooks are emitted (`OnItemAddedTo{Name}`, `OnItemRemovedFrom{Name}`, `OnItemMovedIn{Name}`, `OnItemsResetIn{Name}`, plus a private `On{Name}CollectionChanged` handler forwarding to `OnCollectionChanged<T>`).

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 34-37 — a per-property change hook reacting to `Index`:

```csharp
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}
```

`MinusCommand` is the command property the Command generator derives from the `[VeloxCommand]`-annotated `Minus` method (see [VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md)).
