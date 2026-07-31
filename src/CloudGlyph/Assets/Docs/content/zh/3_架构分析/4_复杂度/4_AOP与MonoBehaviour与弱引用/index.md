# 复杂度分析 — AOP、MonoBehaviour 与弱引用

## AOP

### 钩子查找

$$O(1)$$

`ProxyInstance.Invoke` 用 `Dictionary<string, Tuple<...>>` 按键（成员名）解析钩子三元组（`GetterActions` / `SetterActions` / `MethodActions`）。字典访问摊还 $O(1)$；成员名已由生成的代理归一化（`get_*` / `set_*` 前缀）。

### DispatchProxy 调用

$$O(1) \text{ 每次调用, } + O(h) \text{ 个钩子处理器}$$

每次被拦截调用要付出常量级的分发 + 查找开销，再加上 $O(h)$ 个活动钩子，其中 $h \le 3$（start、coverage/end）。因此一个完整包裹的成员代价为：

$$T_{\text{intercept}} = O(1) + O(h), \quad h \le 3$$

### 反射回退路径

当 `coverage == null` 时，`Invoke` 对真实目标做反射：

```csharp
_targetType?.GetMethod(Name)?.Invoke(_target, args)
```

`GetMethod(string)` 是对类型元数据的线性扫描，`MethodInfo.Invoke` 会对参数装箱：

$$O(m) \text{ 查找 } + O(a) \text{ 调用, } \quad m = \text{类型中的成员数}, \ a = \text{实参个数}$$

因此反射回退严格比 coverage 处理器更贵。*该代价刻画由 `ProxyInstance.cs` 第 33 行的 `GetMethod` / `Invoke` 用法推断，算法属于标准 BCL 行为。*

### 代理缓存

$$O(1) \text{ 摊还每次 } \text{Aop()}$$

`AopCache.Resolve` 是一次 `ConditionalWeakTable.GetValue` —— 摊还 $O(1)$；代理每个目标只创建一次，随目标一起回收。

## MonoBehaviour

### 每帧 Update

$$O(b), \quad b = \text{活动行为数}$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` 对缓存的包装器数组遍历一次，逐个调用 `InvokeUpdate` / `InvokeLateUpdate`（当 `e.Handled == true` 或令牌取消时提前停止）—— `MonoBehaviourManager.cs` 第 610-640 行。数组只在增删行为时或每 `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms 重建一次，因此每帧排序代价被摊还掉。

按目标帧率：

$$T_{\text{update}} = O(b) \text{ 每帧, } \quad \frac{1}{FPS} \le 1000 \text{ ms}, \ FPS \in [1, 1000]$$

### FixedUpdate

$$O(b) \text{ 每约 16 ms}$$

`ExecuteBehaviorsFixedUpdateSync` 在固定线程上按 `SetFixedUpdateInterval` ms（默认 `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`）运行，因此稳态代价是不论帧率如何，每 16 ms 为 $O(b)$。

### 帧节奏控制

睡眠使用 `PrecisionSleep`（低于 `SPIN_ONLY_THRESHOLD_MS = 2` ms 纯自旋，否则 `Thread.Sleep(1)` + 尾部自旋）—— `MonoBehaviourManager.cs` 第 777-802 行。每帧墙钟时间 $O(1)$。

## 弱引用

### WeakQueue / WeakStack

$$\text{Enqueue / Push: } O(1), \quad \text{TryDequeue / TryPop: } O(1) \text{ 摊还}$$

每次变更都是对 `WeakReference<T>` 的加锁 `Queue` / `Stack` 操作。`TryDequeue` / `TryPop` 循环跳过已回收引用：

$$O(1 + d) \text{ 摊还}, \quad d = \text{队头 / 栈顶的死亡引用数}$$

`Count`、`GetEnumerator` 与 `TrimExcess` 会先剪除整个结构：

$$O(n), \quad n = \text{存储的引用数}$$

因此 `Count` / 枚举的最坏情况是 $O(n)$，而常见变更路径保持摊还 $O(1)$。

### WeakCache

$$O(1) \text{ 摊还}$$

`AddOrUpdate` / `TryGetCache` / `Remove` 是 `ConditionalWeakTable` 操作外加一次列表插入 / 扫描。清理是周期性的，当插入计数超过自适应阈值（`_perceptionThreshold = 4`，每次清扫翻倍 —— `WeakCache.cs` 第 12、44-62 行）时触发：

$$\text{清扫: } O(n) \text{ 最坏, } \quad \text{每次插入摊还 } O(1)$$

### 内存

| 结构 | 行为 |
|---|---|
| `ProxyInstance` 钩子 | $O(\text{成员数})$ 字典；代理位于 `ConditionalWeakTable` → 随目标回收 |
| `WeakDelegate` | $O(h)$ 个 `WeakReference<Delegate>`；**不保留**对订阅者的强引用 |
| `WeakQueue` / `WeakStack` | $O(n)$ 个弱引用；访问时剪除死引用，条目不生根对象 |
| `WeakCache` | `ConditionalWeakTable` + $O(n)$ 清扫列表；键不会让值一直存活 |

核心性质是**弱引用避免保留**：订阅者、队列项或缓存键一旦在其他地方不可达即可被回收——这正是这些类型存在的意义。

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| AOP 钩子查找 | $O(1)$ |
| AOP 被拦截调用 | $O(1) + O(h)$，$h \le 3$ |
| AOP 反射回退 | $O(m) + O(a)$ |
| `Aop()` 代理解析 | 摊还 $O(1)$ |
| MonoBehaviour Update（每帧） | $O(b)$ |
| MonoBehaviour FixedUpdate | 每约 16 ms $O(b)$ |
| `WeakQueue.Enqueue` / `WeakStack.Push` | $O(1)$ |
| `WeakQueue.TryDequeue` / `WeakStack.TryPop` | 摊还 $O(1)$ |
| `WeakQueue.Count` / 枚举 | 最坏 $O(n)$（剪除） |
| `WeakCache.AddOrUpdate` / `TryGetCache` | 摊还 $O(1)$ |
| `WeakCache` 周期清扫 | 最坏 $O(n)$ |
