# 弱引用类型 — `WeakCache<TTargetKey, TCacheKey>`

命名空间 `VeloxDev.WeakTypes`。一个 sealed 缓存，把值绑定到*弱*目标键上：映射存放在 `ConditionalWeakTable<TTargetKey, TCacheKey>` 中（辅以 `WeakReference<TTargetKey>` 的清扫列表），因此缓存不会 root 住它的键 —— 一旦目标不再被其它对象引用，它就会被回收，对应条目自动消失。

```csharp
public sealed class WeakCache<TTargetKey, TCacheKey>
    where TTargetKey : class
    where TCacheKey : class
```

两个类型参数都必须是引用类型。`ConditionalWeakTable` 把键当作类 ephemeron 处理：只要 `TTargetKey` 目标存活，所存的 `TCacheKey` 值就存活；目标被回收时两者一起消亡。所有方法都在内部锁上同步。

## 字段

### `WeakCache<TTargetKey,TCacheKey>._perceptionThreshold`

**签名：**
`public int _perceptionThreshold = 4;`

**类型：** `int`

**说明：**
- 一个 public、可变的字段（名字与源码完全一致），决定允许累积多少次插入后再由 `AddOrUpdate` 触发一次清扫。
- `AddOrUpdate` 在内部计数器超过该值后清扫：从清扫列表移除已回收目标、把计数器归 `0`，再按剩余目标数重新推导阈值（`GetNextCleanupThreshold` —— 约为 `0.9 × 2 × count`；无目标剩余时回到 `4`）。因此该字段既是一个可调旋钮，也是一个自适应水位。
- 默认 `4`。与清扫行为一起由 `WeakCacheTests.AddOrUpdate_ManyItems_TriggersCleanup` 验证。

## 方法

### `WeakCache<TTargetKey,TCacheKey>.AddOrUpdate`

**签名：**
`public void AddOrUpdate(TTargetKey target, TCacheKey cache)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 绑定值的弱键。 |
| `cache` | `TCacheKey` | 为 `target` 存储的值。 |

**返回：** `void`

**说明：**
- 若 `target` 已有条目，会先移除再重新加入，因此存储值被覆盖 —— 由 `WeakCacheTests.AddOrUpdate_OverwritesExisting` 与 `AddOrUpdate_And_TryGetCache_ReturnsValue` 验证。
- 同时把 `target` 记入弱清扫列表，以便枚举与清扫能找到它；插入时的清扫时机见 `_perceptionThreshold`。
- 在内部锁内执行。

### `WeakCache<TTargetKey,TCacheKey>.TryGetCache`

**签名：**
`public bool TryGetCache(TTargetKey target, out TCacheKey? cache)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 要查找的键。 |
| `cache` | `TCacheKey?` | 方法返回 `true` 时的存储值；否则为 `null`。 |

**返回：** `bool` — `target` 当前存在条目为 `true`。

**说明：**
- 因为条目随键一起消亡，已被回收的键直接返回 `false` —— 由 `WeakCacheTests.TryGetCache_Missing_ReturnsFalse` 验证。
- 在内部锁内执行。

### `WeakCache<TTargetKey,TCacheKey>.Remove`

**签名：**
`public void Remove(TTargetKey target)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `TTargetKey` | 要移除条目的键。 |

**返回：** `void`

**说明：**
- 移除表条目及清扫列表中任何匹配的引用。
- 移除没有条目的键是无操作 —— 由 `WeakCacheTests.Remove_DeletesEntry` 与 `Remove_NonExistent_NoException` 验证。

### `WeakCache<TTargetKey,TCacheKey>.ForeachCache`

**签名：**
`public void ForeachCache(Action<TTargetKey, TCacheKey> action)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `action` | `Action<TTargetKey, TCacheKey>` | 对每个存活条目以（目标、值）为参调用一次的回调。 |

**返回：** `void`

**说明：**
- 先从清扫列表移除已回收目标，再遍历剩余存活目标，对每个仍保有表条目的目标调用 `action` —— 由 `WeakCacheTests.ForeachCache_IteratesAllEntries` 验证。
- 在内部锁内执行。

## 源文件

`Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs`
