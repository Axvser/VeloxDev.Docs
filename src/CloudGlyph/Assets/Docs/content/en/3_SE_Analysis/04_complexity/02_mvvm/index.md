# Complexity Analysis — MVVM

All bounds refer to the runtime in `Src/Core/VeloxDev.Core/MVVM/{VeloxCommand.cs, ObservableCollectionTracker.cs}` and the generated code templates in `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (the `MVVMPropertyFactory` class emitted by `MVVMWriter`). The source generator itself adds $O(P + C)$ generated members per annotated type at compile time, where $P$ is the number of `[VeloxProperty]` fields/partial properties and $C$ the number of `[VeloxCommand]` methods; none of that work repeats at run time.

## Generated property setter (default mode)

The generated setter performs a constant number of operations regardless of value type:

$$
O(1)
$$

Steps: `Object.Equals` guard, capture `old`, `OnPropertyChanging`, `OnXxxChanging`, field assignment, `OnXxxChanged`, `OnPropertyChanged` — all constant time. Setter body source: `MVVMPropertyFactory.GetSetterBodyLines`, `Base/Analizer.cs`, lines 287-307 (the `SetProperty`/`RaiseAndSetIfChanged`/`NotifyOfPropertyChange` branches at lines 308-365 are likewise $O(1)$).

For an `INotifyCollectionChanged` property, replacing the collection additionally calls `ObservableCollectionTracker.Unsubscribe(old, ...)` and `EnsureSubscribed(value, ...)` plus `OnItemRemovedFromXxx` / `OnItemAddedToXxx` over the replaced collections' items:

$$
O(k) \quad \text{where } k = |\text{old collection}| + |\text{new collection}|
$$

*The $O(k)$ replacement cost is inferred from the generated collection setter lines (`GetCollectionBeforeAssignmentLines` / `GetCollectionAfterAssignmentLines`, lines 486-526); the non-replacement getter path is $O(1)$.*

## Property-change fan-out

Setting one property triggers the partial `OnXxxChanged` hook plus the notification event, which in turn fans out to every subscriber:

$$
O(1) + O(H)
$$

where $H$ is the number of subscribed `PropertyChanged` / `PropertyChanging` handlers (typically one or two WPF/Avalonia bindings). The fan-out is dominated by the subscribers, not by the number of properties.

## CollectionChanged handler (per mutation)

The generated `OnXxxCollectionChanged` forwards the raw event to `OnCollectionChanged<T>` ($O(1)$) and, on Add / Remove / Replace / Move, materializes the affected items via `EnumerateXxxItems` → `ToArray`:

$$
O(m) \quad \text{for } m \text{ affected items}
$$

(`MVVMPropertyFactory.GenerateCollectionMembers`, `Base/Analizer.cs`, lines 575-700.)

## ObservableCollectionTracker.EnsureSubscribed (subscription dedup)

$$
O(1) \text{ amortized}
$$

`ConditionalWeakTable.GetOrCreateValue` plus a `HashSet<Delegate>` add (`Entry.TryAdd`, guarded by a lock). The dedup key is the `(Method, Target)` identity of the handler (`MethodTargetEqualityComparer`, lines 96-114), which makes repeated getter accesses idempotent even though every getter access passes a fresh delegate instance. The first call per collection subscribes; subsequent calls are a fast constant-time lookup. Weak-reference keys mean the tracking entry disappears when the collection is garbage-collected — no leaks.

(Source: `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`, lines 15-115.)

## Command execution

Normal execution when capacity is available:

$$
O(1) \text{ per trigger, amortized}
$$

`ExecuteAsync` does `SemaphoreSlim.WaitAsync` + `_active.Add` + fire-and-forget (`VeloxCommand.cs`, lines 139-174). When capacity is exhausted the item is enqueued:

$$
O(1) \text{ enqueue, } \quad O(n) \text{ worst-case queued}
$$

where $n$ is the number of queued items. `TryStartPendingAsync` drains up to `_maxConcurrency` items in $O(n)$ total for the drain (lines 349-377); because the queue is drained by the completing invocation, each trigger costs amortized $O(1)$. `CanExecute` evaluates the user predicate plus the force-lock flag in $O(1)$ (line 126).

`Notify()` → `RaiseCanExecuteChanged()` is $O(H)$, where $H$ is the number of registered `CanExecuteChanged` handlers (typically one binding).

## Memory usage

| Structure | Complexity |
|---|---|
| Generated members per annotated type | $O(P + C)$ constant per type; $P$ = `[VeloxProperty]` fields, $C$ = `[VeloxCommand]` methods |
| `VeloxCommand` state | $O(n)$ active + queued `CommandEventArgs`, $n$ = in-flight invocations |
| `ObservableCollectionTracker` table | $O(C)$ tracked collections via `ConditionalWeakTable` (collected with the collections — no leak) |
| `CommandEventArgs` per execution | $O(1)$ transient |

## Per-operation summary

| Operation | Complexity |
|---|---|
| Property get (non-collection) | $O(1)$ |
| Property set (non-collection) | $O(1)$ + $O(H)$ subscriber fan-out |
| Property get (collection) | $O(1)$ amortized (`EnsureSubscribed` idempotent) |
| Property set (collection replacement) | $O(k)$, $k$ = old + new item counts |
| `CollectionChanged` handler | $O(m)$, $m$ = affected items |
| `ExecuteAsync` (capacity free) | $O(1)$ |
| `ExecuteAsync` (queue) | $O(1)$ enqueue, $O(n)$ queued, amortized $O(1)$ per trigger |
| `Notify()` / `CanExecuteChanged` | $O(H)$ handlers |
| `Lock` / `UnLock` / `ChangeSemaphore` | $O(1)$ |
| `Interrupt` / `Clear` | $O(a + q)$ active + queued invocations to cancel |
