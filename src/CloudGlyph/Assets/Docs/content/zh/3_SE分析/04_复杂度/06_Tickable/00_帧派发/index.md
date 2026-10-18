# 帧派发

一帧的成本，以及它为什么不随帧率增长。

设 $N$ 为通道上注册的行为数，$k$ 为自上次重建以来新增或移除的数量。

## 扫描

一次 update 迭代对同一数组做三次扫描：

$$
T_{\text{frame}} = \underbrace{O(N)}_{\text{Update 扫描}} + \underbrace{O(N)}_{\text{LateUpdate 扫描}} + \underbrace{O(1)}_{\text{采样、节拍、统计}}
$$

每次扫描的函数体是：一次数组索引、一次 wrapper 模式匹配、一次委托调用。`Handled` 检查被提到函数体顶部，所以中止该阶段的行为会把**两个**循环的余下部分变成一次分支：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 694-703 行）
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

所以界在一个方向上是紧的：$T_{\text{Update sweep}} \le c_1 N$，常数是一次委托调用；索引 $i$ 处的行为置起 `Handled` 会让两次扫描的代价都变成 $O(i)$ 而不是 $O(N)$。

`try`/`catch` 在循环内部，值得说一下它的成本：无异常路径上，.NET 中的 `try` 块运行期零成本，所以异常隔离在异常真正发生前是免费的。

## 每步，而不是每帧

fixed 泵的成本按步（$h$ ms），不按帧：

$$
T_{\text{fixed}} = O(N) \text{ per owed step}
$$

$F$ fps、步长 $h$ ms 时，每秒欠步数为 $1000/h$，而每秒帧数为 $F$，所以固定扫描发生的频率约为 update 扫描的 $\frac{1000}{F \cdot h}$ 倍：

$$
\frac{\text{steps}}{\text{frame}} \approx \frac{1000}{F \cdot h}
$$

默认 $F = 60$、$h = 16$：$\frac{1000}{60 \cdot 16} \approx 1.04$ 步每帧。目标改成 2 fps 时比值约 31；`SetFixedUpdateInterval(200)` 且 60 fps 时降到 2.5。示例测量这个比值而不是计算它 —— 一秒窗口内的 `Δfixed / Δframes`（`MainWindow.xaml.cs` 第 170-197 行）—— 所以显示值跟随*实测*帧率而不是配置值，并在 update 泵仍在爬升时偏高。还要注意比值不受时间缩放影响：速率移动虚拟时钟，fixed 泵跟随虚拟时钟。

## 均摊的缓存验证

`GetCachedWrappers` 每次扫描都运行，缓存有效时是 $O(1)$：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 743-753 行）
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

- **缓存命中：** 一次 `Stopwatch.GetTimestamp()`、一次 `Interlocked.Read`、一次比较、一次数组的 `volatile` 读。常数，每个 update 帧调用两次（每次 update 扫描一次），每个固定步再调用一次。
- **缓存未命中：** `RebuildCachedWrappers`，$O(N^2)$ 就在这里。

$T_{\text{rebuild}}$ 有三部分 —— 分配并填充（$O(N)$）、插入排序（最坏 $O(N^2)$，已有序数组上 $O(N)$，而这是常见情况，因为 `ExecutionOrder` 是单调递增计数器，注册顺序*就是*执行顺序）、可能的 `Array.Resize` 拷贝（$O(N)$）：

$$
T_{\text{rebuild}} = O(N) + O(N^2)_{\text{worst}} + O(N) = O(N^2) \text{，实际为 } O(N)
$$

源码注释隐含地说明了取舍：选择插入排序而非比较排序，是因为「行为数量通常很小，避免 LINQ 分配」。在现实 $N$（个位数）下，派发循环自身的 $O(N)$ 占主导，排序的渐近性咬不到。

## 空间

每通道的稳态空间是固定的，不随帧增长：

| 结构 | 大小 |
|---|---|
| `_behaviors` | $O(N)$ —— 每个已注册行为一个 wrapper |
| `_cachedWrappers` | $O(N)$ —— 快照 |
| 三个池 | 各 $O(\min(\text{churn}, 50))$，受 `DEFAULT_OBJECT_POOL_SIZE` 限制 |
| 四个队列 | $O(k)$，$k$ 是未应用的变更；通常为 0 |
| 采样器、bus、CTS | 各 $O(1)$ |

**稳态下每帧分配为零。** 一个 `FrameEventArgs` 取一次还一次；每次注册一个 wrapper、每次帧率变更一个配置请求，都是池化的；派发数组只在变更时替换，不按帧替换。这就是池存在的理由，而且可测量：示例的 `HookEntry` 刻意是 struct，「构建时不碰字符串」，因为「默认帧率下通道每秒约 120 次钩子，按调用分配的日志会把 GC 成本加在它正在度量的循环上」（`SimState.cs` 第 119-128 行）。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 691-753、874-903 行；`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs` 第 170-197 行；`Examples/Tickable/WPF/Demo/SimState.cs` 第 119-128 行。
