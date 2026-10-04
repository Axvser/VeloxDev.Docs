# 复杂度 — 过渡动画：节拍与调度器

## 每帧一次等待

让出间隔是上限，不是栅格：

$$
\Delta_{\text{yield}} = \frac{1000}{\max(1, \text{FPS})} \ \text{ms}
$$

且每帧重读，因此在运行中的动画上收紧 `FPS` 会立即生效。因为计时权威是时间轴、不是等待，醒晚了只是画出一帧走得更远的画面而不是错的帧；等待只决定循环多久*看*一次。

$$
O(1)\ \text{time}, \qquad 0\ \text{bytes per wait after the first frame}
$$

有宿主时 `ArmNextFrame` 走宿主的 `FramePacerCore`，否则走一个复用的 `ReusableTimerWait`。它取代的替代方案是 `await Task.Delay(interval, token)`，每次等待建一个全新的 `DelayPromise` 并登记一个全新的取消回调；提交 `8dca3893` 实测那是每次等待 **184 字节**（100 次等待：0 字节对 18 400）。`ReusableTimerWait` 用的是 `Task.Delay` 最终也会用的同一个 `Timer` 队列，因此改变的是等待的成本而不是它何时落地。

代价是每个*动画*一个 `Timer`（约 200 字节）—— 而且只对一个真的会等待的动画：`RunPassAsync` 在等待之**前**先画那一帧、并在该帧结束这趟时返回，因此单帧或零时长的趟永远不会构造它。超过约 1.1 帧之后复用定时器就已领先。

## 读时钟

趟位置是一次减法加一次换算：

$$
\text{elapsedTicks} = \text{Timeline.Ticks} - \text{Run.PassAnchor}, \qquad \text{elapsedMs} = \frac{\text{elapsedTicks} \cdot 1000}{\text{TicksPerSecond}}
$$

读 `Timeline.Ticks` 是**无锁**的：相干字段在序列计数器下发布，而由于唯一的写者是控制调用，读者实际上从不重试。自旋循环是期望 $O(1)$，在罕见的撕裂读上至多一次 `SpinWait`。

位置算术本身值得引用，因为它的顺序就是全部要害：

$$
\text{Advance}(p, \Delta, \sigma) = p + \left\lfloor \frac{\Delta}{S} \right\rfloor \sigma + \frac{(\Delta \bmod S)\,\sigma}{S}, \qquad S = 10^4
$$

整数部分在任何乘法**之前**先被取出。显然的 $\Delta \cdot \sigma / S$ 会在 `long.MaxValue / σ` 处溢出：速率为 $10^4$ 时那是 Windows 上约 2.9 年真实时间，但在 Linux 上只有 **10.7 天**（那里的 `Stopwatch` tick 是纳秒）。C# 算术不检查溢出，所以失败不是异常而是静默回绕到负位置，让一个从未被暂停、从未被定位的消费者永久卡死。实测（BenchmarkDotNet，提交 `f5485adf`）：先乘写法 $0.23$ ns 对这里 $0.61$ ns —— 每帧每动画 $0.38$ ns，也就是一百个动画 60 FPS 下每秒 $2.3\ \mu s$。

## 采样模式

`IUncompensatedTimeSampler` 在两个 `long` 字段上是 $O(1)$、无累加器。`CompensatingTimeSampler` 保留整数 tick，并精确交付

$$
\text{delivered} = \left\lfloor \frac{\text{elapsed}}{\text{Step}} \right\rfloor = \sum_{\text{calls}} \min\big(\text{pending},\ \text{MaxStepsPerCall}\big)
$$

不足一步的余数被携带（$\text{acc} \bmod \text{Step}$），超上限的欠账被迟延而非丢弃，因此该恒等式跨调用成立。被宽恕的欠账有界：

$$
\text{dropped} = \max(0,\ \text{pending} - \text{MaxPendingSteps}), \qquad \text{pending} \le \text{MaxPendingSteps}
$$

默认 `MaxPendingSteps = 64` 在 16 ms 步长下约等于一秒。一次重基（`Epoch` 变化）丢弃欠账而不是偿还它，这正是让向后定位不产生负推送的原因。

## 停摆信号

$$
\text{cost of a paused animation} = O(1)\ \text{wake-ups per change}, \quad \text{not} \quad O\!\left(\frac{1}{\Delta_{\text{yield}}}\right)
$$

`WaitWhileStalledAsync` 让循环停在一个恰在 `IsAdvancing` 为假时装上的闸上。一次必须在停摆期间被看见的控制调用会**替换**该闸并完成旧的，于是停摆的消费者每次变化只醒一次、重新读状态，而不是轮询。没有这个配对，`while (!IsAdvancing) await WaitWhileStalledAsync()` 会立刻返回并把一个核热转掉 —— 这就是谓词与信号在一处维护的原因。

## 调度器查找

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 是一次 `ConditionalWeakTable.GetValue`（互斥）或一次分配（非互斥）。`Execute` 由 `SemaphoreSlim` 门串行化；进入与离开一趟是摊还 $O(1)$ —— `Track` / `Untrack` 是按该趟 token 源为键的一次字典增/删，而 `DrainActive`（由 `Exit` 调用）对该调度器上 $K$ 个活动 run 是 $O(K)$。

