# Weak Types — `WeakCache`

通过 `ConditionalWeakTable<TTargetKey, TCacheKey>` 加 `List<WeakReference<TTargetKey>>` 清扫列表，把弱键映射到缓存值。

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

**签名：**
`public void AddOrUpdate(TTargetKey target, TCacheKey cache)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 弱键。 |
| `cache` | `TCacheKey` | 要存储的值。 |

**返回：** `void`

**说明：**
- 对同一 target 覆盖已有条目。当插入计数器超过 `_perceptionThreshold`（自适应，默认 `4`）时，清扫移除已回收目标并增长阈值（`GetNextCleanupThreshold` ≈ `0.9 * 下一个容量`）。由 `WeakCacheTests.AddOrUpdate_*` 验证。

#### `WeakCache<TTargetKey,TCacheKey>.TryGetCache`

**签名：**
`public bool TryGetCache(TTargetKey target, out TCacheKey? cache)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 弱键。 |
| `cache` | `TCacheKey?` | 存储的值，或 `null`。 |

**返回：** `bool` — 键存在并取到值为 `true`。

**说明：**
- 经 `ConditionalWeakTable` 摊还 O(1)；键已被回收的条目会自动缺失。

#### `WeakCache<TTargetKey,TCacheKey>.Remove`

**签名：**
`public void Remove(TTargetKey target)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 要移除的弱键。 |

**返回：** `void`

**说明：**
- 移除表条目与清扫列表中任何匹配引用；移除不存在的键是无操作（由 `WeakCacheTests.Remove_NonExistent_NoException` 验证）。

#### `WeakCache<TTargetKey,TCacheKey>.ForeachCache`

**签名：**
`public void ForeachCache(Action<TTargetKey, TCacheKey> action)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `action` | `Action<TTargetKey, TCacheKey>` | 对每个存活条目调用的回调。 |

**返回：** `void`

**说明：**
- 先从清扫列表移除已回收目标，再遍历幸存者（由 `WeakCacheTests.ForeachCache_IteratesAllEntries` 验证）。
