# 定步长节拍与补偿

fixed 泵的算术是本特性唯一真正的算法内容所在：一个欠整步、再补还的补偿采样器，且它报告的总量取自步序号而不是一个running求和。

设 $h$ 为步长（毫秒），$r$ 为时钟速率，$\Delta t$ 为两次 `Advance` 之间的墙钟时间。

## 采样器的算术

两次唤醒之间推进的虚拟时间是 $r \cdot \Delta t$，所以欠的整步数为

$$
n = \left\lfloor \frac{r \cdot \Delta t + \varepsilon}{h} \right\rfloor
$$

其中 $\varepsilon$ 是上一次调用存下的分数余数。采样器保留这个余数，这正是推送数跟随虚拟时钟而不是唤醒节奏的原因：在墙钟区间 $T$ 内的推送总数是

$$
\sum n \approx \left\lfloor \frac{r \cdot T}{h} \right\rfloor
$$

它与区间如何被切成唤醒无关。`TickableBusTests.FixedUpdatePushesTrackTheVirtualClockNotTheWakeCadence` 用 4 倍速率与 600 ms 窗口断言这一点，在 $\frac{r \cdot T}{h} = 150$ 附近接受一个 $+30\% / +20\%$ 的区间 —— 这个区间存在是因为 600 ms 窗口不包含整数个步，且采样器可能正持有半步。

旧实现恰恰差在这里：它**每次唤醒至多推一步**，所以每次唤醒的计数是 $\min(\lfloor r \cdot \Delta t / h \rfloor, 1)$，上限与 $r$ 无关。按一秒量，旧形式无论速率如何都给出约 $1000/h$ 次推送；新形式给出约 $r \cdot 1000 / h$ 次。

## 每步的总量

每个交付的步拿到它自己序号对应的时间：

$$
t_i = \bigl(\text{firstStep} + i\bigr) \cdot h, \qquad i = 0 \ldots n-1, \qquad \text{firstStep} = \text{sample.Step} - n + 1
$$

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（583-599 行）
var count = _fixedSampler.Advance(out var sample);
if (count > 0)
{
    var stepTicks = _fixedSampler.Step.Ticks;
    var firstStep = sample.Step - count + 1;

    for (var i = 0; i < count; i++)
    {
        var fixedFrameArgs = CreateFrameEventArgs(
            sample.Delta,
            TimeSpan.FromTicks((firstStep + i) * stepTicks));
        ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);

        _frameEventArgsPool.Return(fixedFrameArgs);
    }
}
```

替代做法 —— 把最后一次读数重复 $n$ 遍 —— 正是代码注释里点名移除掉的。序号形式每步代价 $O(1)$（一次乘法），换来的是 $t_i$ 在一整个批次里也精确且单调，这正是消费者能据以重建积分的原因。

## 两个上界：突发与欠账

采样器把三个整数分开保存 —— `_acc`（不足一步的余数）、`_earned`（时间已支付的步数）、`_delivered`（实际交出的步数）—— 于是 `PendingSteps = _earned - _delivered` 就是任意时刻的欠账（`CompensatingTimeSampler.cs` 32-44、104 行）。两个独立的上界作用于它：

| 上界 | 常量 | 默认 | 它约束什么 |
|---|---|---|---|
| `MaxStepsPerCall` | `DefaultMaxStepsPerCall` | 8 | 一次 `Advance` 最多交出几步。约束补还突发量 |
| `MaxPendingSteps` | `DefaultMaxPendingSteps` | 64 | 最多允许累积多少欠账。16 ms 步长下约一秒 |

每次调用的上界约束工作量，其余部分保持**欠着**；欠账上界约束欠账本身，超出部分被**宽恕**。按顺序：

$$
\text{pending} \to \min\left(\text{pending},\ P_{\max}\right) \quad\text{（超出部分宽恕，计入 }\texttt{DroppedSteps}\text{）}
$$

$$
n = \min\left(\text{pending},\ M_{\text{call}}\right)
$$

其中 $P_{\max} = 64$、$M_{\text{call}} = 8$。$S$ 毫秒的停摆按速率 $r$ 欠 $\left\lfloor r \cdot S / h \right\rfloor$ 步；高于 $P_{\max}$ 的部分被丢弃且永不回来：

$$
\text{被宽恕的步数} = \max\left(0, \left\lfloor \frac{r \cdot S}{h} \right\rfloor - P_{\max}\right), \qquad \text{调用后仍欠} = \text{pending} - n
$$

宽恕是刻意的，源码给出了理由：*「不宽恕的话，被挂起过的机器会欠下几百万步，而按 MaxStepsPerCall 限速偿还期间消费者要比直接宽恕落后得更久」*。`DroppedSteps` 是一个公开计数器，正是为了让这次损失可观察而不是静默。

WPF 演示的第三个卡顿按钮就是为它准备的。它的标签直接写出了算术：1500 ms 停摆在 16 ms 步长下欠约 94 步，超过 64 步的欠账上限，于是超出的部分被宽恕并永久丢失（`MainWindow.xaml` 63-64 行）。同一个演示上的 200 ms 按钮欠约 12 步 —— 两个上界之内，所以没有东西被丢弃，补还就是一批。

由此得到两个代价：

$$
T_{\text{补还}} = O(M_{\text{call}} \cdot N), \qquad T_{\text{稳态}} = O(1) \text{ 每步（摊还）}
$$

每次唤醒的工作量有界，代价是可能有有界的仿真时间被丢弃。

## Epoch：欠账消失的第三条路

还有一条路径，它正是「暂停中的通道恰好零成本」的原因：

```csharp
// Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs（133-141 行）
if (epoch != _epoch)
{
    _epoch = epoch;
    _lastTicks = now;
    _acc = 0;
    _earned = _delivered;
    sample = default;
    return 0;
}
```

总线在每次 rebase 时递增它的 `Epoch` —— 暂停、恢复、速率变更、seek。看到新 epoch 的采样器按构造丢弃欠账而不是补还，因此**暂停欠零步是可证的，且无需为暂停写任何特判**。同一个机制也防止速率变更用旧步长结算累加器，也正是 WPF 演示的「未交付时间」读数在速率或步长变更后应当归零重爬的原因。

这个检查的代价是每次 `Advance` 一次 `long` 比较 —— $O(1)$。

## 为什么等待要分片

线程路径上的睡眠从不是一次睡满整个间隔的 `Thread.Sleep`：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（862-870 行）
private static void Sleep(TimeSpan duration, CancellationToken token)
{
    var chunk = TimeSpan.FromMilliseconds(MAX_SLEEP_CHUNK_MS);
    for (var remaining = duration; remaining > TimeSpan.Zero; remaining -= chunk)
    {
        if (token.IsCancellationRequested) return;
        Thread.Sleep(remaining < chunk ? remaining : chunk);
    }
}
```

