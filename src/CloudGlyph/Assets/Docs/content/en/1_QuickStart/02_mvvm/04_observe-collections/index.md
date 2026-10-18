# MVVM — Observe Collection Changes

When a `[VeloxProperty]` member's type implements `INotifyCollectionChanged` (for example `ObservableCollection<T>`), the generator subscribes it automatically — both when items change inside the collection and when the whole instance is replaced.

## 1. Declaring a collection property

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

**Expected result:** `public ObservableCollection<string> Items` is generated, and `Items.Add("ready")` is observed even though the field initializer bypassed the setter.

## 2. Generated hook surface

For a property named `Items` with item type `string`:

```csharp
partial void OnItemsChanging(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);
partial void OnItemsChanged(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemsResetInItems();
```

The first pair fires when the whole instance is replaced through the setter. The four per-item hooks are dispatched from the generated `OnItemsCollectionChanged` handler:

| `NotifyCollectionChangedAction` | Hooks raised |
| --- | --- |
| `Add` | `OnItemAddedToItems(e.NewItems)` |
| `Remove` | `OnItemRemovedFromItems(e.OldItems)` |
| `Replace` | `OnItemRemovedFromItems(e.OldItems)`, then `OnItemAddedToItems(e.NewItems)` |
| `Move` | `OnItemMovedInItems(e.NewItems)` |
| `Reset` | `OnItemsResetInItems()` |

**Expected result:** `Items.Add("x")` reaches `OnItemAddedToItems`; `Items.Clear()` reaches `OnItemsResetInItems`; replacing the whole instance calls `OnItemsChanging` / `OnItemsChanged` and reports the old items as removed and the new ones as added.

## 3. The `OnCollectionChanged<T>` override point

Every collection event first funnels into one override point. When no base class provides it, the generator emits:

```csharp
protected virtual void OnCollectionChanged<T>(
    string propertyName,
    global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    global::System.Collections.Generic.IEnumerable<T>? oldItems,
    global::System.Collections.Generic.IEnumerable<T>? newItems)
{
}
```

A base that already declares it is reused. The demos' `ObservableViewModelBase` declares it `protected virtual`, and `MainWindowViewModel` overrides it to write a trace line.

**Expected result:** every add / remove / move / replace / reset calls `OnCollectionChanged<T>` before the per-action hook.

## 4. Why subscription is lazy

A field initializer such as `_items = []` assigns the backing field directly, so a subscription that lived only in the setter would never run. The generated getter closes that gap:

```csharp
global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
```

and the setter detaches the outgoing instance before replacing it:

```csharp
global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);
```

Deduplication is by `(Method, Target)` identity, not delegate reference, because a method group produces a fresh delegate on every getter read. Each collection's entries live in a `ConditionalWeakTable`, so a collected collection takes its tracking entry with it.

**Expected result:** repeated getter reads add no duplicate subscriptions; a replaced collection stops raising events for this view-model; a non-`INotifyCollectionChanged` value is silently ignored.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `Base/Analizer.cs` (`MVVMPropertyFactory.GenerateCollectionMembers`), `MVVM/ObservableCollectionTracker.cs` and `Examples/MVVM/WPF/Demo/{MainWindowViewModel.cs, ObservableViewModelBase.cs}`.
