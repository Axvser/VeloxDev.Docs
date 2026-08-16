# Data Flow — Weak Types

All four types are lock-guarded; dead references are skipped or pruned on access. The diagrams below trace the three representative flows.

## 1. WeakQueue — enqueue, collect, dequeue skips dead refs

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "WeakQueue~T~" as W
participant "WeakReference~T~" as WR
participant "GC" as G

C -> W: Enqueue(new Payload(1))
activate W
W -> WR: new WeakReference~T~(item)
W --> C: void
deactivate W

note over WR,G: the Payload has no other strong reference -> GC collects it

C -> G: GC.Collect()
G -> WR: target cleared (TryGetTarget -> false)

C -> W: TryDequeue(out item)
activate W
W -> WR: Dequeue() then TryGetTarget(out item)
WR --> W: false (dead)
W -> W: loop continues to next reference
note over W: dead entry is dropped, not returned
W --> C: false / next live item
deactivate W
@enduml
```

Runtime probe, 2026-08-17: after `GC.Collect()` the queue reported `Count: 1` and `TryDequeue` returned only the still-alive item.

## 2. WeakCache — AddOrUpdate and periodic sweep

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "WeakCache~K~V~" as W
participant "ConditionalWeakTable" as T
participant "sweep List~WeakReference~K~~" as L

C -> W: AddOrUpdate(key, value)
activate W
W -> W: _counter++ ; if _counter > _perceptionThreshold
alt threshold crossed
    W -> L: RemoveAll(w => !w.TryGetTarget(out _))
    W -> W: _counter = 0
    W -> W: _perceptionThreshold = GetNextCleanupThreshold(count)
end
W -> T: Add(key, value) (replaces existing)
W -> L: Add(new WeakReference~K~(key))
W --> C: void
deactivate W

note over T: key collected elsewhere -> ConditionalWeakTable entry disappears

C -> W: TryGetCache(key, out value)
activate W
W -> T: TryGetValue(key)
alt live key
    T --> W: value
    W --> C: true
else key collected
    T --> W: miss
    W --> C: false
end
deactivate W
@enduml
```

Source: `WeakCache.cs` lines 44-63 (`AddOrUpdate`), 31-43 (`TryGetCache`), 75-79 (`GetNextCleanupThreshold`).

## 3. WeakDelegate — pruning collected handlers on invoke/clone

```plantuml
@startuml
!theme plain

participant "Publisher" as P
participant "WeakDelegate~T~" as W
participant "WeakReference~Delegate~" as WR
participant "Subscriber" as S

P -> W: AddHandler(live.Handle)
P -> W: AddHandler(dead.Handle, CanUpdateCache: false)
note over W: cache stays null (or live-only); dead is only weakly held

note over WR,S: dead subscriber goes out of scope -> GC collects it

P -> W: Invoke([args])
activate W
alt cache is null
    W -> W: RebuildCache()
    W -> WR: TryGetTarget per handler
    WR --> W: live -> combine ; dead -> skip
    W -> W: _combinedDelegate = combined live handlers
end
W -> S: live handler executes (dead handler pruned)
W --> P: void
deactivate W

P -> W: Clone()
activate W
W -> W: rebuild from live handlers only
W --> P: new WeakDelegate (no dead handlers)
deactivate W
@enduml
```

Source: `WeakDelegate.cs` lines 10-19 (`AddHandler`), 40-51 (`GetInvocationList`), 62-76 (`RebuildCache`), 78-87 (`CleanupCollectedHandlers`), 89-104 (`Clone`). Runtime probe, 2026-08-17: after GC, invoking the original ran only the live handler (counter `1`), and invoking a `Clone` also ran only the live handler (counter `2`).
