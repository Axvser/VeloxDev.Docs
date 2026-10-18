# 复杂度 — 过渡动画：节拍器与调度器

## 每帧一次等待

让出间隔是上限，不是栅格：

$$
\Delta_{\text{yield}} = \frac{1000}{\max(1, \text{FPS})} \ \text{ms}
$$

它每帧重读，因此在运行中的动画上收紧 `FPS` 立即生效。因为时间轴 —— 不是等待 —— 是计时权威，晚醒只会画出更靠后的一帧而不是错误的一帧；等待只决定循环多久*看*一次。

$$
O(1)\ \text{time}, \qquad 0\ \text{bytes per wait after the first frame}
$$

`ArmNextFrame` 在有宿主 `FramePacerCore` 时经它路由，否则经一个复用的 `ReusableTimerWait`。它取代的替代方案是 `await Task.Delay(interval, token)`：每次等待构建一个新的 `DelayPromise` 并注册一次新的取消回调；提交 `8dca3893` 测得每次等待 **184 字节**（100 次等待：0 字节对 18 400）。`ReusableTimerWait` 与 `Task.Delay` 最终进入同一个 `Timer` 队列，因此它改变的是等待的*成本*，不是等待的*落地时机*。

代价是每个*动画*一个 `Timer`（约 200 字节）—— 且只对真正会等待的动画：`RunPassAsync` 先画帧再等待，若该帧已结束本趟就直接返回，因此单帧或零时长趟根本不构造它。超过约 1.1 帧后，复用定时器就已经领先。

## 读取时钟

趟位置是一次减法加一次换算：

$$
\text{elapsedTicks} = \text{Timeline.Ticks} - \text{Run.PassAnchor}, \qquad \text{elapsedMs} = \frac{\text{elapsedTicks} \cdot 1000}{\text{TicksPerSecond}}
$$

读取 `Timeline.Ticks` 是**无锁**的：一致的字段在序列计数器下发布，且因为只有控制调用会写，读者实际上从不重试。自旋循环是 $O(1)$ 期望，罕见的撕裂读最多一次 `SpinWait`。

位置运算本身值得引用，因为它的顺序就是全部要点：

$$
\text{Advance}(p, \Delta, \sigma) = p + \left\lfloor \frac{\Delta}{S} \right\rfloor \sigma + \frac{(\Delta \bmod S)\,\sigma}{S}, \qquad S = 10^4
$$

整数部分在相乘**之前**先取出。显然的 $\Delta \cdot \sigma / S$ 在 `long.MaxValue / σ` 处溢出：速度 $10^4$ 时，在 Windows 上约 2.9 年真实时间，但在 Linux 上只有 **10.7 天**（`Stopwatch` tick 是纳秒）。C# 算术不检查，因此失败不是异常，而是静默回绕到负位置，让一个从未暂停、从未定位的消费者永久卡住。测量值（BenchmarkDotNet，提交 `f5485adf`）：先乘形式 $0.23$ ns，本形式 $0.61$ ns —— 每帧每动画 $0.38$ ns，或 100 个动画 60 FPS 时每秒 $2.3\ \mu s$。

## 采样模式

`IUncompensatedTimeSampler` 是两个 `long` 字段上的 $O(1)$，没有累加器。`CompensatingTimeSampler` 保持整数 tick，并恰好交付

$$
\text{delivered} = \left\lfloor \frac{\text{elapsed}}{\text{Step}} \right\rfloor = \sum_{\text{calls}} \min\big(\text{pending},\ \text{MaxStepsPerCall}\big)
$$

子步余数被携带（$\text{acc} \bmod \text{Step}$），超上限的债务被延期而不是丢弃，因此该恒等式跨调用成立。被豁免的债务有界：

$$
\text{dropped} = \max(0,\ \text{pending} - \text{MaxPendingSteps}), \qquad \text{pending} \le \text{MaxPendingSteps}
$$

默认 `MaxPendingSteps = 64` 在 16 ms 步长下约代表一秒。重定基准（`Epoch` 变化）丢弃债务而不是偿还，这正是防止向后定位产生负推送的原因。

## 停泊信号

$$
\text{cost of a paused animation} = O(1)\ \text{wake-ups per change}, \quad \text{not} \quad O\!\left(\frac{1}{\Delta_{\text{yield}}}\right)
$$

`WaitWhileStalledAsync` 把循环停泊在一个恰好于 `IsAdvancing` 为 false 时安装的门上。必须在停泊时被看见的控制调用会**替换**门并完成旧门，因此停泊消费者每次变化只醒一次并重读状态，而不是轮询。没有这种配对，`while (!IsAdvancing) await WaitWhileStalledAsync()` 会立即返回并烧满一个核 —— 这就是谓词与信号必须在一处维护的原因。

## 调度器查找

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 是一次 `ConditionalWeakTable.GetValue`（互斥）或一次分配（非互斥）。`Execute` 由一个 `SemaphoreSlim` 门串行化；进入与离开一趟是摊还 $O(1)$ —— `Track` / `Untrack` 是以运行 token 源为键的一次字典增/删，`DrainActive`（由 `Exit` 调用）对调度器上 $K$ 个活动运行是 $O(K)$。

