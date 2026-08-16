# Design Patterns — Weak Types

The four `VeloxDev.WeakTypes` collections all implement the **Weak Reference** idiom: they hold `WeakReference<T>` (or a `ConditionalWeakTable`) instead of strong references, so the GC can reclaim subscribers, queue items, stack items, and cache keys that become unreachable elsewhere. On top of that, they apply **Sweep-on-Access**: dead references are pruned lazily when a member is touched, so no background thread is needed for cleanup.

```mermaid
classDiagram
    class WeakDelegate~TDelegate~ {
        <<sealed>>
        -volatile TDelegate? _combinedDelegate
        -List~WeakReference~Delegate~~ _handlers
        +AddHandler(handler, CanUpdateCache) void
        +RemoveHandler(handler, CanUpdateCache) void
        +GetInvocationList() TDelegate?
        +Invoke(objects) void
        +Clone() WeakDelegate~TDelegate~
    }
    class WeakQueue~T~ {
        <<sealed>>
        -Queue~WeakReference~T~~ _references
        +Count int
        +IsEmpty bool
        +Enqueue(item) void
        +TryDequeue(out item) bool
        +TryPeek(out item) bool
        +TrimExcess() void
        +Clear() void
    }
    class WeakStack~T~ {
        <<sealed>>
        -Stack~WeakReference~T~~ _references
        +Count int
        +IsEmpty bool
        +Push(item) void
        +TryPop(out item) bool
        +TryPeek(out item) bool
        +TrimExcess() void
        +Clear() void
    }
    class WeakCache~TTargetKey, TCacheKey~ {
        <<sealed>>
        -ConditionalWeakTable~TTargetKey, TCacheKey~ _caches
        -List~WeakReference~TTargetKey~~ _targets
        +int _perceptionThreshold
        +AddOrUpdate(target, cache) void
        +TryGetCache(target, out cache) bool
        +Remove(target) void
        +ForeachCache(action) void
    }
    class WeakReference~T~ {
        <<struct>>
    }
    class ConditionalWeakTable~TTargetKey, TCacheKey~ {
        <<sealed>>
    }

    WeakDelegate~TDelegate~ o-- WeakReference~Delegate~ : stores handlers
    WeakQueue~T~ o-- WeakReference~T~ : stores items
    WeakStack~T~ o-- WeakReference~T~ : stores items
    WeakCache~TTargetKey, TCacheKey~ o-- ConditionalWeakTable~TTargetKey, TCacheKey~ : keyed storage
    WeakCache~TTargetKey, TCacheKey~ o-- WeakReference~TTargetKey~ : sweep list
```

## 1. Weak Reference idiom

Each type stores weak references instead of strong ones, so the container never keeps its payload alive.

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs (lines 34-42)
public void Enqueue(T item)
{
    if (item == null) throw new ArgumentNullException(nameof(item));
    lock (_lock)
    {
        _references.Enqueue(new WeakReference<T>(item));
    }
}
```

| Type | Storage | What stays collectible |
|---|---|---|
| `WeakDelegate<TDelegate>` | `List<WeakReference<Delegate>>` | Subscriber delegates (plus a strong combined-delegate cache) |
| `WeakQueue<T>` | `Queue<WeakReference<T>>` | Queued items |
| `WeakStack<T>` | `Stack<WeakReference<T>>` | Stacked items |
| `WeakCache<TTargetKey,TCacheKey>` | `ConditionalWeakTable` + `List<WeakReference<TTargetKey>>` | Cache keys (values die with their key) |

## 2. Sweep-on-Access

Dead references are pruned lazily when a member is touched, rather than by a dedicated thread.

| Type | Sweep trigger |
|---|---|
| `WeakQueue<T>` / `WeakStack<T>` | `Count`, `GetEnumerator`, `TrimExcess` call `Prune()`; `TryDequeue`/`TryPop`/`TryPeek` skip dead refs in a loop |
| `WeakDelegate<TDelegate>` | `RebuildCache()` (called from `AddHandler`/`RemoveHandler` with cache update, `GetInvocationList` when the cache is null, and `Clone`) |
| `WeakCache<TTargetKey,TCacheKey>` | `AddOrUpdate` sweeps when the insert counter exceeds `_perceptionThreshold`; `ForeachCache` removes dead targets first |

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakQueue.cs (lines 124-135)
private void Prune()
{
    var activeReferences = _references
        .Where(r => r.TryGetTarget(out _))
        .ToList();

    _references.Clear();
    foreach (var reference in activeReferences)
    {
        _references.Enqueue(reference);
    }
}
```

| Trade-off | Analysis |
|---|---|
| Lazy cleanup | Amortized O(1) per mutation; the occasional sweep is O(n) — acceptable because the sweep runs only when a dead ref is actually encountered |
| Weak cache of `WeakDelegate` | The combined-delegate cache is a strong reference; collected handlers are pruned only when the cache is rebuilt (documented in the API page) |

> Source references: `Src/Core/VeloxDev.Core/WeakTypes/*.cs`, verified by `Src/Core/VeloxDev.Core.Test/WeakTypes/*.cs` and a standalone console probe run on 2026-08-17.
