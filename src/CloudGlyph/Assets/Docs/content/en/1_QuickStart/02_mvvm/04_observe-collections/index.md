# MVVM — Observe Collection Changes

When a `[VeloxProperty]` member's type implements `INotifyCollectionChanged` (an `ObservableCollection<T>`, and most collection view-models), the generator wires `CollectionChanged` to your hooks automatically — both when items change *inside* the collection and when the whole collection instance is *replaced*.

## 1. Declaring a collection property

The attribute is the same; the type is what changes the generated members:

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private ObservableCollection<string> _items = [];

    public CounterViewModel()
    {
        Items.Add("ready");
    }
}
```

**Expected result:** `public ObservableCollection<string> Items` is generated. Both `Items.Add(...)` and `Items = [...]` are observed — section 4 explains why the field initializer alone would otherwise be invisible.

## 2. Generated members

For a property named `Items` with item type `string`, the generator emits this hook surface (verbatim from a real build):

```csharp
partial void OnItemsChanging(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);
partial void OnItemsChanged(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemsResetInItems();
```

`OnItemsChanging` / `OnItemsChanged` fire when the whole collection instance is replaced through the property setter. The four per-item hooks map onto the `NotifyCollectionChangedAction` of the underlying event, dispatched from a generated private `OnItemsCollectionChanged` handler:

| `NotifyCollectionChangedAction` | Hook raised |
|---|---|
| `Add` | `OnItemAddedToItems(e.NewItems)` |
| `Remove` | `OnItemRemovedFromItems(e.OldItems)` |
| `Replace` | `OnItemRemovedFromItems(e.OldItems)`, then `OnItemAddedToItems(e.NewItems)` |
| `Move` | `OnItemMovedInItems(e.NewItems)` |
| `Reset` | `OnItemsResetInItems()` |

Implement any of them in your own partial part. The WPF and Avalonia demos (`Examples/MVVM/*/.../MainWindowViewModel.cs`) implement all four for their `Items` collection.

**Expected result:** `Items.Add("x")` calls `OnItemAddedToItems` with the added items; `Items.Clear()` calls `OnItemsResetInItems`; replacing the whole collection instance calls `OnItemsChanged`, and the new contents are bulk-added through `OnItemAddedToItems` after the old ones are bulk-removed through `OnItemRemovedFromItems`.

## 3. An overridable `OnCollectionChanged<T>`

Every collection event also funnels into one override point, raised *before* the per-action hooks. When no base class provides it, the generator emits this (shown here as generated for a bare `partial class`):

```csharp
protected virtual void OnCollectionChanged<T>(
    string propertyName,
    global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    global::System.Collections.Generic.IEnumerable<T>? oldItems,
    global::System.Collections.Generic.IEnumerable<T>? newItems)
{
}
```

A base that already declares it is reused — the demos override it in their own `ObservableViewModelBase`:

```csharp
protected override void OnCollectionChanged<T>(
    string propertyName,
    System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    System.Collections.Generic.IEnumerable<T>? oldItems,
    System.Collections.Generic.IEnumerable<T>? newItems)
{
    System.Console.WriteLine($"{propertyName}: {e.Action}");
}
```

**Expected result:** every add / remove / move / replace / reset prints one `OnCollectionChanged<T>` line in addition to the per-item hook.

## 4. Why subscription is lazy (`ObservableCollectionTracker`)

A field initializer such as `_items = []` assigns the backing field *directly*, bypassing the generated setter, so a subscribe step living only in the setter would never run for it. `VeloxDev.MVVM.ObservableCollectionTracker` closes that gap:

- the generated **getter** calls `ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged)` on every access, which subscribes exactly once;
- the generated **setter** calls `Unsubscribe(old, OnItemsCollectionChanged)` on the outgoing instance before replacing it, so no handler leaks onto a discarded collection.

The generated getter of the property above is, verbatim:

```csharp
public System.Collections.ObjectModel.ObservableCollection<System.String> Items
{
    get
    {
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
        return this._items;
    }
    set
    {
        if (global::System.Object.Equals(this._items, value)) return;
        var old = this._items;
        OnPropertyChanging(nameof(Items));
        OnItemsChanging(old, value);
        global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);
        this._items = value;
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(value, OnItemsCollectionChanged);
        OnItemsChanged(old, value);
        OnPropertyChanged(nameof(Items));
    }
}
```

De-duplication is by `(Method, Target)` identity, not by delegate reference, because a method group produces a fresh delegate instance on every getter read; comparing by reference would re-subscribe on every read and grow the invocation list without bound. Tracking entries live in a `ConditionalWeakTable`, so a collected collection takes its entry with it.

**Expected result:** hooks fire for items added after any getter access, even when the collection came from a field initializer; repeated getter reads add no duplicate subscriptions; a replaced collection stops raising events for this view-model.

## Run declaration

- ✅ Actually built and run on 2026-10-01. The `Items` property above — including the lazy `= []` initializer and the constructor's `Items.Add("ready")` — was compiled with `dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true` and executed with `dotnet run -c Debug` in a scratch console project referencing `VeloxDev.Core` and the generator. Recorded output, showing the hook firing for a mutation that happened after the field initializer bypassed the setter:

  ```text
  [collection] added: ready
  initial: Count=0, CanExecute(Decrement)=False
  Items: ready
  ```

- The generated property in section 4 and the hook declarations in section 2 are copied verbatim from `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs`. The `Replace` and `Reset` rows of the action table were not separately executed in this pass; they are transcribed from the generated `OnItemsCollectionChanged` switch in that same file.
