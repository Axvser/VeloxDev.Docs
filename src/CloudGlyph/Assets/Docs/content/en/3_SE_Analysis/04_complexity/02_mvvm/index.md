# Complexity Analysis — MVVM

All bounds refer to the runtime in `Src/Core/VeloxDev.Core/MVVM/{CommandPipeline{TParam,TResult}.cs, CommandCompletion.cs, ObservableCollectionTracker.cs}` and to the generated code templates in `Src/Generators/VeloxDev.Core.Generator/{Base/Analizer.cs, Writers/CommandWriter.cs}`. The generator adds $O(P + C)$ generated members per annotated type at compile time, where $P$ is the number of `[VeloxProperty]` members and $C$ the number of `[VeloxCommand]` methods; none of that work repeats at run time.

**Notation.** $n$ = in-flight executions (active + queued), $k$ = items in an old + new collection during a replacement, $m$ = items affected by one `CollectionChanged`, $H$ = subscribers of one event, $R$ = emitters that would like to report `Canceled` for one execution.

## Generated property setter (default mode)

$$
T_{\text{set}}(scalar) = O(1)
$$

The steps are the equality guard, capturing `old`, `OnPropertyChanging`, `On{Name}Changing`, the assignment, `On{Name}Changed` and `OnPropertyChanged`. The setter body is emitted by `MVVMPropertyFactory.GetSetterBodyLines` (`Base/Analizer.cs`).

