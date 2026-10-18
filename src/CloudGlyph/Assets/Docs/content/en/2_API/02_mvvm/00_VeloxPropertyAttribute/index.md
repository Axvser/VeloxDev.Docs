# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`) marks a member that the MVVM source generator turns into a change-notifying property.

## Class: `VeloxPropertyAttribute`

**Signature**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **Base type:** `System.Attribute`. **Not sealed.**
- **Targets:** `Field` or `Property`. `AllowMultiple = false`, `Inherited = false`.
- **Constructors:** the implicit parameterless one only.
- **Members:** none — the type is a pure marker.

**Notes:** every behaviour is decided by `VeloxDev.Generators.MVVM` from the annotated member and its containing class. The containing type must be `partial`; the annotated field must be a field, and the annotated property must be a C# 13 `partial` property.

## Emitted members

For `[VeloxProperty] private int _count;`:

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if(global::System.Object.Equals(this._count, value)) return;
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

Naming: a leading `_` is dropped and the next character is upper-cased (`_index` → `Index`, `_selectedItem` → `SelectedItem`). A name that yields no valid identifier reports `VELOX_MVVM_PROP002`.

##### Property: `{Name}`

A public property with the annotated member's type. The setter short-circuits on `Object.Equals` (floating-point types compare bit patterns instead, so `-0.0` and `NaN` are preserved), raises `OnPropertyChanging(nameof({Name}))`, calls `partial On{Name}Changing(old, new)`, assigns, calls `partial On{Name}Changed(old, new)`, then raises `OnPropertyChanged(nameof({Name}))`.

For the `partial`-property form the generator preserves the access modifiers and accessor visibility you declared, and emits a backing field named `_{camelCaseName}` unless an accessible field of that name already exists.

##### Hook: `On{Name}Changing(T oldValue, T newValue)`

`partial void`. Declared by the generator; implemented (or left out) by you. Runs before the assignment.

##### Hook: `On{Name}Changed(T oldValue, T newValue)`

`partial void`. Runs after the assignment.

##### Collection members (`INotifyCollectionChanged` types)

The getter lazily subscribes through `ObservableCollectionTracker.EnsureSubscribed`; the setter unsubscribes the outgoing instance, calls `OnItemRemovedFrom{Name}` for the old items, assigns, then calls `OnItemAddedTo{Name}` for the new items.

| Member | Signature |
| --- | --- |
| `OnItemAddedTo{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemRemovedFrom{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemMovedIn{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemsResetIn{Name}` | `partial void ()` |
| `OnCollectionChanged<T>` | `protected virtual void (string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` |

When the collection's item type cannot be determined, the hooks take the non-generic `IEnumerable` instead.

## Diagnostics

| Id | Severity | Condition |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | two members map to the same property name, or an existing field cannot back the property |
| `VELOX_MVVM_PROP002` | Warning | the field name yields no valid identifier |
| `VELOX_MVVM_PROP003` | Warning | the annotated property is not `partial` |

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 28-34
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
[VeloxProperty] private string _collectionStatus = "等待集合通知";
[VeloxProperty] private string _collectionTrace = "OnCollectionChanged<T> 尚未触发";
```

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 37-51
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify();
}

partial void OnSelectedItemChanged(string? oldValue, string? newValue)
{
    SelectedItemSummary = newValue is null ? "当前选中: (无)" : $"当前选中: {newValue}";
    RemoveSelectedItemCommand.Notify();
}
```

**Notes:**

- The attribute is not inherited and not repeatable.
- No MVVM base class is required. The generator adds whatever the class does not already provide: events, `OnPropertyChanging(string)` / `OnPropertyChanged(string)`, or the two interfaces. It also recognizes CommunityToolkit.Mvvm, Prism, ReactiveUI and Caliburn.Micro bases and delegates to their notifiers.
- The demos use the field form; the `partial`-property form is implemented by the same writer (`ReadAutoProperties`) and exercised by `McpServerConfiguration.cs`, not by the MVVM demos.
