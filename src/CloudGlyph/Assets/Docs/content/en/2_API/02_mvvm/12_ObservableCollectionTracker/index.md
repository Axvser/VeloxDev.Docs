# MVVM — `ObservableCollectionTracker`

`VeloxDev.MVVM.ObservableCollectionTracker` (`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`) is a `static` helper called by generated code so that `INotifyCollectionChanged.CollectionChanged` subscriptions exist even when a collection property's backing field is initialized directly (e.g. `= []`), bypassing the generated setter.

## Class: `ObservableCollectionTracker`

**Signature**

```csharp
public static class ObservableCollectionTracker
{
    public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler);
    public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler);
}
```

`NotifyCollectionChangedEventHandler` is `System.Collections.Specialized.NotifyCollectionChangedEventHandler`.

##### Methods

###### `ObservableCollectionTracker.EnsureSubscribed`

**Signature:**
`void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)`

| Parameter | Type | Description |
|---|---|---|
| `collection` | `object?` | The collection to observe. A `null` value, or one that is not `INotifyCollectionChanged`, is ignored. |
| `handler` | `NotifyCollectionChangedEventHandler` | The handler to attach. Attaching the same `(Method, Target)` twice is a no-op. |

**Returns:** `void`.

**Exceptions:** none. A non-notifying `collection` is a no-op rather than an error.

**Example:**

```csharp
// Source: Generated — the getter of a [VeloxProperty] collection member
public ObservableCollection<string> Items
{
    get
    {
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
        return this._items;
    }
}
```

**Notes:**

- Called from the generated property **getter** on every access; subsequent calls are a fast O(1) lookup.
- The dedup key is `(Method, Target)` identity, not delegate reference identity. The generated getters pass a method group (`OnItemsCollectionChanged`), which produces a *fresh* delegate instance on every access; comparing by reference would re-subscribe every read and grow the event's invocation list without bound.
- Tracking lives in a `ConditionalWeakTable<object, Entry>` keyed by collection identity: when the collection is garbage-collected, its entry goes with it — no leak. The table is safe for concurrent getter/setter access.

###### `ObservableCollectionTracker.Unsubscribe`

**Signature:**
`void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)`

| Parameter | Type | Description |
|---|---|---|
| `collection` | `object?` | The collection to detach from. A `null` value, or one that is not `INotifyCollectionChanged`, is ignored. |
| `handler` | `NotifyCollectionChangedEventHandler` | The handler to detach. |

**Returns:** `void`.

**Exceptions:** none.

**Notes:**

- Called from the generated property **setter** when a collection is replaced (`global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);`).
- This removes the **subscription**, not the record of it: the entry survives, so a later `EnsureSubscribed` with the same handler subscribes to that collection again. That is the behaviour the generated getter depends on, since it calls `EnsureSubscribed` on every read.

## Why it exists

A member such as

```csharp
[VeloxProperty] private ObservableCollection<string> _items = [];
```

assigns its backing field through the initializer `= []`, which bypasses the generated setter. If subscription happened only in the setter, `CollectionChanged` would never be observed. The generated getter calls `EnsureSubscribed` instead, so the first read subscribes the private `On{Property}CollectionChanged` handler.

## Behaviour pinned by tests

`Src/Core/VeloxDev.Core.Test/MVVM/ObservableCollectionTrackerTests.cs`:

| Test | Contract |
|---|---|
| `EnsureSubscribed_WithAFreshMethodGroupDelegate_SubscribesOnlyOnce` | fresh delegate, same method + target → one subscription |
| `EnsureSubscribed_ReportsEachChangeExactlyOnce` | one mutation → one callback |
| `Unsubscribe_DetachesTheHandler` | detached handler stops receiving |
| `Unsubscribe_ThenEnsureSubscribed_SubscribesAgain` | the entry survives, so re-subscribing works |
| `EnsureSubscribed_TreatsDistinctTargetsAsDistinctHandlers` | same method on a different instance is a different handler |
| `EnsureSubscribed_OnSomethingThatCannotNotify_IsANoOp` | non-`INotifyCollectionChanged` collection |
| `Unsubscribe_OnACollectionNeverSubscribed_IsANoOp` | detaching an unknown handler |
| `ConcurrentEnsureSubscribed_SubscribesOnce` | concurrent getter access still subscribes once |
