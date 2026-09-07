# Complexity Analysis — Weak Types

The three shapes of weak container share one cost model: an **amortized O(1) hot path** plus an **occasional O(n) sweep** that reclaims the empty wrappers of collected objects. Every operation here is lock-guarded (`lock (_lock)`), so these are single-threaded-amortized bounds that also hold per-lock-section under contention.

## WeakQueue / WeakStack

Mutation is a lock-guarded `Queue`/`Stack` push/pop on a `WeakReference<T>`:

$$
\text{Enqueue / Push: } O(1), \qquad \text{TryDequeue / TryPop / TryPeek: } O(1 + d) \text{ amortized}
$$

where $d$ = dead references at the front / top. `TryDequeue`/`TryPop`/`TryPeek` pop and drop dead wrappers until they reach a live item (or empty), so each dead wrapper is dropped exactly once over its lifetime — the accumulated cost of skipping dead entries is amortized O(1) per entry added. `Count`, `GetEnumerator` and `TrimExcess` first compact the whole structure (`Prune()`, `WeakQueue.cs` lines 124-135; `WeakStack.cs` lines 124-136, which also reverses so LIFO order survives):

$$
O(n), \quad n = \text{stored reference wrappers}
$$

| Operation | Complexity |
|---|---|
| `Enqueue` / `Push` | $O(1)$ |
| `EnqueueRange` / `PushRange` | $O(k)$, $k$ = input size ($PushRange$ adds an $O(k)$ `Reverse` so items keep their order on the stack) |
| `TryDequeue` / `TryPop` / `TryPeek` | $O(1 + d)$ amortized |
| `Count` / `GetEnumerator` / `TrimExcess` | $O(n)$ worst-case (prune first) |
| `Clear` | $O(n)$ — the BCL `Queue`/`Stack` nulls out every stored slot to release the wrappers |

**Memory.** The container holds $O(n)$ `WeakReference<T>` wrappers and never roots the payloads, so a payload becomes collectible as soon as no other strong reference exists. Between sweeps the container may hold empty wrappers for already-collected payloads (garbage slots), but because every `Count`/enumeration/`TrimExcess` compacts and every pop skips them, the wasted space is transient and bounded by the live working set.

## WeakCache

`AddOrUpdate` / `TryGetCache` / `Remove` are `ConditionalWeakTable` operations plus a list scan, so lookup and insert are amortized O(1). Cleanup is periodic, triggered when the insert counter exceeds an **adaptive** threshold (`_perceptionThreshold`, default `4`):

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs (lines 75-79)
private static int GetNextCleanupThreshold(int currentCount)
{
    int nextCapacity = currentCount == 0 ? 4 : currentCount * 2;
    return (int)(nextCapacity * 0.9);
}
```

The sweep threshold grows geometrically with the live count, so the per-insert amortized cost stays constant:

$$
\text{sweep: } O(n) \text{ worst-case}, \qquad \text{amortized } O(1) \text{ per insert}
$$

| Operation | Complexity |
|---|---|
| `AddOrUpdate` | amortized $O(1)$ (occasional $O(n)$ sweep of the tracking list) |
| `TryGetCache` | amortized $O(1)$ (table read; the key's liveliness does not change the cost) |
| `Remove` | $O(1)$ table removal + $O(n)$ scan of the tracking list |
| `ForeachCache` | $O(n)$ (prune tracking list + walk live keys through the table) |

**Memory.** The `ConditionalWeakTable` is the source of truth: it weakly references each target key and strongly references the value only while the key lives, so the cache holds $O(n_{\text{live}})$ live entries and never roots a dead key's value — eviction is automatic and exact, no leak window. The tracking list adds $O(m)$ weak references ($m \ge n_{\text{live}}$, cleaned by the sweep) purely to support enumeration and duplicate tracking; it never participates in lookup and never roots a key.

## WeakDelegate

The hot path is a single `volatile` field read, which is why the per-frame invocation in the transition engine is lock-free:

$$
O(1) \text{ — cached combined delegate is read, then invoked typed or via DynamicInvoke}
$$

Rebuilding the multicast cache costs a pass over the handler list: `RebuildCache` runs `CleanupCollectedHandlers` ($O(h)$) and then `Delegate.Combine`s every live handler ($O(h)$), where $h$ = stored handler wrappers.

| Operation | Complexity |
|---|---|
| `AddHandler` (`CanUpdateCache: true`) | $O(1)$ append + $O(h)$ rebuild |
| `AddHandler` (`CanUpdateCache: false`) | $O(1)$ |
| `RemoveHandler` | $O(h)$ scan/remove (+ $O(h)$ rebuild if requested) |
| `GetInvocationList` (cache hit) | $O(1)$, lock-free |
| `GetInvocationList` (cache miss) | $O(h)$ rebuild under the lock |
| `Invoke(object?[] objects)` | $O(1)$ read + DynamicInvoke dispatch cost |
| `Clone` | $O(h)$ (copy live handlers + rebuild) |

**Memory.** `_handlers` is $O(h)$ `WeakReference<Delegate>` wrappers plus one cached combined delegate. The combined delegate is a **strong** reference to every handler added since the last rebuild — the only strong reference in the whole feature — so unsubscribed handlers are released only when a rebuild excludes them (`CleanupCollectedHandlers` drops the dead wrappers). Handlers added with `CanUpdateCache: false` never enter the cache and are genuinely weak.

## Per-operation summary

| Operation | Complexity |
|---|---|
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | $O(1)$ amortized |
| `WeakQueue.Count` / enumeration | $O(n)$ worst-case (prune) |
| `WeakCache.AddOrUpdate` / `TryGetCache` | $O(1)$ amortized |
| `WeakCache` periodic sweep | $O(n)$ worst-case, amortized $O(1)$ |
| `WeakDelegate.GetInvocationList` (hot path) | $O(1)$, lock-free |
| `WeakDelegate` add/remove/clone | $O(h)$ rebuild |
| Memory growth | Payloads are never rooted (except `WeakDelegate`'s rebuilt combined delegate); empty wrappers are reclaimed on access, so dead entries do not grow memory permanently |
