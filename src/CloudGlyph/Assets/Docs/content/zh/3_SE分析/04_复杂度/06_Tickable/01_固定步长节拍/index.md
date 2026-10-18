# 固定步长节拍与补偿

fixed 泵的算术是本特性唯一真正有算法内容的地方：一个补偿采样器，欠整步并补还，报告的总时间来自步序号而不是累加和。

设 $h$ 为步长（毫秒），$r$ 为时钟速率，$\Delta t$ 为两次 `Advance` 之间的墙钟时间。

## 采样器的算术

两次唤醒之间推进的虚拟时间是 $r \cdot \Delta t$，所以欠的整步数为

$$
n = \left\lfloor \frac{r \cdot \Delta t + \varepsilon}{h} \right\rfloor
$$

其中 $\varepsilon$ 是上一次调用结余的分数余数。采样器保留这个余数，这正是让推送次数跟随虚拟时钟而不是唤醒节奏的原因：墙钟区间 $T$ 内的总推送次数为

$$
\sum n \approx \left\lfloor \frac{r \cdot T}{h} \right\rfloor
$$

与区间如何切成唤醒无关。`TickableBusTests.FixedUpdatePushesTrackTheVirtualClockNotTheWakeCadence` 用 4 倍速率和 600 ms 窗口断言这一点，接受 $\frac{r \cdot T}{h} = 150$ 附近 −30% / +20% 的带宽 —— 带宽存在是因为 600 ms 窗口包含非整数步，采样器可能持有一个部分步。

这换来的是与唤醒切分方式无关的推送计数：采样器保留分数余数，所以一次迟到的唤醒会交付它欠下的步，而不是丢掉它们。

## 每步的总时间

每个交付的步拿到自己序号的总时间：

$$
t_i = \bigl(\text{firstStep} + i\bigr) \cdot h, \qquad i = 0 \ldots n-1, \qquad \text{firstStep} = \text{sample.Step} - n + 1
$$

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 478-496 行）
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

替代做法 —— 把最后一次读数重复 $n$ 遍 —— 正是代码注释点名的被移除项。序号形式的代价是每步 $O(1)$（一次乘法），换来的是 $t_i$ 在一批之内也精确且单调，这正是消费者能重建积分的原因。

## 两个上界：突发与欠账

采样器把三个整数分开保存 —— `_acc`（不足一步的余数）、`_earned`（时间已支付的步数）、`_delivered`（已交出的步数）—— 于是任意时刻 `PendingSteps = _earned - _delivered` 就是欠账（`CompensatingTimeSampler.cs` 第 38-43、105 行）。两个独立上限作用于它：

| 上限 | 常量 | 默认 | 限制什么 |
|---|---|---|---|
| `MaxStepsPerCall` | `DefaultMaxStepsPerCall` | 8 | 一次 `Advance` 最多交出多少步。限制追赶突发 |
| `MaxPendingSteps` | `DefaultMaxPendingSteps` | 64 | 欠账最多能积累多少。约等于 16 ms 步长下的一秒 |

每次调用上限限制工作量，余下**继续欠着**；欠账上限限制债务并**宽恕**超出部分。依次为：

$$
\text{pending} \to \min\left(\text{pending},\ P_{\max}\right) \quad\text{（超出部分宽恕，计入 } \texttt{DroppedSteps}\text{）}
$$

$$
n = \min\left(\text{pending},\ M_{\text{call}}\right)
$$

其中 $P_{\max} = 64$、$M_{\text{call}} = 8$。速率 $r$ 下停摆 $S$ ms 欠 $\left\lfloor r \cdot S / h \right\rfloor$ 步；超过 $P_{\max}$ 的部分被丢弃且永不再现：

$$
\text{steps forgiven} = \max\left(0, \left\lfloor \frac{r \cdot S}{h} \right\rfloor - P_{\max}\right), \qquad \text{steps still owed after the call} = \text{pending} - n
$$

宽恕是刻意的，源码说明了原因：*「不宽恕的话，被挂起过的机器会欠下几百万步，而按 MaxStepsPerCall 限速偿还期间消费者要比直接宽恕落后得更久」*。`DroppedSteps` 是公开计数器，正是为了让损失可观察而不是静默。

这就是 WPF 示例第三个卡顿按钮的用途。它的标签直接写出算术：16 ms 步长下停摆 1500 ms 欠约 94 步，超过 64 步的欠账上限，所以超出部分被宽恕并永久丢失（`MainWindow.xaml` 第 63-64 行）。同样的运行在 200 ms 按钮上欠约 12 步 —— 在两个上限之内，所以什么都不丢，追赶只是一批。

由此两个成本：

$$
T_{\text{catch-up}} = O(M_{\text{call}} \cdot N), \qquad T_{\text{steady}} = O(1) \text{ per step amortised}
$$

每次唤醒的工作有界，代价是一段可能有界、可能被丢弃的模拟时间。

## Epoch：欠账消失的第三条路

还有一条路径，它让暂停中的通道开销恰好为零：

```csharp
// Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs（第 134-142 行）
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

bus 每次重定基（暂停、恢复、速率变更、seek）都会递增 `Epoch`。看到新 epoch 的采样器按构造丢弃欠账而不是补还，所以**暂停欠零步是可证明的，不需要为暂停写特例**。这也是速率变更不会对着旧步长结算累加器的机制，以及示例的「未交付时间」读数在速率或步长变更后会回落到零而不是重新爬升的原因。

检查的代价是每次 `Advance` 一次 `long` 比较 —— $O(1)$。

## 为什么等待要分片

线程路径上的睡眠从不是一次睡满整个间隔：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 864-872 行）
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

等待 $w$ ms 的 `Thread.Sleep` 调用次数是 $\lceil w / 50 \rceil$，所以停止延迟以 $50$ ms 为界：

$$
\text{stop latency} \le \min(w, 50\ \text{ms})
$$

在允许的最低目标帧率（$1$）下，帧预算为 $1000$ ms；不分片的话停止要等满一整秒。分片最多带来每帧 $50$ ms 量化的调度开销，采样器会吸收它，因为 fixed 泵有补偿，而 update 泵的 `DeltaTime` 是测量出来的而不是假设的。

## update 泵的节拍

update 泵按**墙钟**而不是虚拟时钟控制节拍：

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs（第 838-849 行）
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

所以墙钟意义上的帧间隔是

$$
\max\left(\frac{1}{F},\ \text{time spent in the sweep}\right)
$$

可达帧率受扫描成本限制：

$$
F_{\text{achieved}} \le \frac{1}{T_{\text{sweep}}}
$$

这就是派发常数在实践上重要的原因。如果一个行为耗时 30 ms，任何高于约 33 fps 的目标都不可达，而按墙钟测量的 `CurrentFPS` 会报告这一点。`TargetFPS` 则继续声称 60。

> 源码：`Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` 第 448-509、559-622、838-872 行；`Examples/Tickable/WPF/Demo/MainWindow.xaml` 第 63-64 行；`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` 第 255-319 行。