按目标的**非互斥**表是并发集合，因此注册与注销是 $O(1)$，只有*枚举*它 —— 用于 `Exit`、`Pause` 或任何其他控制调用 —— 才花费 $O(M)$，$M$ 是该目标上并发非互斥动画数。这是唯一随运行数增长的操作，也是*查询*助手（`Position`、`Cycle`、`Rate`、`IsPaused`）走 `TryGetFirstRun` 的原因：它返回第一个条目而不构建列表 —— 对一个没有运行的目标提问（这正是逐帧 `Transition.Position(target)` 大多数时候做的事）零分配。

`InterpolatorCore.CreateScheduler(target, effect)` 是对平台 effect 类型的一次类型测试加同样的查找，因此是 $O(1)$，且拒绝时零分配：基类返回 `null`，只有识别该 effect 的平台才继续 `FindOrCreate`。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 已声明状态（`IFrameState`） | $O(P)$ —— 三个字典（值 + 插值器 + 选项） |
| 已准备集合（`SamplerSet`） | $O(P)$ —— 每条路径一个 `(property, sampler, start, end, options)` 条目；**无帧列表** |
| `SamplerSet` 逐条目 `Working` 暂存 | $O(P)$，每次动画惰性分配一次并复用 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable` —— 随目标回收，无泄漏 |
| 非互斥调度器表 | 每目标 $O(N + M)$ |
| `TransitionProperty` 记忆缓存（`FromPropertyCache`） | $O(R)$ —— 每个曾反射的 `PropertyInfo` 一条共享路径，进程内持有（弱键，可回收的 `AssemblyLoadContext` 仍可卸载） |
| 每个运行循环一个 `ReusableTimerWait` | $O(1)$ —— 约 200 字节，首帧即结束的趟完全不分配 |
| Effect 事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活处理器目标数 |
| 跨帧存活的每动画状态 | $O(1)$ —— 一个 `TransitionRun`（时间轴、锚点、趟计数、token、线程） |

关于该表有两点。`SamplerSet` 的替换策略让 `Repeat` 既便宜又正确：重复段重放首次迭代准备的集合，因此 $O(P)$ 的准备成本每段只付一次，无论多少次迭代。`TransitionProperty` 缓存则是主题切换成本从每*次切换*变成每*进程*的原因：提交 `58ae23b3` 测得旧行为对一千个双属性元素约 **1.6 秒 UI 线程停顿、分配 29 MB**（首帧之前），之后约 **10 ms 与 6 MB**。

## 逐操作汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` —— 精确命中 | $O(1)$ |
| `TryGetInterpolator` —— 未命中 | $O(B + I)$，每属性每次动画一次 |
| `CreateScheduler`（类型测试 + CWT 查找） | $O(1)$ |
| `TransitionProperty.FromProperty` | 每 `PropertyInfo` 摊还 $O(1)$ |
| `.Property(...)` | $O(k)$，加冲突检查的 $O(P \cdot k)$ |
| `Prepare` 一个属性 | $O(1)$，注册表未命中时加 $O(B + I)$，结构体装配时加 $O(m_j)$ |
| `Prepare` 所有属性 | $O(P) + O(\sum m_j)$ |
| 采样一个属性（`InsertFrame`） | $O(1)$；$C$ 通道有界组为 $O(C)$ |
| 对一个采样施加所有属性 | $O(P)$ |
| 缓动 + 端点处理 | $O(1)$ |
| 一帧的等待 | $O(1)$ 时间，首帧后 0 字节 |
| `Timeline.Ticks` 读取 | $O(1)$ 期望，无锁 |
| `Advance`（位置运算） | $O(1)$，实测 0.61 ns |
| 调度器 `FindOrCreate` | $O(1)$ |
| 调度器进入 / 离开（`Track` / `Untrack`） | 摊还 $O(1)$ |
| `Exit` / 跨运行控制扫描 | 该目标上非互斥运行为 $O(M)$；四个查询经 `TryGetFirstRun` 为 $O(1)$ |
| 不可采样路径扫描（`RejectUnsampleablePaths`，每次运行一次） | $O(P)$ 次注册表查找 |
| 诊断报告 | 每阶段每运行 $O(1)$（`HashSet` 守卫限制重复） |

> 源：`Src/Core/VeloxDev.Core/TransitionSystem/{Runtime/FramePacerCore,Runtime/ReusableTimerWait,Runtime/TransitionInterpreter,Runtime/TransitionRun,Runtime/TransitionScheduler,Binding/TransitionProperty}.cs`、`Src/Core/VeloxDev.Core/Timing/{TimeSourceCore,CompensatingTimeSampler,UncompensatedTimeSampler}.cs`、`Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,ReusableTimerWaitTests,TimelineControlTests}.cs`、`Src/Core/VeloxDev.Core.Test/Timing/{CompensatingTimeSamplerTests,TimerCoreRegistryTests}.cs`。
