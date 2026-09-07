# MVVM — Observe Collection Changes

When a `[VeloxProperty]` member's type implements `INotifyCollectionChanged` (an `ObservableCollection<T>` and most collection view-models), the generator wires `CollectionChanged` to your hooks automatically — both when items change *inside* the collection and when the whole collection instance is *replaced*.

## 1. Declaring a collection property

Same attribute, any `INotifyCollectionChanged` type:

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private ObservableCollection<string> _items = [];

    public CounterViewModel()
    {
        Items.Add("seed");
    }
}
```

**Expected result:** `public ObservableCollection<string> Items` is generated. The constructor can also use the property's object initializer (`Items = [...]`) — see section 3 for why both styles are covered.

## 2. Generated hooks

For a property named `Items` of item type `string`, the generator emits:

```csharp
partial void OnItemsChanging(ObservableCollection<string> oldValue, ObservableCollection<string> newValue);
partial void OnItemsChanged(ObservableCollection<string> oldValue, ObservableCollection<string> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemsResetInItems();
```

The `OnItemsChanging` / `OnItemsChanged` pair fires when the whole collection instance is replaced (through the property setter, like `OnIndexChanged` for a scalar). The four per-item hooks map onto the `NotifyCollectionChangedAction` of the underlying event:

| `NotifyCollectionChangedAction` | Hook raised |
|---|---|
| `Add` | `OnItemAddedToItems(newItems)` |
| `Remove` | `OnItemRemovedFromItems(oldItems)` |
| `Replace` | `OnItemRemovedFromItems(oldItems)` then `OnItemAddedToItems(newItems)` |
| `Move` | `OnItemMovedInItems(newItems)` |
| `Reset` | `OnItemsResetInItems()` |

Implement any of them in your own partial part. The WPF demo (`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`) implements `OnItemAddedToItems`, `OnItemRemovedFromItems`, `OnItemMovedInItems` and `OnItemsResetInItems` for its `Items` collection.

**Expected result:** `Items.Add("x")` calls `OnItemAddedToItems` with the added items; `Items.Clear()` calls `OnItemsResetInItems`; replacing the whole collection instance calls `OnItemsChanged` and then bulk-adds the new contents through `OnItemAddedToItems`.

## 3. An overridable `OnCollectionChanged<T>`

Every collection event also funnels into a single override point. When no base class provides it, the generator emits a `protected virtual void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)`; a base that already declares it is reused (the demos override it in `ObservableViewModelBase`):

```csharp
public partial class CounterViewModel
{
    protected override void OnCollectionChanged<T>(
        string propertyName,
        System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
        System.Collections.Generic.IEnumerable<T>? oldItems,
        System.Collections.Generic.IEnumerable<T>? newItems)
    {
        System.Console.WriteLine($"{propertyName}: {e.Action}");
    }
}
```

**Expected result:** every add/remove/move/replace/reset prints one `OnCollectionChanged<T>` line in addition to the per-item hooks.

## 4. Why subscription is lazy (`ObservableCollectionTracker`)

A field initializer such as `_items = []` assigns the backing field *directly*, bypassing the generated setter — so the setter's subscribe step never runs. `VeloxDev.MVVM.ObservableCollectionTracker` closes this gap: the generated getter calls `ObservableCollectionTracker.EnsureSubscribed(value, OnItemsCollectionChanged)` on every access, which subscribes exactly once (deduplicated by method+target identity) via a `ConditionalWeakTable`. The setter calls `Unsubscribe` on the old instance before replacing it, so no handler leaks and a replaced collection never gets re-subscribed.

**Expected result:** hook methods fire for items added after any getter access, even when the collection was created by a field initializer; repeated getter reads do not add duplicate subscriptions, and the tracker never keeps a collected collection alive.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Hook names and the action mapping come from `MVVMPropertyFactory.GenerateCollectionMembers()` in `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`; tracker semantics come from `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`; the demo hooks come from `Examples/MVVM/*/.../MainWindowViewModel.cs`.
