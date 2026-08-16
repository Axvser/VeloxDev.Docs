# Weak Types — `WeakCache`

Maps a weak key to a cache value via `ConditionalWeakTable<TTargetKey, TCacheKey>` plus a `List<WeakReference<TTargetKey>>` sweep list.

```csharp
public sealed class WeakCache<TTargetKey, TCacheKey>
    where TTargetKey : class
    where TCacheKey : class
{
    private readonly ConditionalWeakTable<TTargetKey, TCacheKey> _caches = new();
    private readonly List<WeakReference<TTargetKey>> _targets = [];
    public int _perceptionThreshold = 4;
}
```

#### `WeakCache<TTargetKey,TCacheKey>.AddOrUpdate`

**Signature:**
`public void AddOrUpdate(TTargetKey target, TCacheKey cache)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The weak key. |
| `cache` | `TCacheKey` | The value to store. |

**Returns:** `void`

**Notes:**
- Overwrites an existing entry for the same target. When the insert counter exceeds `_perceptionThreshold` (adaptive, default `4`), a sweep removes collected targets and the threshold grows (`GetNextCleanupThreshold` ≈ `0.9 * next capacity`). Verified by `WeakCacheTests.AddOrUpdate_*`.

#### `WeakCache<TTargetKey,TCacheKey>.TryGetCache`

**Signature:**
`public bool TryGetCache(TTargetKey target, out TCacheKey? cache)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The weak key. |
| `cache` | `TCacheKey?` | The stored value, or `null`. |

**Returns:** `bool` — `true` when the key exists and its value is retrieved.

**Notes:**
- O(1) amortized via the `ConditionalWeakTable`; entries whose key was collected are automatically absent.

#### `WeakCache<TTargetKey,TCacheKey>.Remove`

**Signature:**
`public void Remove(TTargetKey target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `TTargetKey` | The weak key to remove. |

**Returns:** `void`

**Notes:**
- Removes the table entry and any matching sweep-list reference; removing a non-existent key is a no-op (verified by `WeakCacheTests.Remove_NonExistent_NoException`).

#### `WeakCache<TTargetKey,TCacheKey>.ForeachCache`

**Signature:**
`public void ForeachCache(Action<TTargetKey, TCacheKey> action)`

| Parameter | Type | Description |
|---|---|---|
| `action` | `Action<TTargetKey, TCacheKey>` | A callback invoked for each live entry. |

**Returns:** `void`

**Notes:**
- Prunes collected targets from the sweep list first, then iterates the survivors (verified by `WeakCacheTests.ForeachCache_IteratesAllEntries`).