```csharp
// Source: Base/Analizer.cs — Default setter mode
if(global::System.Object.Equals(this._count, value)) return;
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

$$
T_{\text{notify}}(scalar) = O(1) + O(H)
$$

where $H$ is the number of subscribed `PropertyChanged` / `PropertyChanging` handlers. The fan-out is dominated by subscribers, not by the number of properties.

## CollectionChanged handler (per mutation)

The generated `On{Name}CollectionChanged` forwards the raw event to `OnCollectionChanged<T>` and, on Add / Remove / Replace / Move, materializes the affected items through `Enumerate{Name}Items` → `ToArray`:

$$
T_{\text{mutation}} = O(m)
$$

for $m$ affected items (`MVVMPropertyFactory.GenerateCollectionMembers`). A `Reset` is $O(1)$: it carries no items and dispatches to `OnItemsResetIn{Name}`.

## `ObservableCollectionTracker`

$$
\text{EnsureSubscribed} = O(1)\ \text{amortized}, \qquad \text{Unsubscribe} = O(1)
$$

`ConditionalWeakTable.GetOrCreateValue` plus a `HashSet<Delegate>` add, guarded by a lock. The dedup key is the `(Method, Target)` pair, which makes repeated getter accesses idempotent:

$$
q \text{ getter reads} \;\Rightarrow\; 1 \text{ subscription}
$$

Without that dedup the event's invocation list would grow by one delegate per read, so a later mutation would cost $O(q)$ instead of $O(1)$.

Weak-reference keys mean the tracking entry disappears when the collection is garbage-collected, so the table's size is bounded by live collections.

## Command execution

Normal execution with capacity available:

$$
T_{\text{execute}} = O(1)
$$

`ExecuteCore` does one `SemaphoreSlim.WaitAsync`, one `_active.Add`, and starts the body. When capacity is exhausted the item is enqueued:

$$
T_{\text{enqueue}} = O(1), \qquad \text{queue depth} \le n
$$

`TryStartPendingAsync` drains up to `_maxConcurrency` items at once:

$$
T_{\text{drain}} = O(n)\ \text{for the drain}, \qquad O(1)\ \text{amortized per trigger}
$$

`CanExecute` evaluates the user predicate plus the force-lock flag in $O(1)$, and `Notify()` → `RaiseCanExecuteChanged()` is $O(H)$ in the number of `CanExecuteChanged` subscribers.

`EventContext` changes the constant, not the complexity: with a context set, each event costs one `SynchronizationContext.Post` — $O(1)$ — but the handler runs on the context's thread at its own time.

Typed commands carry the parameter and result in their own types through the queue, so the per-execution cost is the same $O(1)$ with less boxing; the arity family packs multiple parameters into a `ValueTuple`, which is a struct and allocates nothing.

## Cancellation, clearing and disposal

$$
T_{\text{interrupt}} = O(a), \qquad T_{\text{clear}} = O(a + q)
$$

where $a$ = active and $q$ = queued executions swept (`InterruptAsync`, `ClearAsync`). Both are linear in the number of affected items because each needs a `Cancel()` and one event.

Per-execution resource handling is $O(1)$: one `CancellationTokenSource` is created when `_isCtsNeeded` and disposed exactly once — by `ExecuteCoreAsync`'s `finally` for anything that ran, or by `ClearAsync` for a pending item that never ran. `TakeCts` is `Interlocked.Exchange`, $O(1)$, so two racers cannot both claim disposal.

## The awaitable path

$$
T_{\text{executeAndWait}} = T_{\text{execute}} + O(1)
$$

`ExecuteAndWaitAsync` adds one `TaskCompletionSource<CommandCompletion>` and one token registration. Completing the sink is $O(1)$ via `TrySetResult` / `TrySetCanceled`, and `RunContinuationsAsynchronously` keeps the continuation off the pipeline's stack. `ExecuteAndWaitTypedAsync` is the same shape with a typed completion; returning `TResult` avoids the boxing of the untyped path.

The single-`Canceled` guarantee is $O(1)$:

$$
\text{reports per execution} = \min(R,\ 1) = 1
$$

`TryMarkCancelReported` is a single `Interlocked.Exchange`, so however many emitters want to report a cancellation — `Interrupt`, `Clear`, the body's own `OperationCanceledException` — exactly the first succeeds.

## Memory usage

| Structure | Complexity |
| --- | --- |
| Generated members per annotated type | $O(P + C)$, constant per type |
| Command state | $O(n)$ `CommandEventArgs` across `_active` (a `HashSet`) + `_pendingQueue` (a `Queue`) |
| Per execution, subscribed stages | $O(1)$ `CommandEventArgs` **per stage with a subscriber**; a stage with no subscriber allocates nothing |
| Per execution, awaiting call | $O(1)$: one `TaskCompletionSource` |
| Per cancellable execution | $O(1)$: one `CancellationTokenSource`, disposed at the end of that execution |
| `ObservableCollectionTracker` table | $O(\text{live collections})$, via `ConditionalWeakTable` |
| `CommandCompletion` | a `readonly struct`: no allocation of its own |
| Typed command argument/result | no box on the typed path; binding through `ICommand` still boxes |

The per-subscriber allocation rule is the one the code was explicitly shaped around:

$$
\text{alloc} = O\bigl(|\{\text{stages with at least one subscriber}\}|\bigr)
$$

`CommandAllocationTests` pins it relatively — a command with no subscribers must allocate strictly less per execution than one with all eight events subscribed — rather than against an absolute figure.

## Per-operation summary

| Operation | Complexity |
| --- | --- |
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
| `ExecuteAndWaitAsync` / typed twin | as `ExecuteAsync` $+ O(1)$ |
| `IsBusy` / `ActiveCount` / `PendingCount` | $O(1)$ — two `Count` reads, no lock taken |
| Extension lookup | $O(1)$: one `as` cast, or a `NotSupportedException` |
| `Notify()` / `CanExecuteChanged` | $O(H)$ handlers |
| `Lock` / `Unlock` / `Continue` | $O(1)$, plus a drain when the queue is non-empty |
| `ChangeSemaphore` | $O(1) + O(n)$ drain |
| `Interrupt` | $O(a)$ |
| `Clear` | $O(a + q)$ |
| `Dispose` | $O(1)$ |

## Caveats on these bounds

- All are **steady-state** costs. The generator's work is compile-time and does not appear at run time.
- $H$, $n$, $a$, $q$, $k$ and $m$ are unbounded from the library's point of view; the bounds are exact in these parameters.
- The `EventContext` path trades ordering guarantees for thread affinity, not for time: complexity is unchanged, but events are posted asynchronously.
- `IsBusy` / `ActiveCount` / `PendingCount` are deliberately **not** synchronized with the state lock, so a concurrent update may leave them one step stale. Reading them is $O(1)$ but not linearizable — a deliberate trade.