每目标的**非互斥**表是并发集合，因此登记与注销是 $O(1)$，只有*枚举*它 —— 为一次 `Exit`、一次 `Pause` 或任何其他控制调用 —— 才付出 $O(M)$，其中 $M$ 是该目标上并发非互斥动画数。那是唯一一个成本随有多少动画在跑而增长的操作，也是为什么那些*查询*助手（`Position`、`Cycle`、`Rate`、`IsPaused`）走 `TryGetFirstRun` —— 它在不建列表的情况下返回第一条 —— 对一个什么都没在跑的目标提问，而那正是一个逐帧 `Transition.Position(target)` 大多数时候在做的事，零分配。

`InterpolatorCore.CreateScheduler(target, effect)` 是对平台 effect 类型的一次类型测试加同一次查找，因此是 $O(1)$，且拒绝时不分配：基类返回 `null`，只有认出该 effect 的平台才继续 `FindOrCreate`。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 已声明状态（`IFrameState`） | $O(P)$ —— 三份字典（值 + 插值器 + 选项） |
| 已准备集合（`SamplerSet`） | $O(P)$ —— 每条路径一条 `(property, sampler, start, end, options)` 条目；**无帧列表** |
| `SamplerSet` 逐条目 `Working` 暂存 | $O(P)$，每动画惰性分配一次并复用 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable` —— 随目标回收，无泄漏 |
| 非互斥调度器表 | 每目标 $O(N + M)$ |
| `TransitionProperty` 记忆缓存（`FromPropertyCache`） | $O(R)$ —— 每个曾被反射的 `PropertyInfo` 一条共享路径，持有整个进程（弱键，因此可回收的 `AssemblyLoadContext` 仍能卸载） |
| 每条运行中循环一个 `ReusableTimerWait` | $O(1)$ —— 约 200 字节，且首帧即结束的趟完全没有 |
| effect 事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活处理器目标数 |
| 跨帧存活的每动画状态 | $O(1)$ —— 一个 `TransitionRun`（时间轴、锚点、趟、token、线程） |

关于该表有两点说明。`SamplerSet` 的替换策略让 `Repeat` 既廉价又正确：一个重复的分段重放它首次迭代准备的那套集合，因此 $O(P)$ 的准备成本每分段只付一次，无论有多少次迭代。而 `TransitionProperty` 缓存是主题切换的成本按*进程*而非按*切换*计的原因：提交 `58ae23b3` 实测旧行为在一千个双属性元素上是约 **1.6 秒 UI 线程停顿与 29 MB 分配**（首帧之前），改后约 **10 毫秒与 6 MB**。

## 逐操作汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` —— 精确命中 | $O(1)$ |
| `TryGetInterpolator` —— 未命中 | $O(B + I)$，每动画每属性一次 |
| `CreateScheduler`（类型测试 + CWT 查找） | $O(1)$ |
| `TransitionProperty.FromProperty` | 每个 `PropertyInfo` 摊还 $O(1)$ |
| `.Property(...)` | $O(k)$，外加冲突检查的 $O(P \cdot k)$ |
| `Prepare` 单个属性 | $O(1)$，加注册表未命中时的 $O(B + I)$ 与结构体装配的 $O(m_j)$ |
| `Prepare` 全部属性 | $O(P) + O(\sum m_j)$ |
| 采样单个属性（`InsertFrame`） | $O(1)$；$C$ 通道受限组为 $O(C)$ |
| 把一次采样施加到全部属性 | $O(P)$ |
| 缓动 + 端点处理 | $O(1)$ |
| 一帧的等待 | $O(1)$ 时间，首帧之后 0 字节 |
| 读 `Timeline.Ticks` | 期望 $O(1)$，无锁 |
| `Advance`（位置算术） | $O(1)$，实测 0.61 ns |
| 调度器 `FindOrCreate` | $O(1)$ |
| 调度器进入 / 离开（`Track` / `Untrack`） | 摊还 $O(1)$ |
| `Exit` / 跨 run 的控制扫描 | 该目标上非互斥 run 的 $O(M)$；四个查询经 `TryGetFirstRun` 为 $O(1)$ |
| 不可采样路径扫描（`RejectUnsampleablePaths`，每趟一次） | $O(P)$ 次注册表查找 |
| 诊断报告 | 每阶段每趟 $O(1)$（一个 `HashSet` 守卫封顶重复） |

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/{TransitionInterpreter,FramePacerCore,ReusableTimerWait,TransitionScheduler,TransitionRun,TransitionProperty}.cs`、`Src/Core/VeloxDev.Core/Timing/{TimeSourceCore,CompensatingTimeSampler,UncompensatedTimeSampler}.cs`、`Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,ReusableTimerWaitTests,TimelineControlTests}.cs`、`Src/Core/VeloxDev.Core.Test/Timing/{CompensatingTimeSamplerTests,TimerCoreRegistryTests}.cs`。
