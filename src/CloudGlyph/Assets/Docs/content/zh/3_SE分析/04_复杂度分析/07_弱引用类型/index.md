# 复杂度分析 — 弱引用类型

三类弱容器的成本模型一致：**摊还 O(1) 的热路径**外加**偶发 O(n) 清扫**，回收已回收对象的空包装。此处每个操作都受 `lock (_lock)` 保护，因此这些是单线程摊还界，在争用下也按每个锁区间成立。

## WeakQueue / WeakStack

变更是对 `WeakReference<T>` 的加锁 `Queue`/`Stack` 压入/弹出：

$$
\text{Enqueue / Push: } O(1), \qquad \text{TryDequeue / TryPop / TryPeek: } O(1 + d) \text{ 摊还}
$$

其中 $d$ = 队头 / 栈顶的死亡引用数。`TryDequeue`/`TryPop`/`TryPeek` 弹出并丢弃死亡包装，直到抵达存活条目（或为空）；每个死亡包装在其生命周期内恰好被丢弃一次，因此跳过死亡条目的累计代价摊还到每个新增条目为 O(1)。`Count`、`GetEnumerator` 与 `TrimExcess` 会先压缩整个结构（`Prune()`，`WeakQueue.cs` 第 124-135 行；`WeakStack.cs` 第 124-136 行，后者还会反转以保证 LIFO 顺序）：

$$
O(n), \quad n = \text{存储的引用包装数}
$$

| 操作 | 复杂度 |
|---|---|
| `Enqueue` / `Push` | $O(1)$ |
| `EnqueueRange` / `PushRange` | $O(k)$，$k$ = 输入大小（`PushRange` 另加 $O(k)$ 的 `Reverse`，使条目在栈上保持原有顺序） |
| `TryDequeue` / `TryPop` / `TryPeek` | 摊还 $O(1 + d)$ |
| `Count` / `GetEnumerator` / `TrimExcess` | 最坏 $O(n)$（先剪除） |
| `Clear` | $O(n)$ — BCL 的 `Queue`/`Stack` 会把每个存储槽置空以释放包装 |

**内存。** 容器持有 $O(n)$ 个 `WeakReference<T>` 包装且绝不扎根载荷，因此载荷一旦不再被其它强引用持有即可被回收。两次清扫之间容器可能保留已被回收载荷的空包装（垃圾槽位），但每次 `Count`/枚举/`TrimExcess` 都会压缩、每次弹出都会跳过它们，故浪费的空间是暂时的，且受存活工作集限制。

## WeakCache

`AddOrUpdate` / `TryGetCache` / `Remove` 是 `ConditionalWeakTable` 操作外加一次列表扫描，因此查找与插入摊还 O(1)。清理是周期性的，当插入计数超过**自适应**阈值（`_perceptionThreshold`，默认 `4`）时触发：

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs（第 75-79 行）
private static int GetNextCleanupThreshold(int currentCount)
{
    int nextCapacity = currentCount == 0 ? 4 : currentCount * 2;
    return (int)(nextCapacity * 0.9);
}
```

清扫阈值按存活数几何增长，因此每次插入的摊还代价保持恒定：

$$
\text{清扫: } O(n) \text{ 最坏}, \qquad \text{每次插入摊还 } O(1)
$$

| 操作 | 复杂度 |
|---|---|
| `AddOrUpdate` | 摊还 $O(1)$（偶发对追踪列表的 $O(n)$ 清扫） |
| `TryGetCache` | 摊还 $O(1)$（表读取；键的存活与否不改变代价） |
| `Remove` | 表移除 $O(1)$ + 追踪列表扫描 $O(n)$ |
| `ForeachCache` | $O(n)$（剪除追踪列表 + 经表遍历存活键） |

**内存。** `ConditionalWeakTable` 是真源：它弱引用每个目标键，且仅在键存活期间强引用值，因此缓存只持有 $O(n_{\text{live}})$ 个存活条目，绝不扎根死亡键的值——淘汰自动且精确，无泄漏窗口。追踪列表额外提供 $O(m)$ 个弱引用（$m \ge n_{\text{live}}$，由清扫清理），纯粹用于枚举与去重追踪；它从不参与查找，也从不扎根键。

## WeakDelegate

热路径是单次 `volatile` 字段读取，这正是过渡引擎每帧调用无锁的原因：

$$
O(1) \text{ — 读取已缓存组合委托，然后类型化或经 DynamicInvoke 调用}
$$

重建多播缓存需要对处理器列表做一次遍历：`RebuildCache` 运行 `CleanupCollectedHandlers`（$O(h)$）再对每个存活处理器 `Delegate.Combine`（$O(h)$），其中 $h$ = 存储的处理器包装数。

| 操作 | 复杂度 |
|---|---|
| `AddHandler`（`CanUpdateCache: true`） | 追加 $O(1)$ + 重建 $O(h)$ |
| `AddHandler`（`CanUpdateCache: false`） | $O(1)$ |
| `RemoveHandler` | 扫描/移除 $O(h)$（如请求则另加 $O(h)$ 重建） |
| `GetInvocationList`（缓存命中） | $O(1)$，无锁 |
| `GetInvocationList`（缓存未命中） | 加锁重建 $O(h)$ |
| `Invoke(object?[] objects)` | 读取 $O(1)$ + DynamicInvoke 分发开销 |
| `Clone` | $O(h)$（复制存活处理器 + 重建） |

**内存。** `_handlers` 是 $O(h)$ 个 `WeakReference<Delegate>` 包装外加一个缓存的组合委托。组合委托是对上次重建以来每个已添加处理器的**强**引用——整个功能里唯一的强引用——因此未退订处理器只会在某次重建将其排除时被释放（`CleanupCollectedHandlers` 丢弃死亡包装）。以 `CanUpdateCache: false` 添加的处理器从不进入缓存，是真正弱的。

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | 摊还 $O(1)$ |
| `WeakQueue.Count` / 枚举 | 最坏 $O(n)$（剪除） |
| `WeakCache.AddOrUpdate` / `TryGetCache` | 摊还 $O(1)$ |
| `WeakCache` 周期清扫 | 最坏 $O(n)$，摊还 $O(1)$ |
| `WeakDelegate.GetInvocationList`（热路径） | $O(1)$，无锁 |
| `WeakDelegate` 增/删/克隆 | 重建 $O(h)$ |
| 内存增长 | 载荷从不被扎根（`WeakDelegate` 重建后的组合委托除外）；空包装访问时即被回收，因此死亡条目不会永久占用内存 |
