# 注册表、快照与池化

三个结构限定了本特性的内存，并让热路径保持零分配。

设 $C$ 为进程中创建的通道数，$N$ 为一个通道上的行为数，$K$ 为池容量（`DEFAULT_OBJECT_POOL_SIZE` = 50）。

## 通道注册表

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 1019-1032 行）
private static readonly ConcurrentDictionary<string, LoopChannel> _channels = new();

private static LoopChannel GetOrCreateChannel(string name)
{
    return _channels.GetOrAdd(name, n =>
    {
        var ch = new LoopChannel(n);
        // …四个事件转发器…
        return ch;
    });
}
```

| 操作 | 期望时间 | 空间 |
|---|---|---|
| `GetOrCreateChannel`（名字已存在） | $O(1)$ 哈希探测 | — |
| `GetOrCreateChannel`（新名字） | $O(1)$ + 通道构造 | 每通道 $O(1)$ |
| 状态查询（`IsRunning`、`Bus` 等） | $O(1)$ `TryGetValue` | — |
| `ChannelNames` | 枚举 $O(C)$ | — |

字典读路径无锁，这很重要，因为示例里状态查询按显示频率运行：`MainWindow.xaml.cs` 每 33 ms 轮询它们。注册表从不修剪，所以空间是 $O(C)$，且 $C$ 只增不减 —— 具名通道是进程生命周期的对象。

通道构造是 `GetOrCreateChannel` 中唯一昂贵的部分，每个名字发生一次：`TimerCore.CreateTimeSource<ITimeSourceControl>()` 加两个采样器、`LoopChannel` 构造函数据中的三个 `ObjectPool` 实例（`_frameEventArgsPool`、`_configRequestPool`、`_wrapperPool`，声明在第 154-156 行；构造函数在 162-169 行）、一个 `CancellationTokenSource`，以及四个委托订阅。

## 写时复制快照

| 操作 | 时间 | 空间 |
|---|---|---|
| `GetCachedWrappers` 命中 | $O(1)$ | — |
| `RebuildCachedWrappers` —— 填充 | $O(N)$ | $O(N)$ 新数组 |
| `RebuildCachedWrappers` —— 插入排序 | 已有序时 $O(N)$，最坏 $O(N^2)$ | $O(1)$ |
| `RebuildCachedWrappers` —— `Array.Resize` 缩短 | $O(N)$ 拷贝，仅在跳过某些 wrapper 时 | $O(N)$ |
| 派发扫描读取 | $O(1)$ —— 一次 `volatile` 数组引用 | — |

排序是本特性唯一的超线性项，而且被有意限制住：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 886-897 行）
// Insertion sort — behavior counts are usually small, avoiding LINQ allocations
for (int i = 1; i < idx; i++)
{
    var key = arr[i];
    int j = i - 1;
    while (j >= 0 && arr[j].ExecutionOrder > key.ExecutionOrder)
    {
        arr[j + 1] = arr[j];
        j--;
    }
    arr[j + 1] = key;
}
```

输入几乎总是已经有序：`ExecutionOrder` 是 `Interlocked.Increment(ref _instanceCounter)`，所以数组按构造就有序，并按字典枚举顺序重建。插入排序在有序数组上的最好情况是 $O(N)$、每元素一次比较，它的成本在无分配的内层循环而不是比较委托。$N$ 在个位数时，$O(N^2)$ 最坏情况也就是几十次比较。

重建的均摊值得一提：除非 `_wrappersNeedSort` 被置位，它最多每 `MAX_CONFIG_CACHE_DURATION_MS`（1 秒）运行一次；该标志只由新增或移除排空置起。所以每次注册的代价是一次重建，而不是每帧一次重建。

## 三个池

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 76-94 行）
[MethodImpl(MethodImplOptions.AggressiveInlining)]
public T Get()
{
    if (_pool.TryPop(out var item))
    {
        Interlocked.Decrement(ref _count);
        return item;
    }
    return new T();
}

[MethodImpl(MethodImplOptions.AggressiveInlining)]
public void Return(T item)
{
    if (Interlocked.Increment(ref _count) <= maxSize)
        _pool.Push(item);
    else
        Interlocked.Decrement(ref _count);
}
```

| 操作 | 时间 | 空间 | 说明 |
|---|---|---|---|
| `Get`（命中） | $O(1)$ | — | `ConcurrentStack.TryPop` |
| `Get`（未命中） | $O(1)$ | 一次分配 | 不阻塞、无等待队列 |
| `Return`（未超上限） | $O(1)$ | — | |
| `Return`（超上限） | $O(1)$ | 对象变成垃圾 | 突发下池会收缩而不是无限增长 |

占用计数器是用 `Interlocked` 维护的 `int`，不是 `_pool.Count` —— 读取 `ConcurrentStack<T>.Count` 是 $O(n)$，而它在每次 `Return` 时都被读。

池占用随时间同时受 churn 与上限约束：

$$
\text{occupancy} \le \min(K,\ \text{peak concurrent demand}), \qquad K = 50
$$

每通道稳态需求很小且已知：

| 池 | 同时存活的对象 |
|---|---|
| `_frameEventArgsPool` | 1 个 update 帧参数 + 追赶批次中最多 `MaxStepsPerCall`（8）个 fixed 步参数 |
| `_configRequestPool` | 稳态 0 个；每次帧率变更 1 个，直到下次排空 |
| `_wrapperPool` | 每个已注册行为 1 个，即 $O(N)$ |

三个通道、若干行为时，池化内存总共是几百个小对象，不随帧率或运行时长增长。

## 总空间

$$
S = O(C) + O(C \cdot (\text{samplers} + \text{bus} + \text{pools})) + O(N) + O(K)
$$

具体到每通道：两个采样器、一个时间源、三个最多各 50 元素的池、四个队列（稳态为空）、一个 `CancellationTokenSource`、两个线程（异步模式下为零），以及行为字典与其快照。这个清单里没有任何东西随帧率增长，也没有任何东西随时间增长 —— 运行一周的通道持有的对象与运行一秒后完全相同。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 71-95、154-156、162-169、743-753、874-903、1019-1032 行；`Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs` 第 24-30 行。
