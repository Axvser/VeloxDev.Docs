# 时间层 — 实现

命名空间 `VeloxDev.Timing`（`Src/Core/VeloxDev.Core/Timing/*.cs`）。默认源、两个默认采样器、它们共享的 tick 换算，以及平台用来替换的注册表。它们实现的契约见 [contracts](../00_契约/index.md)。

### 静态类：`TimeConversion`

按源发布的单位做 tick 换算，使源之外的任何东西都不读框架时钟的频率。

```csharp
public static class TimeConversion
{
    public static long DefaultTicksPerSecond { get; }          // Stopwatch.Frequency

    public static TimeSpan TicksToTimeSpan(long ticks, long ticksPerSecond);
    public static long TicksToSpanTicks(long ticks, long ticksPerSecond);
    public static long SpanToTicks(TimeSpan span, long ticksPerSecond);
    public static double TicksToMilliseconds(long ticks, long ticksPerSecond);
    public static double TicksToSeconds(long ticks, long ticksPerSecond);
    public static long MillisecondsToTicks(double milliseconds, long ticksPerSecond);
}
```

**说明：** 每个成员都要求传入单位而不是假定一个：注入的源可能以浏览器的微秒或宿主的合成 tick 计数，而一个悄悄用 `Stopwatch.Frequency` 的换算会偏差几个数量级且毫无症状。`DefaultTicksPerSecond` 是默认源的单位，也是本命名空间中唯一提到 `Stopwatch` 的地方。

### 类：`TimeSourceCore : ITimeSourceControl`

默认时间源：一条绝对虚拟时间轴 —— 它在哪、跑多快，以及暂停期间让消费者停摆的那道闸。它也是**拥有时间的宿主派生的基类**。

```csharp
public class TimeSourceCore : ITimeSourceControl
{
    public TimeSourceCore();                                       // 机器时钟
    protected TimeSourceCore(Func<long> nowStamp, long ticksPerSecond);

    public long TicksPerSecond { get; }
    public long Ticks { get; }
    public TimeSpan Position { get; }
    public bool IsPaused { get; }
    public bool IsAdvancing { get; }
    public long Epoch { get; }
    public double Rate { get; set; }                               // set → SetRate

    public void Pause();
    public void Resume();
    public void SetRate(double rate);
    public void Seek(TimeSpan position);
    public void Wake();
    public Task WaitWhileStalledAsync(CancellationToken cancellationToken = default);

    protected void SetHostFeeding(bool feeding);
}
```

**说明：**
- 两条接缝，对应两种宿主形状：**拉取**型宿主回答「现在几点」并经受保护构造函数提供时间戳；**推送**型宿主的位置在回调中到达，它返回最后一次收到的值并通过 `SetHostFeeding` 报告供给状态。两者否则都要自行推演的一切 —— 锚点算术、epoch 协议、溢出守卫、停摆信号 —— 都留在这里。时间戳是 `Func<long>` 而不是虚方法，这是**刻意的**：它只在构造函数里读一次，而虚方法会在子类自己的构造函数赋好任何它可能读取的东西之前就运行重写 —— 经典的构造顺序陷阱，症状在这里是一口时钟。受保护构造函数对 null 时间戳抛 `ArgumentNullException`，对非正的 `ticksPerSecond` 抛 `ArgumentOutOfRangeException`。
- `SetHostFeeding(feeding)` 报告谁在喂这个源、供给是停了还是恢复了。供给静默会冻结位置而无人调用 `Pause`，`IsAdvancing` 必须如此报告，否则锚定在这里的每条循环都会继续采样一个并不在变的帧。它是方法而不是一个由宿主重写的 `IsAdvancing`，因为谓词与停摆信号必须一起动，宿主看不见它们是否一起动了，而弄错从宿主侧是不可见的。它**不是**重基：位置恰好在停止处接着走，因此累加器的基准仍然有效、`Epoch` 不动（一个自身时钟在供给静默期间仍在走的宿主描述的是跳跃，它用 `Seek` 说明）。幂等，可从任意线程调用。
- 时间是源自身单位下的原始整数 tick —— 不是 `double` 毫秒。精度不是理由（`double` 能精确容纳数十年的整数 tick）；理由是整口时钟状态因而可以是一组 `long` 字段，它们在 32 位与 64 位上各自原子、交换零成本。播放速率以 10 000 为标定的整数保存，于是时钟状态全程是整数的。
- 这条时间轴是**绝对的、永不重启**的 —— 这正是让多个消费者锚定在同一个实例上、共享一套传输的原因。单个消费者的趟被表达为该时间轴上的一个**锚点**，而不是通过重置它，因此在一个消费者上开启一趟不会移动任何其他消费者。
- 读取位置是**无锁**的：相干字段在序列计数器下发布，而由于唯一的写者是控制调用，读者实际上从不重试。写走写闸，读者从不触碰。停摆信号（`_parkGate`）恰好在 `IsAdvancing` 为假时非空 —— 绑定在消费者停摆所用的谓词上而不是绑定在「暂停」上，因此两者永不分歧。它同时是唤醒机制；一次必须在停摆期间被看见的控制调用会替换它并完成旧的，于是停摆的消费者每次变化只醒一次、然后重新读状态，而不是轮询。
- `internal static long Advance(position, elapsedTicks, speed)` 是位置算术，其顺序就是全部要害：elapsed 的整数部分在任何乘法**之前**先被取出。显然的 `elapsed * speed / Scale` 会在 `long.MaxValue / speed` 处溢出 —— 在 Windows 上约 2.9 年真实时间，但在 Linux 上只有 10.7 **天**（那里的 `Stopwatch` tick 是纳秒）。C# 算术不检查溢出，所以失败不是异常而是静默回绕到负位置，让一个从未被暂停、从未被定位的消费者永久卡死。（提交 `f5485adf`；实测 0.61 ns 对不安全写法的 0.23 ns —— 每个动画每帧 0.38 ns。）
- *核验：* `TimeSourceContractTests`、`HostTimeSourceTests`。

