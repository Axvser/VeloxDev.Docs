# Complexity Analysis — MVVM

All bounds refer to the runtime in `Src/Core/VeloxDev.Core/MVVM/{VeloxCommand.cs, CommandCompletion.cs, ObservableCollectionTracker.cs}` and to the generated code templates in `Src/Generators/VeloxDev.Core.Generator/{Base/Analizer.cs, Writers/CommandWriter.cs}`. The source generator itself adds $O(P + C)$ generated members per annotated type at compile time, where $P$ is the number of `[VeloxProperty]` fields/partial properties and $C$ the number of `[VeloxCommand]` methods; none of that work repeats at run time.

**Notation.** $n$ = in-flight executions (active + queued), $k$ = items in an old + new collection during a replacement, $m$ = items affected by one `CollectionChanged`, $H$ = subscribers of one event, $R$ = emitters that would like to report `Canceled` for one execution.

## Generated property setter (default mode)

The generated setter performs a constant number of operations regardless of the value's type:

$$
T_{\text{set}}(scalar) = O(1)
$$

The steps are the `Object.Equals` guard, capturing `old`, `OnPropertyChanging`, `On{Name}Changing`, the field assignment, `On{Name}Changed` and `OnPropertyChanged` — all constant time. The setter body is emitted by `MVVMPropertyFactory.GetSetterBodyLines` (`Base/Analizer.cs`, line 466) and confirmed in the generated file:

```csharp
// Source: Generated — CounterViewModel_QuickStart_Mvvm_MVVM.g.cs, the Count property
if (global::System.Object.Equals(this._count, value)) return;
var old = this._count;
OnPropertyChanging(nameof(Count));
OnCountChanging(old, value);
this._count = value;
OnCountChanged(old, value);
OnPropertyChanged(nameof(Count));
```

For an `INotifyCollectionChanged` property, replacing the collection additionally calls `Unsubscribe(old, …)` and `EnsureSubscribed(value, …)` plus `OnItemRemovedFrom{Name}` / `OnItemAddedTo{Name}` over the replaced collections' items:

$$
T_{\text{set}}(collection\ replacement) = O(k), \qquad k = |\text{old}| + |\text{new}|
$$

The non-replacement getter path stays constant, plus the amortized tracker lookup:

$$
T_{\text{get}}(collection) = O(1)\ \text{amortized}
$$

## Property-change fan-out

Setting one property triggers the partial hook plus the notification event, which fans out to every subscriber:

$$
T_{\text{notify}}(scalar) = O(1) + O(H)
$$

where $H$ is the number of subscribed `PropertyChanged` / `PropertyChanging` handlers (typically one or two bindings). The fan-out is dominated by subscribers, not by the number of properties.

## CollectionChanged handler (per mutation)

The generated `On{Name}CollectionChanged` forwards the raw event to `OnCollectionChanged<T>` in constant time and, on Add / Remove / Replace / Move, materializes the affected items through `Enumerate{Name}Items` → `ToArray`:

$$
T_{\text{mutation}} = O(m)
$$

for $m$ affected items (`MVVMPropertyFactory.GenerateCollectionMembers`, `Base/Analizer.cs`, line 754). A `Reset` is $O(1)$: it carries no items and dispatches to `OnItemsResetIn{Name}`.

## `ObservableCollectionTracker`

$$
\text{EnsureSubscribed} = O(1)\ \text{amortized}, \qquad \text{Unsubscribe} = O(1)
$$

`ConditionalWeakTable.GetOrCreateValue` plus a `HashSet<Delegate>` add (`Entry.TryAdd`, guarded by a lock). The dedup key is the `(Method, Target)` pair of the handler (`MethodTargetEqualityComparer`, `ObservableCollectionTracker.cs` lines 100-118), which is what makes repeated getter accesses idempotent:

$$
q \text{ getter reads} \;\Rightarrow\; 1 \text{ subscription}
$$

The subtlety worth naming: without `(Method, Target)` dedup the *time* of the reads would still be $O(q)$, but the event's invocation list would grow by one delegate per read, so a single later mutation would cost $O(q)$ instead of $O(1)$. The comparer is what keeps that from happening.

Weak-reference keys mean the tracking entry disappears when the collection is garbage-collected — no leak, so the table's size is bounded by the live collections, not by the ones ever seen.

## Command execution

Normal execution with capacity available:

$$
T_{\text{execute}} = O(1)
$$

`ExecuteCore` does one `SemaphoreSlim.WaitAsync` + `_active.Add` + fire-and-forget (`VeloxCommand.cs`, lines 474-531). When capacity is exhausted the item is enqueued:

$$
T_{\text{enqueue}} = O(1), \qquad \text{queue depth} \le n
$$

`TryStartPendingAsync` (lines 794-822) drains up to `_maxConcurrency` items at once:

$$
T_{\text{drain}} = O(n)\ \text{for the drain}, \qquad O(1)\ \text{amortized per trigger}
$$

`CanExecute` evaluates the user predicate plus the force-lock flag in $O(1)$ (lines 407-408), and `Notify()` → `RaiseCanExecuteChanged()` is $O(H)$ in the number of `CanExecuteChanged` subscribers.

`EventContext` changes the constant, not the complexity: with a context set, each event costs one `SynchronizationContext.Post` — $O(1)$ — but the handler now runs on the context's thread at its own time.

## Cancellation, clearing and disposal

$$
T_{\text{interrupt}} = O(a), \qquad T_{\text{clear}} = O(a + q)
$$

where $a$ = active and $q$ = queued executions swept (`InterruptAsync` lines 642-683, `ClearAsync` lines 686-747). Both are linear in the number of affected items because each needs a `Cancel()` and one event.

