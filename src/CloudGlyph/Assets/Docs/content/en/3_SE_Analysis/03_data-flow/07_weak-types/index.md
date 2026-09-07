# Data Flow — Weak Types

All four types are guarded by a per-instance `lock`, and dead references are skipped or pruned on access. The three diagrams trace the representative flows: a weak queue, the ephemeron cache sweep, and the weak multicast. Generic constraints make the payload a reference type: `WeakQueue<T>` / `WeakStack<T>` are `where T : class`, so `TryDequeue` / `TryPop` / `TryPeek` surface a `T?` whose null/`false` also means "no live item".

## 1. WeakQueue — enqueue, collect, dequeue skips dead refs

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "WeakQueue~T~" as W
participant "WeakReference~T~" as WR
participant "GC" as G

C -> W: Enqueue(payload)
activate W
W -> WR: new WeakReference~T~(payload)
W --> C: void
deactivate W

note over WR: payload has no other strong reference, so it is collectible

C -> G: GC.Collect()
G --> WR: target cleared (TryGetTarget -> false)

C -> W: TryDequeue(out item)
activate W
loop while _references.Count > 0
    W -> WR: Dequeue().TryGetTarget(out item)
    alt collected target
        WR --> W: false - wrapper already dropped, scan next
    else live target
        WR --> W: true
        W --> C: item returned
    end
end
W --> C: false (queue exhausted)
deactivate W
@enduml
```

`Enqueue` only wraps the item (`WeakQueue.cs`, lines 34-42). `TryDequeue` pops the front and calls `TryGetTarget`; a collected payload means the wrapper has already been dropped and the loop continues (lines 63-78). `TryPeek` behaves the same but keeps the live front in place, dropping only dead entries (lines 80-96). `Count` and `GetEnumerator` first run `Prune()` over the whole backing queue (lines 10-21, 107-120, 124-135), so the reported count and the yielded items are always live; a dead payload is never returned.

## 2. WeakCache — AddOrUpdate, periodic sweep, ephemeron eviction

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "WeakCache~TTargetKey, TCacheKey~" as W
participant "ConditionalWeakTable" as T
participant "tracking List~WeakReference~TTargetKey~~" as L

C -> W: AddOrUpdate(key, value)
activate W

alt _counter > _perceptionThreshold
    W -> L: RemoveAll dead weak refs
    W -> W: _counter = 0
    W -> W: _perceptionThreshold = GetNextCleanupThreshold(live count)
end

alt key is already cached
    W -> T: Remove(key)
    W -> L: RemoveAll refs equal to key
end

W -> T: Add(key, value)
W -> L: Add(new WeakReference~TTargetKey~(key))
W -> W: _counter++
W --> C: void
deactivate W

note over T: the key is held weakly (ephemeron) - when it dies, the entry and its value die together

C -> W: TryGetCache(key, out value)
activate W
W -> T: TryGetValue(key)
alt key alive
    T --> W: value
    W --> C: true
else key collected
    T --> W: miss
    W --> C: false
end
deactivate W
@enduml
```

The table (`_caches`) is the source of truth for lookup. `AddOrUpdate` first checks the sweep counter, then, because `ConditionalWeakTable.Add` throws when the key already exists, explicitly `Remove`s a prior entry before adding the new one; it also refreshes the tracking list so `_targets` holds one weak reference per live key (lines 44-63). `TryGetCache` is a plain table read (lines 31-43): when the key has been collected the ephemeron entry is gone, so the value — which is only ever referenced through the table while the key lives — is gone too, and no manual eviction is needed. `ForeachCache` (lines 14-30) prunes dead tracking refs first and then walks the surviving keys through the table. Note the sweep threshold grows geometrically from the live count (`GetNextCleanupThreshold`, lines 75-79), which keeps the periodic cleanup amortized O(1) per insert.

## 3. WeakDelegate — weak multicast and pruning on rebuild

```plantuml
@startuml
!theme plain

participant "Publisher" as P
participant "WeakDelegate~TDelegate~" as W
participant "WeakReference~Delegate~" as WR
participant "Subscriber (transient)" as S

P -> W: AddHandler(steady.Handle)
note over W: default CanUpdateCache: true rebuilds the combined cache
P -> W: AddHandler(transient.Handle, CanUpdateCache: false)
note over W: transient kept weakly only; strong cache stays steady-only

note over S: transient goes out of scope, GC collects it

P -> W: Invoke(args)
activate W
W -> W: read _combinedDelegate (volatile, lock-free)
W --> P: steady runs; collected transient is never invoked
deactivate W

P -> W: RemoveHandler(other) / Clone()
activate W
W -> W: RebuildCache() -> CleanupCollectedHandlers()
W -> WR: TryGetTarget(out _)
WR --> W: false (dead) - wrapper removed from _handlers
W -> W: Delegate.Combine(live handlers)
W --> P: cache now holds live handlers only
deactivate W
@enduml
```

`AddHandler` appends a `WeakReference<Delegate>` and, when `CanUpdateCache` is true, immediately rebuilds the combined delegate (lines 10-18); `RemoveHandler` scans from the tail and removes matching entries (lines 20-33). Invocation never walks the weak list on the hot path: `GetInvocationList` returns the cached `_combinedDelegate` through a lock-free `volatile` read, and only locks-and-rebuilds when the cache is null (lines 40-51). `Invoke(object?[] objects)` DynamicInvokes that cached delegate (lines 58-61) — callers that know the signature invoke it typed instead, which is what `TransitionEffectCore` does per frame (`TransitionEffect.cs`, lines 87-90). The cached delegate is a strong reference, so pruning only removes the wrapper entries of collected handlers: `RebuildCache` calls `CleanupCollectedHandlers` (lines 63-77, 79-88), and `Clone` copies only the live handlers into a fresh instance (lines 90-105). The one leak-shaped corner is therefore a handler added with the default cache update that never unsubscribes — it stays rooted by the strong cache until some later add/remove/clone rebuilds around it.

Source: `Src/Core/VeloxDev.Core/WeakTypes/{WeakQueue,WeakStack,WeakDelegate,WeakCache}.cs`; usage in `Src/Core/VeloxDev.Core/TransitionSystem/TransitionEffect.cs`; behavior covered by `Src/Core/VeloxDev.Core.Test/WeakTypes/*.cs` (FIFO/LIFO ordering, peek, range ops, cache overwrite/remove/cleanup).
