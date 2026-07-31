# Complexity Analysis — MVVM

## Generated property setter (default mode)

The generated setter performs a constant number of operations regardless of value type:

$$O(1)$$

Steps: `Object.Equals` guard, capture `old`, `OnPropertyChanging`, `OnXxxChanging`, field assignment, `OnXxxChanged`, `OnPropertyChanged` — all constant time. Setter body source: `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`, `GetSetterBodyLines`, lines 287-307.

For an `INotifyCollectionChanged` property, replacing the collection additionally calls `ObservableCollectionTracker.Unsubscribe(old, ...)` and `EnsureSubscribed(value, ...)` plus `OnItemRemovedFromXxx` / `OnItemAddedToXxx` over the replaced collections' items:

$$O(k) \quad \text{where } k = |\text{old collection}| + |\text{new collection}|$$

*The $O(k)$ replacement cost is inferred from the generated collection setter lines (`GetCollectionBeforeAssignmentLines` / `GetCollectionAfterAssignmentLines`, lines 486-526); the non-replacement getter path is $O(1)$.*

## CollectionChanged handler (per mutation)

The generated `OnXxxCollectionChanged` forwards the raw event to `OnCollectionChanged<T>` ($O(1)$) and, on Add / Remove / Replace / Move, materializes the affected items via `EnumerateXxxItems` → `ToArray`:

$$O(m) \quad \text{for } m \text{ affected items}$$

(`GenerateCollectionMembers`, lines 575-700.)

## ObservableCollectionTracker.EnsureSubscribed

$$O(1) \text{ amortized}$$

`ConditionalWeakTable.GetOrCreateValue` plus a `HashSet<Delegate>` add (`Entry.TryAdd`, reference-identity comparison). The first call per collection subscribes; subsequent calls are a fast identity lookup. Weak-reference keys mean the tracking entry disappears when the collection is garbage-collected — no leaks.

(Source: `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`, lines 15-56.)

## Command execution

Normal execution when capacity is available:

$$O(1) \text{ per trigger, amortized}$$

`ExecuteAsync` does `SemaphoreSlim.WaitAsync` + `_active.Add` + fire-and-forget (VeloxCommand.cs, lines 139-174). When capacity is exhausted the item is enqueued:

$$O(1) \text{ enqueue, } \quad O(n) \text{ worst-case queued}$$

where $n$ is the number of queued items. `TryStartPendingAsync` drains up to `_maxConcurrency` items in $O(n)$ total for the drain (lines 349-377); because the queue is drained by the completing invocation, each trigger costs amortized $O(1)$.

`Notify()` → `RaiseCanExecuteChanged()` is $O(H)$, where $H$ is the number of registered `CanExecuteChanged` handlers (typically one binding).

## Memory usage

| Structure | Complexity |
|---|---|
| Generated members per annotated type | $O(P + C)$ constant per type; $P$ = `[VeloxProperty]` fields, $C$ = `[VeloxCommand]` methods |
| `VeloxCommand` state | $O(n)$ active + queued `CommandEventArgs`, $n$ = in-flight invocations |
| `ObservableCollectionTracker` table | $O(C)$ tracked collections via `ConditionalWeakTable` (collected with the collections) |
| `CommandEventArgs` per execution | $O(1)$ transient |

## Per-operation summary

| Operation | Complexity |
|---|---|
| Property get (non-collection) | $O(1)$ |
| Property set (non-collection) | $O(1)$ |
| Property get (collection) | $O(1)$ amortized (`EnsureSubscribed` idempotent) |
| Property set (collection replacement) | $O(k)$, $k$ = old + new item counts |
| `CollectionChanged` handler | $O(m)$, $m$ = affected items |
| `ExecuteAsync` (capacity free) | $O(1)$ |
| `ExecuteAsync` (queue) | $O(1)$ enqueue, $O(n)$ queued |
| `Notify()` / `CanExecuteChanged` | $O(H)$ handlers |
| `Lock` / `UnLock` / `ChangeSemaphore` | $O(1)$ |
| `Interrupt` / `Clear` | $O(a + q)$ active + queued invocations to cancel |
