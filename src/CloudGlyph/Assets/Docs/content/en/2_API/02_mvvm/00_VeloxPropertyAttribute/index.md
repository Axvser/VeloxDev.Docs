# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`) marks a member that the MVVM source generator turns into a change-notifying property supporting `INotifyPropertyChanging` and `INotifyPropertyChanged`.

## Class: `VeloxPropertyAttribute`

**Signature**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **Base type:** `System.Attribute`. Not `sealed`.
- **Targets:** `Field` or `Property`.
- **Flags:** `AllowMultiple = false`, `Inherited = false`.
- **Constructors:** the implicit parameterless one only.
- **Properties / methods:** none declared — the type is a pure marker.

**Notes:**

- The attribute has no parameters; every behaviour is decided by the generator (`VeloxDev.Generators.MVVM`, documented on the `13_MVVM` page) from the annotated member and its containing class.
- The containing class must be `partial`, and the annotated field must be a field (not a local or a captured variable).

## Emitted members

The generator emits the property and its hooks into a second partial part of the same class. For `[VeloxProperty] private int _count;` the emitted property is exactly:

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if (global::System.Object.Equals(this._count, value)) return;
        var old = this._count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        this._count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}
partial void OnCountChanging(System.Int32 oldValue, System.Int32 newValue);
partial void OnCountChanged(System.Int32 oldValue, System.Int32 newValue);
```

Naming: a leading `_` is dropped and the next character is upper-cased (`_index` → `Index`, `_selectedItem` → `SelectedItem`).

## Generated members by member kind

##### Property: `{Name}`

A public property with the annotated member's type. The setter short-circuits on `Object.Equals`, raises `OnPropertyChanging(nameof({Name}))`, calls `partial On{Name}Changing(old, new)`, assigns, calls `partial On{Name}Changed(old, new)`, then raises `OnPropertyChanged(nameof({Name}))`.

##### Hook: `On{Name}Changing(T oldValue, T newValue)`

`partial void`. Declared by the generator; implemented (or left out) by you. Runs before the assignment.

##### Hook: `On{Name}Changed(T oldValue, T newValue)`

`partial void`. Runs after the assignment.

##### Collection members (`INotifyCollectionChanged` types)

The getter lazily subscribes through `ObservableCollectionTracker.EnsureSubscribed`, and the setter unsubscribes the outgoing instance. Four per-action `partial` hooks and one override point are added on top of the changing/changed pair:

| Member | Signature |
|---|---|
| `On{Name}Changing` / `On{Name}Changed` | `partial void (TCollection oldValue, TCollection newValue)` |
| `OnItemAddedTo{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemRemovedFrom{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemMovedIn{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemsResetIn{Name}` | `partial void ()` |
| `OnCollectionChanged<T>` | `protected virtual void (string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` |

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 25-31
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
[VeloxProperty] private string _collectionStatus = "等待集合通知";
```

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 34-43
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}

partial void OnSelectedItemChanged(string? oldValue, string? newValue)
{
    SelectedItemSummary = newValue is null ? "当前选中: (无)" : $"当前选中: {newValue}";
    RemoveSelectedItemCommand.Notify();
}
```

**Notes:**

- The attribute is not inherited and not repeatable: annotate each member once.
- Because the property is generated, the view-model needs no MVVM base class — the generator adds whatever the class does not already provide (events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, or the two interfaces). It also recognizes CommunityToolkit.Mvvm, Prism, ReactiveUI and Caliburn.Micro bases and delegates to their notifiers instead.
- The `partial`-property form (`[VeloxProperty] public partial string Greeting { get; set; }`) is *inferred from the generator source* for this module's page set; the form used by the WPF/Avalonia demos (fields) is Demo-verified.
