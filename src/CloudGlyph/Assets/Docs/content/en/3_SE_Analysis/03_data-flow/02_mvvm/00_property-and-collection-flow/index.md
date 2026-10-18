# Data Flow — Property and Collection

The scalar-property path and the collection path share a shape: the generator emits a skeleton at compile time, and the setter drives it at run time. The collection path adds a lazy subscription so that a field initializer (`= []`) cannot leave `CollectionChanged` unobserved.

## (a) Generator output → INPC flow

```plantuml
@startuml
!theme plain

participant "Source generator\nVeloxDev.Generators.MVVM" as Gen
participant "MVVM partial\nCounterViewModel_..._MVVM.g.cs" as GVM
participant "Command body\n(Increment method)" as Body
participant "Binding\nWPF / Avalonia" as Bind

== compile time: generator output ==
Gen -> GVM: MVVMWriter emits Count property; OnPropertyChanging /\nOnPropertyChanged methods; OnCountChanging / OnCountChanged partials
note right of GVM: merged with the hand-written partial into one type

== runtime: generated setter drives INPC ==
Body -> GVM: Count = newValue
activate GVM
GVM -> GVM: equality guard (returns early if unchanged)
GVM -> GVM: OnPropertyChanging(nameof(Count)) -> PropertyChanging
GVM -> GVM: OnCountChanging(old, value) (user partial hook)
GVM -> GVM: assign the backing field this._count
GVM -> GVM: OnCountChanged(old, value) (user partial hook)
GVM -> Bind: OnPropertyChanged(nameof(Count)) fires PropertyChanged
Bind -> Bind: re-reads Count, refreshes the bound control
GVM --> Body
deactivate GVM
@enduml
```

> Source: the setter shape is emitted by `MVVMPropertyFactory.GetSetterBodyLines` (`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`).

```csharp
// Source: Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs (Default setter mode)
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
```

## (b) Collection flow: initializer → getter subscription → per-action hooks

The interesting step is the first `Items.Add("ready")` in the constructor. The field initializer assigned `this._items` directly, so the setter never ran; the subscription exists only because the **getter** was read on the way to `Add`.

```plantuml
@startuml
!theme plain

participant "Constructor" as Ctor
participant "Generated getter\nItems" as Getter
participant "ObservableCollectionTracker" as Tracker
participant "ObservableCollection\n<string>" as Coll
participant "Generated handler\nOnItemsCollectionChanged" as Handler
participant "User hooks\nOnItemAddedToItems" as Hooks

Ctor -> Getter: Items.Add("ready")
activate Getter
Getter -> Tracker: EnsureSubscribed(this._items, OnItemsCollectionChanged)
activate Tracker
Tracker -> Tracker: ConditionalWeakTable.GetOrCreateValue(collection)
Tracker -> Tracker: Entry.TryAdd(handler) -> dedupe by (Method, Target)
Tracker -> Coll: CollectionChanged += handler
Tracker --> Getter
deactivate Tracker
Getter --> Ctor: this._items
deactivate Getter

Ctor -> Coll: Add("ready")
activate Coll
Coll -> Handler: CollectionChanged(sender, e) [Action = Add]
activate Handler
Handler -> Handler: OnCollectionChanged(nameof(Items), e, oldItems, newItems)
Handler -> Hooks: OnItemAddedToItems(enumerated NewItems)
Hooks --> Handler
Handler --> Coll
deactivate Handler
Coll --> Ctor
deactivate Coll
@enduml
```

> Source: `MVVMPropertyFactory.GenerateCollectionMembers` (`Base/Analizer.cs`); tracker behaviour — `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`.

```csharp
// Source: Base/Analizer.cs — the generated collection getter
get
{
    global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
    return this._items;
}
```

## (c) Replacing the whole collection

Replacement is where `Unsubscribe` matters: without it the discarded collection would keep a handler pointing back into this view-model.

```plantuml
@startuml
!theme plain

participant "Code" as Code
participant "Generated setter\nItems" as Setter
participant "ObservableCollectionTracker" as Tracker
participant "Old collection" as Old
participant "New collection" as New
participant "User hooks" as Hooks

Code -> Setter: Items = newList
activate Setter
Setter -> Setter: Object.Equals(this._items, value) guard
Setter -> Setter: OnPropertyChanging(nameof(Items))
Setter -> Setter: OnItemsChanging(old, value)
Setter -> Tracker: Unsubscribe(old, OnItemsCollectionChanged)
activate Tracker
Tracker -> Old: CollectionChanged -= handler
Tracker -> Tracker: Entry.Remove(handler) (the record survives)
Tracker --> Setter
deactivate Tracker
Setter -> Hooks: OnItemRemovedFromItems(enumerate old)
Setter -> Setter: this._items = value
Setter -> Tracker: EnsureSubscribed(value, OnItemsCollectionChanged)
activate Tracker
Tracker -> New: CollectionChanged += handler
Tracker --> Setter
deactivate Tracker
Setter -> Hooks: OnItemAddedToItems(enumerate new)
Setter -> Setter: OnItemsChanged(old, value)
Setter -> Setter: OnPropertyChanged(nameof(Items))
Setter --> Code
deactivate Setter
@enduml
```

> Source: `MVVMPropertyFactory.GetSetterBodyLines` and `GenerateCollectionMembers` (`Base/Analizer.cs`); `Unsubscribe` — `ObservableCollectionTracker.cs`.

## Per-action dispatch

The generated `OnItemsCollectionChanged` calls `OnCollectionChanged<T>` first, then maps `NotifyCollectionChangedAction` onto the user hooks:

```csharp
// Source: Base/Analizer.cs — GenerateCollectionMembers
var oldItems = e.OldItems is null ? null : EnumerateItemsItems(e.OldItems);
var newItems = e.NewItems is null ? null : EnumerateItemsItems(e.NewItems);
OnCollectionChanged(nameof(Items), e, oldItems, newItems);
switch (e.Action)
{
    case NotifyCollectionChangedAction.Add when e.NewItems is not null:
        OnItemAddedToItems(EnumerateItemsItems(e.NewItems));
        break;
    case NotifyCollectionChangedAction.Remove when e.OldItems is not null:
        OnItemRemovedFromItems(EnumerateItemsItems(e.OldItems));
        break;
    case NotifyCollectionChangedAction.Replace:
        if (e.OldItems is not null)
        {
            OnItemRemovedFromItems(EnumerateItemsItems(e.OldItems));
        }
        if (e.NewItems is not null)
        {
            OnItemAddedToItems(EnumerateItemsItems(e.NewItems));
        }
        break;
    case NotifyCollectionChangedAction.Move when e.NewItems is not null:
        OnItemMovedInItems(EnumerateItemsItems(e.NewItems));
        break;
    case NotifyCollectionChangedAction.Reset:
        OnItemsResetInItems();
        break;
}
```

## Error and edge paths

| Path | Behaviour |
| --- | --- |
| Value unchanged | The equality guard returns before any notification or hook. |
| Collection is not `INotifyCollectionChanged` | `EnsureSubscribed` / `Unsubscribe` return immediately. |
| `null` collection | Same early return; no exception. |
| Handler arrives as a fresh method-group delegate | Deduped by `(Method, Target)`, so the invocation list does not grow. |
| Collection garbage-collected | Its `ConditionalWeakTable` entry goes with it — no leak. |
| Handler throws | Collection handlers are plain .NET event subscribers and are not guarded by the tracker. |
