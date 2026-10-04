# 时间层 — 契约

命名空间 `VeloxDev.Timing`（`Src/Core/VeloxDev.Core/Interfaces/Timing/*.cs`）。消费者读的源、操纵它的控制面，以及建在其上的两种采样模式。实现见 [implementation](../01_实现/index.md)。

### 结构体：`TimeSample`

```csharp
public readonly struct TimeSample
{
    public TimeSample(TimeSpan delta, TimeSpan total, long step, long epoch);

    public TimeSpan Delta { get; }
    public TimeSpan Total { get; }
    public long Step { get; }
    public long Epoch { get; }
}
```

| 成员 | 说明 |
|---|---|
| `Delta` | 本次采样覆盖的时间。对非补偿采样器是自上次采样以来的实测间隔；对补偿采样器是固定的 `Step`，因为消费者必须按固定步长积分。`TimeSpan.Zero` 表示没有前进，调用方不应推帧。 |
| `Total` | 自上次 `ITimeSampler.Reset` 以来已计入的时间。对补偿采样器由已交付步数派生，因此精确、永不吸收不足一步的余数。 |
| `Step` | 到目前为止交付的步数；非补偿采样器为 0。 |
| `Epoch` | 采样时刻源的 `ITimeSource.Epoch`。变化表示源被重基（暂停、恢复、重定位或变速），任何累计状态不再可比较。 |

**说明：** `default(TimeSample)` 是「没什么可推」的值 —— 全零样本。它刻意**不携带绝对位置**：采样器的调用方已经持有源，需要绝对值时可以自己读 `ITimeSource.Ticks`；把绝对量与相对量放进同一个值，会诱使人读错那一个 —— 而且对补偿采样器而言，两者本就应当不一致（不足一步的余数按设计被排除在 `Total` 之外）。

### 接口：`ITimeSource`

```csharp
public interface ITimeSource
{
    long TicksPerSecond { get; }
    long Ticks { get; }
    TimeSpan Position { get; }
    double Rate { get; }
    bool IsPaused { get; }
    bool IsAdvancing { get; }
    long Epoch { get; }

    Task WaitWhileStalledAsync(CancellationToken cancellationToken = default);
}
```

| 成员 | 说明 |
|---|---|
| `TicksPerSecond` | `Ticks` 的 tick 单位。消费者用它换算，且**绝不**直接读框架时钟的频率：注入的源可能不是基于 `Stopwatch` 的（浏览器的 `Performance.now()`、宿主的合成时钟），换算就会静默出错。 |
| `Ticks` | 绝对位置，以 `TicksPerSecond` 为单位。两次读数之差有意义，量值本身没有。 |
| `Position` | 相对该源原点的位置，是 `Ticks` 的便捷视图。 |
| `Rate` | 源运行得多快。永不为负；零表示它不在前进。 |
| `IsPaused` | 源被 `ITimeSourceControl.Pause` 暂停期间为 true。 |
| `IsAdvancing` | 位置正在移动时为 true。消费者停摆在其上的是**它**，不是 `IsPaused`。 |
| `Epoch` | 每次源被重基就加一 —— 暂停、恢复、重定位或变速。持有累计状态的消费者比较它来察觉基准已失效。 |
| `WaitWhileStalledAsync(token)` | 源不再停摆时完成；已经在前进时立即完成。`IsAdvancing` 的可等待形式 ——「停摆」恰好是 `!IsAdvancing`。 |

**关于 `IsAdvancing` 与 `IsPaused`：** 两者不同，因为速率为零会冻结源而不暂停它。只检查 `IsPaused` 的循环会在时钟冻结时继续跑，而检查 `IsAdvancing` 但停错信号的循环会空转。`IsAdvancing` 被表述为**不变量，而不是公式**：*true 蕴含位置正在移动*，无论它没移动的原因是什么 —— 一个位置由宿主推进、而不是读取时从时钟算出的源，必须在宿主停止供给时报 `false`（播放循环被挂起、解码缓冲空、标签页切到后台），即便没人调用 `Pause`。弄错是静默的：一个冻结时仍报 `true` 的源，永远不让它的消费者停摆，于是锚定在它上面的每条循环都以采样率写着一个并不在变的帧 —— 无异常、无日志、无帧，只是永不停止的工作。

**关于 `WaitWhileStalledAsync`：** 它与 `IsAdvancing` 精确配对，使 `while (!IsAdvancing) await WaitWhileStalledAsync()` 不会在谓词仍为假时返回（那会把一个核热转掉），也使停摆的消费者不靠轮询、而是零唤醒。它还会在**轻推**时返回 —— 停摆期间施加的一次定位 —— 好把新位置画出来；调用方每次醒来后重新读取状态，而不是把完成当作「已恢复」。实现不得在此取写闸、必须以异步而非从控制调用内联的方式完成续体、必须在前进时返回已完成的任务，且必须观察 `cancellationToken`（消费者的停止必须能到达它，即便没有任何东西会替它恢复源）。

### 接口：`ITimeSourceControl : ITimeSource`

```csharp
public interface ITimeSourceControl : ITimeSource
{
    void Pause();
    void Resume();
    void SetRate(double rate);
    void Seek(TimeSpan position);
    void Wake();
}
```