$w$ 毫秒等待对应的 `Thread.Sleep` 调用数是 $\lceil w / 50 \rceil$，因此停止延迟有上界 $50$ ms：

$$
\text{停止延迟} \le \min(w, 50\ \text{ms})
$$

在允许的最低目标帧率（$1$）下，一帧预算是 $1000$ ms；不分片的话一次停止要等满一整秒。分片的代价是每帧最多 $50$ ms 量级的调度开销，而采样器吸收得起：fixed 泵是补偿的，update 泵的 `DeltaTime` 是实测的。

## 给 update 泵限速

update 泵按**墙钟**而不是虚拟时钟限速：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（836-847 行）
private void FrameRateControlSync(long frameStartTime, CancellationToken token)
{
    // 目标帧率约束的是采样节奏，不是虚拟时钟，所以这里量的是墙钟——rate 减半不应该让帧率也减半。
    var elapsed = GetTimestamp() - frameStartTime;
    var target = _cachedTargetFrameDurationTicks;
    if (elapsed < target)
    {
        var sleepTime = (long)(target - elapsed);
        if (sleepTime > 0)
            Sleep(TimeConversion.TicksToTimeSpan(sleepTime, TimeConversion.DefaultTicksPerSecond), token);
    }
}
```

于是墙钟意义上的帧间隔是

$$
\max\left(\frac{1}{F},\ \text{一趟派发所花的时间}\right)
$$

而可达帧率受派发成本封顶：

$$
F_{\text{实测}} \le \frac{1}{T_{\text{派发趟}}}
$$

这就是派发常数为什么实际重要。若某个行为耗时 30 ms，那么约 33 fps 以上的目标都不可达，而报告这件事的是 `CurrentFPS` —— 它按墙钟测量。`TargetFPS` 仍会声称 60。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 446-507、557-620、836-870 行；`Examples/Tickable/WPF/Demo/MainWindow.xaml` 63-64 行；`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` 255-319 行。