Per-execution resource handling is $O(1)$: one `CancellationTokenSource` is created when `_isCtsNeeded`, and disposed exactly once — by `ExecuteCoreAsync`'s `finally` for anything that ran (lines 569-578), or by `ClearAsync` itself for a pending item that never ran (lines 715-723). `TakeCts` (line 888) is `Interlocked.Exchange`, $O(1)$, so two racers cannot both claim disposal.

## The awaitable path

$$
T_{\text{executeAndWait}} = T_{\text{execute}} + O(1)
$$

`ExecuteAndWaitAsync` (lines 452-471) adds, over `ExecuteAsync`, one `TaskCompletionSource<CommandCompletion>` and one token registration. Completing the sink is $O(1)$ via `TrySetResult` / `TrySetCanceled`, and `RunContinuationsAsynchronously` keeps the continuation off the pipeline's stack.

The single-`Canceled` guarantee is $O(1)$:

$$
\text{reports per execution} = \min(R,\ 1) = 1
$$

`TryMarkCancelReported` is a single `Interlocked.Exchange` (line 896), so however many emitters want to report a cancellation — `Interrupt`, `Clear`, the body's own `OperationCanceledException` — exactly the first succeeds.

## Memory usage

| Structure | Complexity |
|---|---|
| Generated members per annotated type | $O(P + C)$, constant per type; $P$ = `[VeloxProperty]` members, $C$ = `[VeloxCommand]` methods |
| `VeloxCommand` state | $O(n)$ `CommandEventArgs` across `_active` (a `HashSet`, line 198) + `_pendingQueue` (a `Queue`, line 196) |
| Per execution, subscribed stages | $O(1)$ `CommandEventArgs` **per stage with a subscriber**; a stage with no subscriber allocates nothing (`RaiseCommandEventAs`, lines 373-393) |
| Per execution, awaiting call | $O(1)$: one `TaskCompletionSource` |
| Per cancellable execution | $O(1)$: one `CancellationTokenSource`, disposed at the end of that execution |
| `ObservableCollectionTracker` table | $O(\text{live collections})$, via `ConditionalWeakTable` — collected with the collections |
| `CommandCompletion` | a `readonly struct`: $0$ allocations of its own |

The per-subscriber allocation rule is worth stating as a bound of its own, because it is the one the code was explicitly shaped around:

$$
\text{alloc} = O\bigl(|\{\text{stages with at least one subscriber}\}|\bigr)
$$

`CommandAllocationTests` pins it relatively — a command with no subscribers must allocate strictly less per execution than one with all eight events subscribed — rather than against an absolute figure, so the assertion does not go stale when the runtime changes shape.

## Per-operation summary

| Operation | Complexity |
|---|---|
| Property get (non-collection) | $O(1)$ |
| Property get (collection) | $O(1)$ amortized (`EnsureSubscribed` idempotent) |
| Property set (non-collection) | $O(1) + O(H)$ subscriber fan-out |
| Property set (collection replacement) | $O(k)$, $k$ = old + new item counts |
| `CollectionChanged` handler | $O(m)$, $m$ = affected items ($O(1)$ on `Reset`) |
| `ObservableCollectionTracker.EnsureSubscribed` | $O(1)$ amortized |
| `ObservableCollectionTracker.Unsubscribe` | $O(1)$ |
| `CanExecute` | $O(1)$ |
| `Execute` / `ExecuteAsync` (capacity free) | $O(1)$ |
| `ExecuteAsync` (queue) | $O(1)$ enqueue; $O(1)$ amortized per trigger when drained |
| `ExecuteAndWaitAsync` | as `ExecuteAsync` $+ O(1)$ |
| `IsBusy` / `ActiveCount` / `PendingCount` | $O(1)$ — two `Count` reads, no lock taken (lines 269-283) |
| `ExecuteAndWaitAsync` / `IsBusy` extension lookup | $O(1)$: one `as` cast, or a `NotSupportedException` |
| `Notify()` / `CanExecuteChanged` | $O(H)$ handlers |
| `Lock` / `Unlock` / `Continue` | $O(1)$, plus a drain when the queue is non-empty |
| `ChangeSemaphore` | $O(1) + O(n)$ drain |
| `Interrupt` | $O(a)$ |
| `Clear` | $O(a + q)$ |
| `Dispose` | $O(1)$ |

## Caveats on these bounds

- All of them are the **steady-state** cost. The generator's own work is compile-time and does not appear at run time at all.
- $H$, $n$, $a$, $q$, $k$ and $m$ are unbounded from the library's point of view: a caller can subscribe arbitrarily many handlers or enqueue arbitrarily many calls. The bounds are exact in these parameters, not in a fixed constant.
- The `EventContext` path trades ordering guarantees for thread affinity rather than for time: complexity is unchanged, but events are posted asynchronously, so a handler can observe the command after the call that raised the event has returned.
- `IsBusy` / `ActiveCount` / `PendingCount` are deliberately **not** synchronized with the state lock, so a concurrent update may leave them one step stale. Reading them is therefore $O(1)$ but not linearizable — a deliberate trade recorded at lines 265-268.

> Source references: `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` (`ExecuteCore` 474, `ExecuteCoreAsync` 533, `TryStartPendingAsync` 794, `InterruptAsync` 642, `ClearAsync` 686, `ExecuteAndWaitAsync` 452, `CanExecute` 407, `IsBusy` 269), `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs` lines 15-118, `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory.GetSetterBodyLines` 466, `GenerateCollectionMembers` 754), `Src/Core/VeloxDev.Core.Test/MVVM/CommandAllocationTests.cs`.