| 成员 | 说明 |
|---|---|
| `Pause()` | 冻结源。暂停期间的时间**按构造**被排除 —— 什么都不累积。幂等。 |
| `Resume()` | 让源以它最后设置的速率继续运行。 |
| `SetRate(rate)` | 改变源运行得多快，而不移动位置。零冻结它但不暂停它；此时恢复什么也不做，只有非零速率能重新启动。速率为负时**抛 `ArgumentOutOfRangeException`** —— 时间只向前走，负速率是调用方错误而不是该夹取的东西（夹成暂停会让动画静默不跑；夹成前进速率会无视所提请求）。 |
| `Seek(position)` | 把源移到 `position`，保持速率。持有累加器的消费者必须把它当作不连续。暂停时没有帧去拾取新位置，所以这还会轻推停摆的消费者去重画。 |
| `Wake()` | **一次**唤醒停摆的消费者而不恢复。源正在运行时是空操作。用于两件不是恢复的事：重画暂停期间改变的位置，以及让取消到达一个其停摆等待对自身 token 一无所知的消费者。实现必须**替换**停摆信号而不是就地完成它 —— 完成它却让它仍装着，会让下一次等待立即返回，把帧空转出来。 |

**说明：** 与 `ITimeSource` 分开，好让读取面成为采样器与被动消费者所收到的 —— 一个 `ITimeSampler` 收到只读契约，**无法暂停世界**。控制调用可从任意线程安全调用，并在内部串行化。

### 接口：`ITimeSampler`

```csharp
public interface ITimeSampler
{
    void Reset();
}
```

**说明：** 两种采样模式共享的状态契约；不直接使用 —— 请选 `IUncompensatedTimeSampler` 或 `ICompensatingTimeSampler`。采样器持有**逐消费者状态**，且恰好有**一个逻辑所有者** —— 一条循环，一个采样器。它不加锁：状态是每帧触碰几次的几个整数，在那里加锁的成本高于它所守护的算术。实现不得在线程间共享，`Reset` 也不例外。`Reset` 重新锚定到源的当前时刻并清空每个累计量，使下一次采样像构造后的第一次；它在循环（重）启动时被调用，绝不在其采样调用进行中，且不触碰源。

### 接口：`IUncompensatedTimeSampler : ITimeSampler`

```csharp
public interface IUncompensatedTimeSampler : ITimeSampler
{
    TimeSample Sample();
}
```

**说明：** 尽力而为的采样 —— 自上次采样以来过了多少时间，且不保证本该采多少次。**晚只是晚。** 消费者对着源定位而不是累加时，这是正确的模式：动画读绝对位置，无论采样节奏如何都正确。调用之间不携带任何东西，所以漏掉一次采样不损失什么。源自上次调用以来没有前进时，`Sample()` 返回 `Delta` 为 `TimeSpan.Zero` 的样本，那是调用方不推帧的信号。

### 接口：`ICompensatingTimeSampler : ITimeSampler`

```csharp
public interface ICompensatingTimeSampler : ITimeSampler
{
    TimeSpan Step { get; set; }
    int MaxStepsPerCall { get; set; }
    int MaxPendingSteps { get; set; }
    long PendingSteps { get; }
    long DroppedSteps { get; }
    TimeSpan TimeToNextStep { get; }
    int Advance(out TimeSample sample);
}
```

| 成员 | 说明 |
|---|---|
| `Step` | 每一步覆盖的固定间隔。也是 `TimeSample.Delta` 报的值，因为消费者按固定步长积分 —— 实测间隔被刻意不暴露。为零或负时**抛 `ArgumentOutOfRangeException`**。 |
| `MaxStepsPerCall` | 一次 `Advance` 最多交付的步数。超出的部分保持**欠着**，因此这约束追帧突发而不影响总量。小于 1 时抛异常。 |
| `MaxPendingSteps` | 一次最多允许欠多少步，超过就宽恕。达到它意味着消费者完全跟不上源的速率，全额偿还会让它永久落后；超出部分被丢弃并计入 `DroppedSteps`。小于 1 时抛异常。 |
| `PendingSteps` | 欠着但未交付的步数。在一次 `Advance` 之后读它，是区分「被上限截断」（非零）与「消费者已追到源的当前时刻」（零）的唯一方法。 |
| `DroppedSteps` | 被 `MaxPendingSteps` 宽恕的步数。非零意味着已交付步数与源已流逝时间已分叉，恰好差这么多步。 |
| `TimeToNextStep` | 距离下一步被欠还有多久 —— 已经欠着步时为 `TimeSpan.Zero`。循环在两次推之间等的东西：恰好睡到边界正是重点，替代方案是在步长的一个分数上醒来再问一次，那既晚又是每次轮询一次唤醒。 |
| `Advance(out sample)` | 报告调用方现在该推几步 —— 至多 `MaxStepsPerCall`，欠不足一步时为零。调用方推那么多次，每次带同样的固定 `Delta`。 |

**说明：** 复还所欠的固定步长采样：在任意区间内交付步数等于 `floor(elapsed / Step)`，无漂移、无步被静默丢失。用于步数必须精确的消费者 —— 物理、定频积分。它与非补偿模式的区别在于如何处理两份剩余：不足一步的余数被带到下次调用，绝不四舍五入掉；而 `MaxStepsPerCall` 本次放不过去的整步保持欠着而非被丢弃，于是计数仍然正确、只是把突发摊开。唯一的界是 `MaxPendingSteps`：没有它契约无法满足，因为一台挂起数小时的机器欠下数百万步，而按上限限速偿还期间消费者要比直接宽恕落后得更久。源的**重基**（`Epoch` 变化）丢弃欠账而不是偿还它：向后定位绝不能产生负推送，向前定位不能凭空补出一串从未发生过的步。
