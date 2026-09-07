# Weak Types — `WeakCache<TTargetKey, TCacheKey>`

Namespace `VeloxDev.WeakTypes`. A sealed cache that binds a value to a *weak* target key: the mapping lives in a `ConditionalWeakTable<TTargetKey, TCacheKey>` (backed by a sweep list of `WeakReference<TTargetKey>`), so the cache never roots its keys — once a target is otherwise unreachable it is collected and its entry disappears automatically.

```csharp
public sealed class WeakCache<TTargetKey, TCacheKey>
    where TTargetKey : class
    where TCacheKey : class
```

Both type parameters must be class types. Because the `ConditionalWeakTable` treats its key as ephemeron-like, the stored `TCacheKey` value stays alive while its `TTargetKey` target is alive, and both die together when the target is collected. All methods are synchronized on an internal lock.

## Fields

### `WeakCache<TTargetKey,TCacheKey>._perceptionThreshold`

**Signature:**
`public int _perceptionThreshold = 4;`

**Type:** `int`

**Notes:**
- A public, mutable field (name kept exactly as in source) controlling how many insertions may accumulate before `AddOrUpdate` runs a cleanup sweep.
- `AddOrUpdate` sweeps once the internal counter exceeds this value: it removes collected targets from the sweep list, resets the counter to `0`, and re-derives the threshold from the number of remaining targets (`GetNextCleanupThreshold` — about `0.9 × 2 × count`, or back to `4` when no target remains). So the field is both a tunable knob and an adaptive watermark.
- Default `4`. Verified together with the sweep behaviour by `WeakCacheTests.AddOrUpdate_ManyItems_TriggersCleanup`.

## Methods

### `WeakCache<TTargetKey,TCacheKey>.AddOrUpdate`

**Signature:**
`public void AddOrUpdate(TTargetKey target, TCacheKey cache)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The weak key to bind the value to. |
| `cache` | `TCacheKey` | The value to store for `target`. |

**Returns:** `void`

**Notes:**
- If an entry already exists for `target`, it is removed first and then re-added, so the stored value is overwritten — verified by `WeakCacheTests.AddOrUpdate_OverwritesExisting` and `AddOrUpdate_And_TryGetCache_ReturnsValue`.
- Also records `target` in the weak sweep list so enumeration and cleanup can find it; sweeps on insert as described under `_perceptionThreshold`.
- Runs under the internal lock.

### `WeakCache<TTargetKey,TCacheKey>.TryGetCache`

**Signature:**
`public bool TryGetCache(TTargetKey target, out TCacheKey? cache)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The key to look up. |
| `cache` | `TCacheKey?` | The stored value when the method returns `true`; `null` otherwise. |

**Returns:** `bool` — `true` when `target` currently has an entry.

**Notes:**
- Because the entry dies with its key, a collected key simply yields `false` — verified by `WeakCacheTests.TryGetCache_Missing_ReturnsFalse`.
- Runs under the internal lock.

### `WeakCache<TTargetKey,TCacheKey>.Remove`

**Signature:**
`public void Remove(TTargetKey target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The key whose entry should be removed. |

**Returns:** `void`

**Notes:**
- Removes the table entry and any matching reference in the sweep list.
- Removing a key that has no entry is a no-op — verified by `WeakCacheTests.Remove_DeletesEntry` and `Remove_NonExistent_NoException`.

### `WeakCache<TTargetKey,TCacheKey>.ForeachCache`

**Signature:**
`public void ForeachCache(Action<TTargetKey, TCacheKey> action)`

| Parameter | Type | Description |
|---|---|---|
| `action` | `Action<TTargetKey, TCacheKey>` | Callback invoked once per live entry with the target and its value. |

**Returns:** `void`

**Notes:**
- First prunes collected targets from the sweep list, then iterates the remaining live targets and invokes `action` for each one that still has a table entry — verified by `WeakCacheTests.ForeachCache_IteratesAllEntries`.
- Runs under the internal lock.

## Source

`Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs`
