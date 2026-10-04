# 帧派发

一帧的代价，以及它为什么不随帧率增长。

设 $N$ 为通道上已注册的行为数，$k$ 为自上次重建以来新增或移除的数量。

## 两趟派发

一次 update 迭代在同一数组上做三趟：

$$
T_{\text{帧}} = \underbrace{O(N)}_{\text{Update 趟}} + \underbrace{O(N)}_{\text{LateUpdate 趟}} + \underbrace{O(1)}_{\text{采样、限速、统计}}
$$

每趟的循环体是：一次数组索引、一次对包装器的模式匹配、一次委托调用。`Handled` 检查被提到循环体开头，因此中止阶段的行为会把**两个**循环的剩余部分压成一次分支：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（692-701 行）
for (int i = 0; i < wrappers.Length; i++)
{
    if (frameArgs.Handled || token.IsCancellationRequested) break;
    var w = wrappers[i];
    if (w is { IsActive: true, Behavior: not null })
    {
        try { w.Behavior.InvokeUpdate(frameArgs); }
        catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
    }
}
```

于是这个界在一个方向上是紧的：$T_{\text{Update 趟}} \le c_1 N$，常数是一次委托调用；而在下标 $i$ 处置位 `Handled` 的行为会让两趟的代价都变成 $O(i)$ 而不是 $O(N)$。

循环体内的 `try`/`catch` 从成本角度值得一提：在无异常路径上，`.NET` 里 `try` 块在运行时零开销，所以异常隔离在异常真正发生之前是免费的。

## 每步，而不是每帧

fixed 泵的代价按步（$h$ 毫秒）计，不按帧计：

$$
T_{\text{固定}} = O(N) \text{ 每欠下的步}
$$

在 $F$ fps 与步长 $h$ 毫秒下，每秒欠的步数是 $1000/h$，而每秒的帧数是 $F$，所以固定趟发生的频率约为 update 趟的 $\frac{1000}{F \cdot h}$ 倍：

$$
\frac{\text{步}}{\text{帧}} \approx \frac{1000}{F \cdot h}
$$

取默认值 $F = 60$、$h = 16$：$\frac{1000}{60 \cdot 16} \approx 1.04$ 步/帧。把目标改成 2 fps，比值约 31；按 `SetFixedUpdateInterval(200)` 且保持 60 fps，则降到 2.5。演示是**测量**这个比值而不是计算它 —— 在一秒窗口内取 $\Delta \text{固定步} / \Delta \text{帧}$（`MainWindow.xaml.cs` 201-228 行）—— 因此它显示的值跟随的是*实测*帧率而非配置帧率，并在 update 泵还在起步时偏大。另需注意这个比值与时间速率无关：速率推动虚拟时钟，而固定泵跟随虚拟时钟。

## 摊还的缓存校验

`GetCachedWrappers` 每趟都会跑，缓存有效时是 $O(1)$：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（741-751 行）
private BehaviorWrapper[] GetCachedWrappers()
{
    var currentTime = GetTimestamp();
    if (_wrappersNeedSort || currentTime - Interlocked.Read(ref _lastConfigCheckTimestamp) >
        TimeConversion.MillisecondsToTicks(MAX_CONFIG_CACHE_DURATION_MS, TimeConversion.DefaultTicksPerSecond))
    {
        RebuildCachedWrappers();
        Interlocked.Exchange(ref _lastConfigCheckTimestamp, currentTime);
    }
    return _cachedWrappers;
}
```

- **缓存命中：** 一次 `Stopwatch.GetTimestamp()`、一次 `Interlocked.Read`、一次比较、一次 `volatile` 数组读取。常数级，每帧调用三次（每趟一次）外加每个固定步一次。
- **缓存未命中：** 走 `RebuildCachedWrappers`，$O(N^2)$ 就在那里。

$T_{\text{重建}}$ 有三部分 —— 分配并填充（$O(N)$）、插入排序（最坏 $O(N^2)$，对已有序数组是 $O(N)$，而这是常态，因为 `ExecutionOrder` 是单调自增计数器且注册顺序*就是*执行顺序）、可能的 `Array.Resize` 拷贝（$O(N)$）：

$$
T_{\text{重建}} = O(N) + O(N^2)_{\text{最坏}} + O(N) = O(N^2) \text{，实际为 } O(N)
$$

源码注释隐含地给出了这个取舍：选插入排序而非比较排序，是因为「行为数通常很小，避免 LINQ 分配」。在现实的 $N$（个位数）下，派发循环自身的 $O(N)$ 才是主项，排序的渐进量级根本咬不到。

## 空间

每通道的稳态空间是固定的，不随帧增长：

| 结构 | 大小 |
|---|---|
| `_behaviors` | $O(N)$ —— 每个已注册行为一个包装器 |
| `_cachedWrappers` | $O(N)$ —— 快照 |
| 三个池 | 各 $O(\min(\text{churn}, 50))$，上限由 `DEFAULT_OBJECT_POOL_SIZE` 给出 |
| 四条队列 | $O(k)$，$k$ 为尚未生效的变化数；常态为 0 |
| 采样器、总线、CTS | 各 $O(1)$ |

**稳态下每帧分配为零。** 一个 `FrameEventArgs` 取出又归还；每次注册一个包装器、每次帧率变更一个配置请求，都池化；派发数组只在变化时替换，不每帧替换。这就是池存在的理由，而且它是可测量的：演示的 `HookEntry` 刻意是一个「构建时不触碰字符串」的结构体，因为「默认帧率下通道每秒约有 120 次钩子调用，一次一分配的日志会给它正在测量的那个循环强加 GC 成本」（`SimState.cs` 146-158 行）。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 689-751、872-901 行；`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs` 201-228 行；`Examples/Tickable/WPF/Demo/SimState.cs` 146-158 行。
