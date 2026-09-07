# Weak Types — GC Behavior

All four types store *weak* references, so their contents are governed by the garbage collector. This page collects the rules you must internalise before using them; the code comes from `Src/Core/VeloxDev.Core/WeakTypes/`.

## 1. What each type stores

| Type | Backing storage |
|---|---|
| `WeakQueue<T>` | `Queue<WeakReference<T>>` |
| `WeakStack<T>` | `Stack<WeakReference<T>>` |
| `WeakDelegate<TDelegate>` | `List<WeakReference<Delegate>>` **plus** a cached combined delegate (`_combinedDelegate`, volatile) |
| `WeakCache<TTargetKey, TCacheKey>` | `ConditionalWeakTable<TTargetKey, TCacheKey>` **plus** a bookkeeping `List<WeakReference<TTargetKey>>` |

None of these root the item. A `WeakReference<T>` does not keep its target alive — it simply allows you to observe whether the target still exists and to recover it if it does.

**Expected result:** you can name the exact storage behind each type and say what is weak.

## 2. Sweep-on-access

Dead entries are not removed eagerly in the background; they are swept when you touch the collection:

- `WeakQueue<T>.Count` (and therefore `IsEmpty`) runs `Prune()` first, so it reports only live items.
- `TryDequeue` / `TryPeek` (and the stack's `TryPop` / `TryPeek`) loop over dead front/top entries and drop them until they reach a live one; they return `false` with `out null` if there is none.
- `GetEnumerator()` prunes and yields only live items.
- `WeakDelegate<TDelegate>` cleans collected weak entries inside `RebuildCache` (an `Add`/`Remove` with `CanUpdateCache: true`, an empty-cache `GetInvocationList`, or `Clone`).
- `WeakCache<TTargetKey, TCacheKey>` rows vanish from the conditional weak table automatically when the key dies; the bookkeeping `WeakReference<TTargetKey>` list is swept by `ForeachCache` and periodically by `AddOrUpdate` when the insertion counter crosses its cleanup threshold.

**Expected result:** you can predict that a dead entry "disappears" the next time the collection is read, not before.

## 3. Collection happens at GC, not at access

A weak entry does not die the instant its last strong reference goes out of scope. The target is collected only when the next GC runs. Until then the weak reference may still report the target as alive, and `Count` still counts it. This is why the demo on the [Complete Code](../08_verify-and-complete-code/) page forces a GC before reading the collections; in production you simply let the GC run on its own schedule.

**Expected result:** you understand that "weak" means *collectible*, not *gone immediately*.

## 4. Making a GC demo deterministic

The runnable program on the Complete Code page observes eviction reliably by shaping lifetimes deliberately:

- Every object meant to be collected is created **inside a helper method** (`FillQueue`, `FillStack`, `AddDeadHandler`, `AddDeadCacheEntry`) whose frame returns before the GC, so the object's only remaining reference is the weak one in the collection.
- Every object meant to survive is created in `Main` and pinned with a `GC.KeepAlive` call at the end.
- A `ForceGc` helper runs two full collections with a finalizer wait between them:

```csharp
private static void ForceGc()
{
    GC.Collect();
    GC.WaitForPendingFinalizers();
    GC.Collect();
}
```

`WaitForPendingFinalizers` matters only if the objects have finalizers (the sample `Payload` does not); the second `Collect` then reclaims anything the finalizer pass released. Run with `dotnet run -c Release` and without an attached debugger.

**Expected result:** the same items are collected on every `Release` run — the recorded transcript in the [Complete Code](../08_verify-and-complete-code/) page is stable.

## 5. Debug vs Release and other caveats

- **Debug / attached debugger.** Under a debugger, or in a Debug build, the JIT can keep local variables alive until the end of their enclosing scope, so objects you *think* are dead may still be reported live. That is why GC demonstrations are run in `Release`.
- **Interned strings.** String literals are interned by the runtime and stay reachable for the whole process. `WeakCacheTests.cs` uses keys such as `"key1"`, so those entries are never evicted; the tests assert API behaviour, not GC eviction. Use freshly allocated object keys (like the `Payload` in this Quick Start) to observe eviction.
- **Weak list still needs a rebuild trigger.** In `WeakDelegate<TDelegate>` the cached combined delegate strongly references every handler merged into it. A subscriber is only collected once it is not part of the current cache — add it with `CanUpdateCache: false`, or ensure a later rebuild/`Clone` drops it (see [WeakDelegate](../03_weak-delegate/)).
- **Do not build correctness on GC timing.** Use weak collections to *avoid leaks*, never to implement "fire exactly once after a delay" logic — collection timing is an implementation detail of the runtime.

**Expected result:** you can explain to a reviewer why a weak-collection result differed between Debug and Release, why the unit tests never assert eviction, and why `CanUpdateCache: false` exists.
