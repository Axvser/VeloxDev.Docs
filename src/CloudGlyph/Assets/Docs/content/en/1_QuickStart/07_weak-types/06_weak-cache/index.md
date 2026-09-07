# Weak Types — WeakCache<TTargetKey, TCacheKey>

`WeakCache<TTargetKey, TCacheKey>` (source `Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs`) attaches a **value** to a **target key** so the value lives exactly as long as the key does. It is built on `System.Runtime.CompilerServices.ConditionalWeakTable<TTargetKey, TCacheKey>`, which never roots the key — the moment the key becomes unreachable the entry can be collected with it. Both type arguments must be reference types.

Think of it as a per-object side-table: "for this live object, remember this derived value" (a cached analysis, a label, an event subscription count), without turning the table into a leak that keeps keys alive forever.

## 1. Add, read, overwrite

`AddOrUpdate(target, value)` inserts or replaces the association; `TryGetCache(target, out value)` reads it back (`true` and the value when the key is live and present, otherwise `false` with `out null`):

```csharp
using System;
using VeloxDev.WeakTypes;

var cache = new WeakCache<Payload, string>();   // Payload is the helper from the Complete Code page
var key1 = new Payload(100);

cache.AddOrUpdate(key1, "value-100");
if (cache.TryGetCache(key1, out var label)) Console.WriteLine($"label: {label}");   // value-100

cache.AddOrUpdate(key1, "updated");             // overwrite the association
Console.WriteLine(cache.TryGetCache(key1, out var v2) ? v2 : "(null)");            // updated
```

**Expected result:** a missing association returns `false` (`TryGetCache_Missing_ReturnsFalse`) and re-adding the same key replaces the old value (`AddOrUpdate_OverwritesExisting`), matching `WeakCacheTests.cs`.

## 2. Remove

`Remove(target)` deletes the association if present; removing a key that is not cached is a harmless no-op:

```csharp
cache.Remove(key1);
Console.WriteLine($"after Remove: {cache.TryGetCache(key1, out _)}");   // False
```

**Expected result:** after `Remove` the lookup returns `false` (`Remove_DeletesEntry`), and `cache.Remove(new Payload(999))` does not throw (`Remove_NonExistent_NoException`).

## 3. Enumerate the live associations

`ForeachCache(Action<TTargetKey, TCacheKey> action)` calls your callback for every *live* key/value pair:

```csharp
var second = new Payload(200);
cache.AddOrUpdate(key1, "value-100");
cache.AddOrUpdate(second, "value-200");
cache.ForeachCache((key, value) => Console.WriteLine($"key={key.Value} -> {value}"));
```

**Expected result:** the callback runs once per live entry — matching `ForeachCache_IteratesAllEntries`, which collects the visited pairs into a dictionary and asserts both are present.

## 4. Eviction is driven by the key

Because the table does not root its keys, eviction happens on the key's own lifetime, not on an explicit size limit:

- When `key1` loses its last strong reference and the GC runs, its row disappears from the conditional weak table, and a later `TryGetCache(key1, out _)` returns `false`.
- The cache also keeps a bookkeeping list of `WeakReference<TTargetKey>` entries (to enumerate keys cheaply); those weak references never pin the keys, and stale entries are removed when `ForeachCache` runs or when the insertion counter crosses a cleanup threshold inside `AddOrUpdate` (`AddOrUpdate_ManyItems_TriggersCleanup` exercises this path with 20 live `object` keys).
- The unit tests use *string literal* keys that are interned by the runtime and therefore never collected, so they prove API behaviour but not eviction. The runnable program on the [Verify & Complete Code](../08_verify-and-complete-code/) page uses real `Payload` keys and shows `TryGetCache` returning `false` after a GC removed a dead key.

**Expected result:** you can predict which associations survive a GC, and you know that adding 20 live keys then reading the last one still succeeds. Detailed GC rules are on the [GC Behavior](../07_gc-behavior/) page.
