# 注册表、快照与对象池

约束本特性内存、并让热路径零分配的三个结构。

设 $C$ 为进程中创建过的通道数，$N$ 为单通道上的行为数，$K$ 为池容量（`DEFAULT_OBJECT_POOL_SIZE` = 50）。

## 通道注册表

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（1017-1030 行）
private static readonly ConcurrentDictionary<string, LoopChannel> _channels = new();

private static LoopChannel GetOrCreateChannel(string name)
{
    return _channels.GetOrAdd(name, n =>
    {
        var ch = new LoopChannel(n);
        // ……四个事件转发器……
        return ch;
    });
}
```

| 操作 | 期望时间 | 空间 |
|---|---|---|
| `GetOrCreateChannel`（名字已存在） | $O(1)$ 哈希探测 | — |
| `GetOrCreateChannel`（新名字） | $O(1)$ 加通道构造 | 每通道 $O(1)$ |
| 状态查询（`IsRunning`、`Bus` 等） | $O(1)$ `TryGetValue` | — |
| `ChannelNames` | $O(C)$ 枚举 | — |

字典的读路径无锁，这很重要，因为状态查询在演示里按显示频率运行：`MainWindow.xaml.cs` 每 33 ms 轮询全部十三个。注册表从不裁剪，所以它的空间是 $O(C)$ 且 $C$ 只增 —— 一个具名通道就是一个进程生命周期的对象。

通道构造是 `GetOrCreateChannel` 里唯一昂贵的部分，且每个名字只发生一次：`TimerCore.CreateTimeSource<ITimeSourceControl>()` 加两个采样器、`LoopChannel` 构造函数里的三个 `ObjectPool` 实例（`_frameEventArgsPool`、`_configRequestPool`、`_wrapperPool`，声明于 152-154 行；构造函数在 160-167 行）、一个 `CancellationTokenSource`，以及四个委托订阅。

## 写时复制快照

| 操作 | 时间 | 空间 |
|---|---|---|
| `GetCachedWrappers` 命中 | $O(1)$ | — |
| `RebuildCachedWrappers` —— 填充 | $O(N)$ | $O(N)$ 新数组 |
| `RebuildCachedWrappers` —— 插入排序 | 已有序时 $O(N)$，最坏 $O(N^2)$ | $O(1)$ |
| `RebuildCachedWrappers` —— `Array.Resize` 缩小 | $O(N)$ 拷贝，仅当有包装器被跳过 | $O(N)$ |
| 派发趟读取 | $O(1)$ —— 一次 `volatile` 数组引用 | — |

排序是本特性里唯一的超线性项，并且是被刻意圈住的：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（883-894 行）
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

输入几乎总是已经有序：`ExecutionOrder` 是 `Interlocked.Increment(ref _instanceCounter)`，所以数组按构造就有序，并按字典枚举顺序重建。插入排序在有序数组上的最佳情况是每个元素一次比较、总 $O(N)$，它的成本优势来自无分配的内层循环而不是比较委托。$N$ 在个位数时，最坏 $O(N^2)$ 也就是几十次比较。

重建的摊还值得说清：除非 `_wrappersNeedSort` 被置位，它每个 `MAX_CONFIG_CACHE_DURATION_MS`（1 秒）最多运行一次；而该标志只由新增或移除的排空过程置位。所以每次注册的代价是一次重建，而不是每帧一次重建。

## 三个对象池

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（74-92 行）
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

| 操作 | 时间 | 空间 | 备注 |
|---|---|---|---|
| `Get`（命中） | $O(1)$ | — | `ConcurrentStack.TryPop` |
| `Get`（未命中） | $O(1)$ | 一次分配 | 不阻塞，无等待队列 |
| `Return`（未超上限） | $O(1)$ | — | |
| `Return`（超上限） | $O(1)$ | 该对象变成垃圾 | 池在突发下收缩而不是无界增长 |

占用计数是 `int` 加 `Interlocked` 维护的，不是 `_pool.Count` —— 读 `ConcurrentStack<T>.Count` 是 $O(n)$，而它在每次 `Return` 时都会被读。

池占用随时间被流入量与上限同时约束：

$$
\text{占用} \le \min(K,\ \text{峰值并发需求}), \qquad K = 50
$$

每通道的稳态需求很小且已知：

| 池 | 同时存活的对象数 |
|---|---|
| `_frameEventArgsPool` | 1 个 update 帧参数 + 补还批次期间最多 `MaxStepsPerCall`（8）个固定步参数 |
| `_configRequestPool` | 稳态为 0；每次帧率变更 1 个，直到下次排空 |
| `_wrapperPool` | 每个已注册行为 1 个，即 $O(N)$ |

三个通道、若干行为时，池化内存总共是几百个小对象，且不随帧率或运行时长增长。

## 总空间

$$
S = O(C) + O(C \cdot (\text{采样器} + \text{总线} + \text{池})) + O(N) + O(K)
$$

具体到每通道：两个采样器、一个时间源、三个各至多 50 元素的池、四条队列（稳态为空）、一个 `CancellationTokenSource`、两条线程（异步模式下为零），以及行为字典与其快照。这个清单里没有任何一项随帧率伸缩，也没有任何一项随时间伸缩 —— 跑了一周的通道与跑了一秒的通道持有完全相同的东西。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 69-93、152-154、160-167、741-751、872-901、1017-1030 行；`Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs` 24-30 行。
