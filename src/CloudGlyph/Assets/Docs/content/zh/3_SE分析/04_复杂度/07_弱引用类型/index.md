# 复杂度分析 — 弱引用类型

三种弱容器形态共享同一成本模型：**摊销 O(1) 热路径**，加上偶尔的 **O(n) 清扫**以回收已回收对象的空包装。这里每个操作都受锁保护（`lock (_lock)`），因此这些是单线程摊销上界，在竞争下对每个锁区段同样成立。

## 弱队列 / 弱栈

变更操作是受锁保护的 `Queue`/`Stack` 对 `WeakReference<T>` 的无操作 push/pop：

$$
\text{Enqueue / Push: } O(1), \qquad \text{TryDequeue / TryPop / TryPeek: } O(1 + d) \text{ amortized}
$$

其中 $d$ = 队首/栈顶的死引用数。`TryDequeue`/`TryPop`/`TryPeek` 弹出并丢弃死包装，直到遇到存活条目（或为空），因此每个死包装在其生命周期内恰好被丢弃一次——跳过死条目的累计成本按每个添加条目摊销为 O(1)。`Count`、`GetEnumerator` 与 `TrimExcess` 先压缩整个结构（`Prune()`，`WeakQueue.cs` 第 137-148 行；`WeakStack.cs` 第 137-149 行，后者还会反转以保持 LIFO 顺序）：

$$
O(n), \quad n = \text{stored reference wrappers}
$$

| 操作 | 复杂度 |
|---|---|
| `Enqueue` / `Push` | $O(1)$ |
| `EnqueueRange` / `PushRange` | $O(k)$，$k$ = 输入大小（$PushRange$ 额外做一次 $O(k)$ 的 `Reverse`，使条目在栈上保持顺序） |
| `TryDequeue` / `TryPop` / `TryPeek` | 摊销 $O(1 + d)$ |
| `Count` / `GetEnumerator` / `TrimExcess` | 最坏 $O(n)$（先剪除） |
| `Clear` | $O(n)$——BCL 的 `Queue`/`Stack` 会把每个存储槽置空以释放包装 |

**内存。** 容器持有 $O(n)$ 个 `WeakReference<T>` 包装，且从不 root 载荷，因此只要没有其它强引用，载荷就可回收。两次清扫之间容器可能为已回收载荷保留空包装（垃圾槽位）；其数量以“上次 `Prune()` 以来新增的条目数”为界，而每次 `Count`/枚举/`TrimExcess` 都会压缩它们，弹出操作也会跳过它们。如果集合只被写入，死包装会一直累积，直到上述某次读取发生。

## 弱缓存

`AddOrUpdate` / `TryGetCache` / `Remove` 是 `ConditionalWeakTable` 操作加一次列表扫描，因此查找与插入是摊销 O(1)。清理是周期性的，在插入计数器超过**自适应**阈值（`_perceptionThreshold`，默认 `4`）时触发：

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs (lines 100-104)
private static int GetNextCleanupThreshold(int currentCount)
{
    int nextCapacity = currentCount == 0 ? 4 : currentCount * 2;
    return (int)(nextCapacity * 0.9);
}
```

清扫阈值随存活数几何增长，因此每次插入的摊销成本保持常数：

$$
\text{sweep: } O(n) \text{ worst-case}, \qquad \text{amortized } O(1) \text{ per insert}
$$

| 操作 | 复杂度 |
|---|---|
| `AddOrUpdate` | 摊销 $O(1)$（偶发 $O(n)$ 的记账列表清扫） |
| `TryGetCache` | 摊销 $O(1)$（表读取；键是否存活不改变成本） |
| `Remove` | $O(1)$ 表移除 + $O(n)$ 记账列表扫描 |
| `ForeachCache` | $O(n)$（剪除记账列表 + 让存活键逐个查表） |

**内存。** `ConditionalWeakTable` 是事实源：它弱引用每个目标键，并且只在键存活时强引用值，因此缓存持有 $O(n_{\text{live}})$ 个存活条目，且从不 root 死键的值——驱逐自动且精确，没有泄漏窗口。记账列表额外增加 $O(m)$ 个弱引用（$m \ge n_{\text{live}}$，由清扫清理），纯粹用于支持枚举与重复跟踪；它从不参与查找，也从不 root 键。

## 弱委托

热路径是一次 `volatile` 字段读取，因此过渡引擎的每帧调用是无锁的：

$$
O(1) \text{ — cached combined delegate is read, then invoked typed or via DynamicInvoke}
$$

重建多播缓存需要对处理器列表做一次遍历：`RebuildCache` 运行 `CleanupCollectedHandlers`（$O(h)$），再对每个存活处理器执行 `Delegate.Combine`（$O(h)$），其中 $h$ = 存储的处理器包装数。

| 操作 | 复杂度 |
|---|---|
| `AddHandler`（`CanUpdateCache: true`） | $O(1)$ 追加 + $O(h)$ 重建 |
| `AddHandler`（`CanUpdateCache: false`） | $O(1)$ |
| `RemoveHandler` | $O(h)$ 扫描；使用默认 `CanUpdateCache: true` 时每个匹配项触发一次 $O(h)$ 重建（$k$ 个重复匹配则为 $O(k \cdot h)$） |
| `GetInvocationList`（缓存命中） | $O(1)$，无锁 |
| `GetInvocationList`（缓存未命中） | 锁内 $O(h)$ 重建 |
| `Invoke(object?[] objects)` | $O(1)$ 读取 + DynamicInvoke 分派成本 |
| `Clone` | $O(h)$（复制存活处理器 + 重建） |

**内存。** `_handlers` 是 $O(h)$ 个 `WeakReference<Delegate>` 包装，外加一个缓存的组合委托。组合委托是对自上次重建以来每个处理器的**强引用**——整个功能中唯一的强引用——因此已退订处理器只会在重建把它们排除时才被释放（`CleanupCollectedHandlers` 丢弃死包装）。以 `CanUpdateCache: false` 添加的处理器从不进入缓存，是真正弱的。

## 逐操作汇总

| 操作 | 复杂度 |
|---|---|
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | 摊销 $O(1)$ |
| `WeakQueue.Count` / 枚举 | 最坏 $O(n)$（先剪除） |
| `WeakCache.AddOrUpdate` / `TryGetCache` | 摊销 $O(1)$ |
| `WeakCache` 周期清扫 | 最坏 $O(n)$，摊销 $O(1)$ |
| `WeakDelegate.GetInvocationList`（热路径） | $O(1)$，无锁 |
| `WeakDelegate` add/remove/clone | $O(h)$ 重建 |
| 内存增长 | 载荷从不被 root（`WeakDelegate` 重建的组合委托除外）；空包装在访问时回收，因此死条目不会永久增长内存 |