### 类：`UncompensatedTimeSampler : TimeSamplerCore, IUncompensatedTimeSampler`

```csharp
public sealed class UncompensatedTimeSampler : TimeSamplerCore, IUncompensatedTimeSampler
{
    public UncompensatedTimeSampler(ITimeSource source);
    public void Reset();
    public TimeSample Sample();
}
```

**说明：** 默认 `IUncompensatedTimeSampler` —— 自上次采样以来的实测间隔，不携带任何东西。全部状态就是两个整数，而它始终正确是因为它**没有累加器**：晚到的采样报更大的间隔、漏掉的采样报更大的间隔，但什么都不欠。暂停期间的时间自动被排除 —— 暂停的源不前进，所以恢复后的下一次采样只覆盖恢复以来的帧而不是暂停本身。这就是本设计不存在帧循环「恢复后 delta 尖峰」的原因；那是在用墙钟测量、同时另有一个标志说「别计数」时产生的假象。同一次 tick 内的重复采样返回 `default`（没有前进），是调用方跳过该帧的信号。*核验：* `UncompensatedTimeSamplerTests`。

### 类：`CompensatingTimeSampler : TimeSamplerCore, ICompensatingTimeSampler`

```csharp
public sealed class CompensatingTimeSampler : TimeSamplerCore, ICompensatingTimeSampler
{
    public const int DefaultMaxStepsPerCall = 8;
    public const int DefaultMaxPendingSteps = 64;

    public CompensatingTimeSampler(ITimeSource source, TimeSpan step);

    public TimeSpan Step { get; set; }
    public int MaxStepsPerCall { get; set; }
    public int MaxPendingSteps { get; set; }
    public long PendingSteps { get; }
    public long DroppedSteps { get; }
    public TimeSpan TimeToNextStep { get; }
    public void Reset();
    public int Advance(out TimeSample sample);
}
```

**说明：**
- 默认 `ICompensatingTimeSampler`：一个定步长累加器，交付步数等于 `floor(elapsed / Step)` 且无漂移。三个量刻意分开，因为把任意两个合并正是让定步长循环漂移的原因：`_acc`（还不够一步的时间 —— 被携带，绝不四舍五入掉）、`_earned`（时间已付账的步数 —— 在上限下它跑在已交付之前）、`_delivered`（实际报出的步数 —— 虚拟时钟是它乘 `Step`，因此它始终是整数计数的函数、绝不是某段实测间隔的函数）。所有算术都在源的**整数 tick** 上：无浮点，因此跑多久都没有累积误差，计数比较也是精确而非近似的。
- `DefaultMaxPendingSteps = 64` 在 16 ms 步长下约等于一秒：一次卡顿、慢帧或短暂停顿都远在界内；达到它意味着消费者完全跟不上。改变 `Step` 会丢弃不足一步的余数（它是按旧步长测得的分数，不是新步长的分数），同时保持已交付步数不动，因此计数保持连续。四舍五入到不到一个 tick 的步长会被垫到一个 tick，用于单位比 `TimeSpan` 的 100 ns 更粗的源。
- *核验：* `CompensatingTimeSamplerTests`（`DoesNotPushUntilAStepIsOwed`、`CarriesTheSubStepRemainderAcrossCalls`、`TheDeliveredCountEqualsFloorOfElapsedOverStep`、`TheCapDefersTheBurstInsteadOfDiscardingIt`、`PastThePendingBoundTheDebtIsForgivenAndCounted`、`ARebaseDiscardsTheDebtInsteadOfPayingIt`、`PausingDiscardsTheSubStepRemainderRatherThanBankingIt`、`ChangingTheStepDropsTheRemainderMeasuredInTheOldStep`、`ResetRePrimesTheClockAndClearsEveryCounter`、`AStepOfZeroOrLessIsRejected`、`BothCapsMustAllowAtLeastOne`）。

