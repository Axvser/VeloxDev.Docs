# Complexity Analysis — Weak Types

## WeakQueue / WeakStack

$$\text{Enqueue / Push: } O(1), \quad \text{TryDequeue / TryPop: } O(1) \text{ amortized}$$

Each mutation is a lock-guarded `Queue`/`Stack` operation on a `WeakReference<T>`. `TryDequeue` / `TryPop` / `TryPeek` skip collected references in a loop:

$$O(1 + d) \text{ amortized}, \quad d = \text{dead references at the front / top}$$

`Count`, `GetEnumerator` and `TrimExcess` first prune the whole structure (`Prune()`, `WeakQueue.cs` lines 124-135 / `WeakStack.cs` lines 124-136):

$$O(n), \quad n = \text{stored references}$$

so the worst case for `Count` / enumeration is $O(n)$, while the common mutation path stays amortized $O(1)$.

| Operation | Complexity |
|---|---|
| `Enqueue` / `Push` | $O(1)$ |
| `EnqueueRange` / `PushRange` | $O(k)$, $k$ = input size (plus $O(k)$ reverse for the stack) |
| `TryDequeue` / `TryPop` / `TryPeek` | $O(1 + d)$ amortized |
| `Count` / `GetEnumerator` / `TrimExcess` | $O(n)$ worst-case (prune first) |
| `Clear` | $O(1)$ (clear the container) |

## WeakCache

$$O(1) \text{ amortized}$$

`AddOrUpdate` / `TryGetCache` / `Remove` are `ConditionalWeakTable` operations plus a list insert / scan. Cleanup is periodic, triggered when the insert counter exceeds an **adaptive** threshold (`_perceptionThreshold`, default `4`):

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs (lines 75-79)
private static int GetNextCleanupThreshold(int currentCount)
{
    int nextCapacity = currentCount == 0 ? 4 : currentCount * 2;
    return (int)(nextCapacity * 0.9);
}
```

The sweep grows the threshold geometrically, so the per-insert amortized cost stays constant:

$$\text{sweep: } O(n) \text{ worst-case}, \quad \text{amortized } O(1) \text{ per insert}$$

| Operation | Complexity |
|---|---|
| `AddOrUpdate` | $O(1)$ amortized (occasional $O(n)$ sweep) |
| `TryGetCache` | $O(1)$ amortized |
| `Remove` | $O(1)$ table removal + $O(n)$ sweep-list scan |
| `ForeachCache` | $O(n)$ (prune + iterate live entries) |

## Memory

| Structure | Behavior |
|---|---|
| `WeakDelegate` | $O(h)$ `WeakReference<Delegate>` + one cached combined delegate; **no strong reference** to subscribers while the cache is unbuilt |
| `WeakQueue` / `WeakStack` | $O(n)$ weak refs; dead refs pruned on access; entries do not root the objects |
| `WeakCache` | `ConditionalWeakTable` + $O(n)$ sweep list; a key that becomes unreachable is removed from the table automatically |

The defining property is that **weak references avoid retention**: a subscriber, queue item, or cache key that becomes unreachable elsewhere can be collected, which is exactly the leak-avoidance these types exist for. The only strong reference is `WeakDelegate`'s cached combined delegate, which is rebuilt (and pruned) on the next `AddHandler` / `RemoveHandler` / `Clone` / cache-miss `GetInvocationList`.

## Per-operation summary

| Operation | Complexity |
|---|---|
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | $O(1)$ amortized |
| `WeakQueue.Count` / enumeration | $O(n)$ worst-case (prune) |
| `WeakCache.AddOrUpdate` / `TryGetCache` | $O(1)$ amortized |
| `WeakCache` periodic sweep | $O(n)$ worst-case |
| Memory growth | Dead entries do not grow memory permanently — they are pruned on access |
