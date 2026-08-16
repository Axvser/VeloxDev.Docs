# 复杂度分析 — 弱引用类型

## WeakQueue / WeakStack

$$\text{Enqueue / Push: } O(1), \quad \text{TryDequeue / TryPop: } O(1) \text{ 摊还}$$

每次变更都是对 `WeakReference<T>` 的加锁 `Queue` / `Stack` 操作。`TryDequeue` / `TryPop` / `TryPeek` 循环跳过已回收引用：

$$O(1 + d) \text{ 摊还}, \quad d = \text{队头 / 栈顶的死亡引用数}$$

`Count`、`GetEnumerator` 与 `TrimExcess` 会先剪除整个结构（`Prune()`，`WeakQueue.cs` 第 124-135 行 / `WeakStack.cs` 第 124-136 行）：

$$O(n), \quad n = \text{存储的引用数}$$

因此 `Count` / 枚举的最坏情况是 $O(n)$，而常见变更路径保持摊还 $O(1)$。

| 操作 | 复杂度 |
|---|---|
| `Enqueue` / `Push` | $O(1)$ |
| `EnqueueRange` / `PushRange` | $O(k)$，$k$ = 输入大小（栈另加 $O(k)$ 反转） |
| `TryDequeue` / `TryPop` / `TryPeek` | 摊还 $O(1 + d)$ |
| `Count` / `GetEnumerator` / `TrimExcess` | 最坏 $O(n)$（先剪除） |
| `Clear` | $O(1)$（清空容器） |

## WeakCache

$$O(1) \text{ 摊还}$$

`AddOrUpdate` / `TryGetCache` / `Remove` 是 `ConditionalWeakTable` 操作外加一次列表插入 / 扫描。清理是周期性的，当插入计数超过**自适应**阈值（`_perceptionThreshold`，默认 `4`）时触发：

```csharp
// Src/Core/VeloxDev.Core/WeakTypes/WeakCache.cs（第 75-79 行）
private static int GetNextCleanupThreshold(int currentCount)
{
    int nextCapacity = currentCount == 0 ? 4 : currentCount * 2;
    return (int)(nextCapacity * 0.9);
}
```

清扫会按几何级数增长阈值，因此每次插入的摊还代价保持恒定：

$$\text{清扫: } O(n) \text{ 最坏}, \quad \text{每次插入摊还 } O(1)$$

| 操作 | 复杂度 |
|---|---|
| `AddOrUpdate` | 摊还 $O(1)$（偶发 $O(n)$ 清扫） |
| `TryGetCache` | 摊还 $O(1)$ |
| `Remove` | 表移除 $O(1)$ + 清扫列表扫描 $O(n)$ |
| `ForeachCache` | $O(n)$（剪除 + 遍历存活条目） |

## 内存

| 结构 | 行为 |
|---|---|
| `WeakDelegate` | $O(h)$ 个 `WeakReference<Delegate>` + 一个缓存组合委托；缓存未构建时**不保留**对订阅者的强引用 |
| `WeakQueue` / `WeakStack` | $O(n)$ 个弱引用；访问时剪除死亡引用；条目不生根对象 |
| `WeakCache` | `ConditionalWeakTable` + $O(n)$ 清扫列表；键一旦不可达，条目自动从表中移除 |

核心性质是**弱引用避免保留**：订阅者、队列项或缓存键一旦在其他地方不可达即可被回收——这正是这些类型存在的意义。唯一的强引用是 `WeakDelegate` 缓存的组合委托，它会在下次 `AddHandler` / `RemoveHandler` / `Clone` / 缓存为 null 的 `GetInvocationList` 时重建（并剪除）。

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | 摊还 $O(1)$ |
| `WeakQueue.Count` / 枚举 | 最坏 $O(n)$（剪除） |
| `WeakCache.AddOrUpdate` / `TryGetCache` | 摊还 $O(1)$ |
| `WeakCache` 周期清扫 | 最坏 $O(n)$ |
| 内存增长 | 死亡条目不会永久占用内存 —— 访问时即被剪除 |