### 静态类：`TimerCore`

发放时间源与采样器的注册表，于是平台可以替换自己的实现而其他一切仍旧索取同一个契约。

```csharp
public static class TimerCore
{
    public const int DefaultFixedStepMilliseconds = 16;

    public static bool RegisterTimeSource<TContract>(Func<TContract> factory) where TContract : class, ITimeSourceControl;
    public static bool RegisterTimeSampler<TSampler>(Func<ITimeSource, TSampler> factory) where TSampler : class, ITimeSampler;
    public static bool UnregisterTimeSource<TContract>() where TContract : class, ITimeSourceControl;
    public static bool UnregisterTimeSampler<TSampler>() where TSampler : class, ITimeSampler;

    public static TContract CreateTimeSource<TContract>() where TContract : class, ITimeSourceControl;
    public static TSampler CreateTimeSampler<TSampler>(ITimeSource source) where TSampler : class, ITimeSampler;
}
```

| 成员 | 说明 |
|---|---|
| `RegisterTimeSource<TContract>(factory)` / `RegisterTimeSampler<TSampler>(factory)` | 把工厂安装在被替换的**契约**下 —— 键是契约类型，不是实现类型。后写胜出且原子（`AddOrUpdate`），与 `InterpolatorCore.RegisterInterpolator` 遵循同一规则。类型实参是契约：`RegisterTimeSource<ITimeSourceControl>(...)`。注册在实现类型下会把它存到没人看的地方。工厂为 null 时抛 `ArgumentNullException`。 |
| `UnregisterTimeSource<TContract>()` / `UnregisterTimeSampler<TSampler>()` | 移除一项注册，使该契约重新无法解析。 |
| `CreateTimeSource<TContract>()` | 为该契约创建源，按**精确**契约查找，不向更宽或更窄的注册回退。回退要在几个可赋值键中挑选，而字典顺序未被规定，于是同一次查找在不同运行会返回不同实现。该契约下没有注册时**抛 `InvalidOperationException`**。 |
| `CreateTimeSampler<TSampler>(source)` | 在源上创建采样器；源为 null 时抛 `ArgumentNullException`，契约未注册时抛 `InvalidOperationException`。 |

**说明：**
- Core 在静态构造函数里安装默认值，因此无论有没有平台接入，查找总能解析：`ITimeSourceControl` → `TimeSourceCore`；`IUncompensatedTimeSampler` → `UncompensatedTimeSampler`；`ICompensatingTimeSampler` → `CompensatingTimeSampler`，`Step = 16 ms`（`DefaultFixedStepMilliseconds`）。
- **每次查找都新建实例**，而只有一口时钟的宿主保持这个形状：每次调用返回一个包着那一路供给的全新包装器，而不是共享单例，于是每个消费者保留自己的暂停与速率。注册一个单例在这里会让暂停一个通道就暂停所有通道 —— 那正是 `TickManager`（`tickable` 特性）里逐通道源要避免的。键是私有的、从不外发：整体替换字典的调用方会丢掉默认值、让所有查找无法解析。
- 存在的替换是为**拥有时间的宿主** —— 播放循环、媒体位置、音频回调 —— 它经 `TimeSourceCore` 的受保护构造函数提供自己的时钟，并经 `SetHostFeeding` 报告是否仍在供给，而不是重新实现整条时间轴。它刻意**不是**为框架的渲染循环准备的：只在帧上移动的时钟会让帧率成为计时权威，而采样路径建立在相反之上 —— 时间轴决定动画走了多远，唤醒只是提醒。把循环按在 UI 线程上是一个真实但不同的问题，由拥有该循环的子系统的 `FramePacerCore` 解决。
- *核验：* `TimerCoreRegistryTests`（`CoreProvidesADefaultSource`、`CoreProvidesBothDefaultSamplers`、`TheDefaultFixedStepIsTheOneTheRegistryAdvertises`、`EveryLookupHandsBackAFreshInstance`、`ARegistrationUnderAContractIsWhatThatContractResolvesTo`、`RegisteringUnderAnImplementationTypeIsNotWhatAContractLookupFinds`、`AnUnregisteredContractThrows`、`UnregisteringLeavesTheContractUnresolvableAgain`）。

### 类：`TimeSamplerCore`（抽象支撑类型）

```csharp
public abstract class TimeSamplerCore
{
    protected TimeSamplerCore(ITimeSource source);
    protected ITimeSource Source { get; }
    protected long TicksPerSecond { get; }
    protected TimeSpan ToTimeSpan(long ticks);
    protected long ToTicks(TimeSpan span);
}
```

**说明：** 两个默认采样器共享的读取句柄与 tick 换算。源为 null 时抛 `ArgumentNullException`。它刻意**不持有采样状态、也不声明 reset**：基类构造函数先于派生字段初始化器运行，从这里发起的 reset 会读到派生类型尚未初始化的字段。每个采样器改从自己的构造函数自我初始化。
