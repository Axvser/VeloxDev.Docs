# 复杂度分析 — 过渡动画

设 $P$ = 声明的属性数，$k$ = 属性路径深度（表达式分段数）。采样是连续的，节拍由该次运行的 `ITimeSourceControl` 决定（它唯一的时间来源是 `Stopwatch`），因此没有预计算的帧数组：`ITransitionEffectCore.FPS` 作为最大采样率上限（让出间隔 = `1000 / FPS` ms），且永远不会物化出每属性帧列表。

## 声明状态（`.Property(...)` 调用）

$$
O(P \cdot \bar{k})
$$

每次 `.Property(lambda, value, options)` 把 lambda 解析为 `TransitionProperty`（路径分段上的 $O(k)$——`TransitionProperty.TryCreate` 解包并沿成员链遍历一次），把值（以及可选的插值选项）存入 `ConcurrentDictionary`（摊还 $O(1)$），并（若给了选项）再存一个选项条目。编译后的 getter/setter 委托在首次读写时惰性构建（$O(k)$ 编译一次），之后复用。对常见的单分段属性，这实际是每次调用 $O(1)$，即整个分段 $O(P)$。

## 路径冲突检查（`StateCore.SetValue`）

$$
O(P \cdot k) \ \text{每次声明} \quad\Rightarrow\quad O(P^2 \cdot k) \ \text{整个分段}
$$

每写入一条路径，`RejectPathConflict` 都会遍历该分段**已有**的 value 路径，用 `TransitionProperty.IsDescendantOf`（每条 $O(k)$）双向判断父子关系，命中即抛 `TransitionPathConflictException`。因此 $P$ 条路径最坏累计 $O(P^2 \cdot k)$。**边界：** 该检查只看单条 transition 的 value 路径；跨 transition 的冲突、以及经 `SetInterpolator` / `SetOptions` 注册的路径都不遍历、不检查。

## 采样器解析

$$
O(1)\ \text{命中} \quad\Rightarrow\quad O(B + I)\ \text{未命中}
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 先在 `NativeInterpolators`（`ConcurrentDictionary<Type, ISampler>`）里试精确类型——一次哈希查找。未命中时它沿基类链由近及远遍历（$B$ = 祖先数），再遍历该类型的接口，取完整名称序数最小的那个匹配（$I$ = 接口数）。接口必须显式排序，因为反射给出的顺序没有保证，并列时总得有个说得出名字的规则。按属性覆盖（`state.Interpolators`）在两者之前再加一次常数检查；`RegisterInterpolator`/`UnregisterInterpolator` 是原子 `AddOrUpdate`/`TryRemove`，同样 $O(1)$。

这次遍历的 $O(B + I)$ 是**每个属性、每次动画一次**，绝不按帧发生：`Prepare` 把每条声明路径解析一次，帧路径只读取 `SamplerSet` 已经持有的那个 `ISampler`。`InterpolatorCoreTests` 钉住了这个顺序（精确 → 最近基类 → 接口，基类优先于接口，两个接口之间按名称序数）。

## 更新器准备（`InterpolatorCore.Prepare`）

$$
O(P) + O\!\left(\sum m_j\right)
$$

`Prepare<TPriorityCore>` 每段/每次动画只运行一次，且在 Awake 完成之后。对 $P$ 个已记录属性的每个：先把路径绑定到目标（`TransitionProperty.BindTo`——路径上没有冻结索引实参时返回实例自身，否则 $O(k)$），再经编译 getter 读取当前值（由 `ProtectedGetValue` 编组，$O(1)$），解析一个 `ISampler`（注册表命中 $O(1)$，走基类/接口遍历时 $O(B + I)$；按属性覆盖 → 注册表 → 值类型 `ISampleable`），调用一次 `NormalizeStart`/`NormalizeEnd` 固定精确端点值，并把每个属性的 `(property, sampler, start, end, options)` 条目存入 `SamplerSet<TPriorityCore>`。值类型 `ISampleable` 属性经由 `StructAssembler` 增加 $O(m_j)$，其中 $m_j$ = 声明的成员数（每个成员各一次注册表查找 + 一次当前值读取）。**不构建每属性帧列表。**

## 采样循环（`TransitionInterpreterCore.Execute`）

$$
\text{每次采样} \; O(P)
$$

每次采样迭代求出一个缓动后的时间并通过 `SamplerSet.Apply` 应用，它遍历 $P$ 个已准备条目（每属性 $O(1)$）：

| 采样器 | 每次采样成本 | 说明 |
|---|---|---|
| 数值（`Double`/`Float`/`Int`/`Long`） | $O(1)$ | 一次 lerp |
| `ColorSampler`（ARGB 通道） | $O(1)$ | 4 个通道 lerp |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF` | $O(1)$ | 分量级 lerp |
| `Vector2`/`Vector3`/`Vector4` | $O(1)$ | 分量级 lerp |
| `QuaternionSampler`（`Slerp`，可选方向取反） | $O(1)$ | 常数级三角运算 |
| 带 `RotationDirection` 的 `DoubleSampler` | $O(1)$ | 每次调用一次 mod-360 delta，然后一次 lerp |

**端点都是 $O(1)$ 替换：** `t <= 0` 写入精确的归一化起点，`t >= 1` 写入精确的归一化终点（不采样）。中间帧调用 `InsertFrame`，引用类型在其中突变每个动画一个的 `working` 暂存（首次中间帧调用时惰性创建并复用）——与声明时共享的 `start`/`end` 绝不突变。值类型算好即赋。复杂的适配器兜底（例如 WPF 混合非纯色 `Brush`）会按帧分配，但常见的纯色/变换路径是零分配的。

中间帧同样**不**钳制：缓动值原样交给采样器，因此 `Back`/`Elastic` 会越出 $[0,1]$——数值型采样器可外推，其余则钉到端点。在这里钳制会把这两条曲线压平。

采样次数**不是**由 `FPS` 决定的——它是时间轴推导的 `elapsed / duration`，由 `1000 / FPS` ms 让出节流（节流阀，而非计时依据；且该值逐帧读取，所以在运行中的动画上可以收紧速率上限）。因此时长为 $D$ 的一程最多发出 $D \cdot \text{FPS}/1000$ 次采样，每次 $O(P)$。自动往返使程数翻倍；`LoopTime` 追加重复（`run.Cycle ≤ effect.LoopTime`）。有限运行的墙钟时间近似为

$$
T_{\text{wall}} \approx \frac{D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])}{\text{rate}}
$$

（当 $\text{LoopTime} = \text{int.MaxValue}$ 时为永远），其中 $\text{rate} = 1$，除非 `Transition.SetRate` 改过它——速率按比例缩放已流逝时间，因此它除的是墙钟时间，而不改变每程的采样次数。不预计算缓动索引列表（$O(1)$ 额外空间）。

## 每帧一次等待（`ReusableTimerWait`）

$$
O(1)\ \text{时间}, \quad 0\ \text{字节/次等待}
$$

循环实际等待的是 `ArmNextFrame`。它的默认实现为整个循环复用**一个** `Timer`——每帧重新装上，而取消登记整次动画只做一次，而不是每帧一次。它替代的写法是 `await Task.Delay(interval, token)`：每等一次就新建一个 `DelayPromise` 并登记一次取消回调；`8dca3893` 实测为每次等待 184 字节（100 次等待：0 字节对 18400 字节）。`ReusableTimerWaitTests` 度量的是同一个差异。

代价是每个动画一个 `Timer`（约 200 字节）——但只对真正等待过的动画成立：`RunPassAsync` 是**先**画帧、再等待，若那一帧已结束本程就直接返回，因此单帧或零时长的程根本不会构造它。超过约 1.1 帧之后，复用计时器就已经更省。改变的只有「怎么等」：唤醒次数不变、线程行为不变，用的还是 `Task.Delay` 本身所在的那个 `TimerQueue`——晚醒只会把一帧画在更靠后的位置，而不是画错。

## 调度器查找（`FindOrCreate`）

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 执行 `ConditionalWeakTable` 查找（`MutualSchedulers`），或分配全新的非互斥调度器。`SemaphoreSlim.WaitAsync()` 门控串行化调度器上的执行；每目标的 `NoMutualSchedulers` 值是一个并发**集合**（`ConcurrentDictionary<ITransitionSchedulerCore, byte>`），登记与注销都是 $O(1)$，只有枚举它时——`Exit`、`Pause` 或任何其它控制调用——才是 $O(M)$，其中 $M$ = 该目标上并发的非互斥动画数。

## 调度器组合（`CreateScheduler`）

$$
O(1)
$$

`InterpolatorCore.CreateScheduler(target, effect)` 是一次针对平台效果类型的类型判断，加上与任何其它获取路径相同的 `ConditionalWeakTable` 查找，因此是 $O(1)$，且「拒绝」时零分配：基类实现返回 `null`，只有认出该效果的平台才会继续走 `FindOrCreate`。这一点重要，是因为它是只持有 `object` 的调用方唯一的入口——主题系统用一次切换跨越运行时类型各不相同的许多目标——所以这是该流程中启动**任何**动画的既有成本，而不是额外开销。

## 反射得到的路径（`TransitionProperty.FromProperty`）

$$
O(1)\ \text{每个 } PropertyInfo \text{ 摊还}
$$

`FromProperty` 经由一个静态 `ConcurrentDictionary<PropertyInfo, TransitionProperty>` 查找，对每个 `PropertyInfo` 返回**共享**路径，因此 $O(k)$ 的表达式解析与惰性的 getter/setter 编译对某个属性在进程内只付一次，而不是每次切换付一次。共享是安全的：路径不可变，`BindTo` 在没有冻结索引实参时返回实例自身，且惰性编译幂等（并发首次使用最多编译两次、丢弃一份）。

引入它的提交（`58ae23b3`）度量了改前的行为：一千个双属性元素时，准备这些路径在首帧之前耗掉约 1.6 秒 UI 线程停顿与 29 MB 分配，改后约为 10 ms 与 6 MB——这让一次切换的墙钟时间回到效果自身的时长，与它覆盖多少元素无关。缓存对每个被反射过的 `PropertyInfo` 保留一个条目，随进程存活。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 状态（`IFrameState`） | $O(P)$ 字典（values + interpolators + options） |
| 已准备的采样器集（`SamplerSet<TPriorityCore>`） | $O(P)$ —— 每属性一个 `(property, sampler, start, end, options)` 条目；无帧列表 |
| `SamplerSet<TPriorityCore>` 每属性 `Working` 暂存 | $O(P)$ —— 每次动画惰性分配一次，跨帧复用 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable`（随目标回收，无泄漏） |
| 非互斥调度器表 | 每目标 $O(N + M)$，其中 $M$ = 并发的非互斥动画数 |
| `TransitionProperty` 备忘缓存（`FromPropertyCache`） | $O(R)$ —— 每个被反射过的不同 `PropertyInfo` 一个共享路径，随进程存活 |
| 每个运行中的循环一个 `ReusableTimerWait` | $O(1)$ —— 约 200 字节，且在首帧即结束的程上完全不分配 |
| 效果事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活的处理器目标 |

## 操作复杂度汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` —— 精确命中 | $O(1)$ |
| `TryGetInterpolator` —— 未命中（基类遍历，再按名称遍历接口） | $O(B + I)$，每属性每次动画一次 |
| `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `CreateScheduler`（效果类型判断 + CWT 查找） | $O(1)$；平台拒绝时零分配 |
| `TransitionProperty.FromProperty` | 摊还 $O(1)$；每个 `PropertyInfo` 的首次调用付解析与 getter/setter 编译 |
| `.Property(...)`（表达式解析 + 冲突检查 + 字典插入） | 每属性 $O(P \cdot k)$（单分段路径 $O(1)$，$P$ = 已声明属性数） |
| `Prepare` 一个属性（绑定路径 + 读当前值 + 解析采样器 + 归一化端点） | $O(1)$（注册表未命中另加 $O(B + I)$，值类型 `ISampleable` 成员装配另加 $O(m_j)$） |
| `Prepare` 所有属性（`InterpolatorCore.Prepare`） | $O(P) + O(\sum m_j)$ |
| 采样一个属性（`ISampler.InsertFrame` / 暂存突变） | $O(1)$ |
| 一次采样应用到所有属性（`SamplerSet.Apply`） | $O(P)$ |
| 一次采样的缓动 + 钳制 | $O(1)$ |
| 一帧的等待（`ArmNextFrame` → `ReusableTimerWait`） | 时间 $O(1)$，0 字节（每个动画一个 `Timer`，而非每帧一个） |
| 端点写入（t <= 0 / t >= 1） | $O(1)$ 替换，不采样 |
| 调度器 `FindOrCreate`（CWT 查找） | $O(1)$ |
| 路径父子冲突检查（`StateCore.RejectPathConflict`） | 每次声明 $O(P \cdot k)$，整个分段 $O(P^2 \cdot k)$ |

## 说明

- 采样器**只准备一次**；每次采样只针对已记录的 start/end/options 重新求值缓动后的时间——无需构建、存储或重新索引帧列表。
- 引用类型经每个动画一个的 `working` 暂存插值，因此常见快速路径每次采样零分配（即使 `LoopTime = int.MaxValue`，每次迭代额外内存也是常数）。
- `SamplerSet.Apply` 为每个目标复用一个缓存闭包，并经由一个 `Interlocked` 读取的字段传递缓动时间，因此每次采样的编组不分配闭包。
- 对当前目标无效的属性路径由编译 getter 以 $O(1)$ 返回 `UnreadablePath` 哨兵，`Prepare` 跳过它而不是从错误的 `null` 采样。
- `TransitionProperty` 的 getter/setter 委托按属性惰性编译一次并跨采样复用，因此采样循环完全避免反射。
- 采样器是每属性、每次动画解析一次，绝不按帧，因此基类/接口遍历那 $O(B + I)$ 尽管不再是单次哈希查找，也依然留在帧路径之外。
- `FromProperty` 的备忘缓存把反射驱动的路径成本从「每次切换」移到「每进程」：对同一个 `PropertyInfo`，解析与编译只发生一次，无论有多少次切换用到它。
- 等待在**时间**上是每帧的，在**分配**上是每动画的：首帧之后，等待不再花任何分配。

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`Transition.cs`、`TransitionRun.cs`、`ReusableTimerWait.cs`、`Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs`、`PathIndex.cs`、`SamplerSet.cs`、`TransitionScheduler.cs`、`TransitionProperty.cs`、`State.cs`、`StructAssembler.cs`、`NativeSamplers/*.cs`、`Src/Core/VeloxDev.Core.Test/TransitionSystem/{InterpolatorCoreTests,ReusableTimerWaitTests}.cs`。

相关分析：[设计模式 — 过渡动画](../../02_设计模式分析/03_过渡动画/index.md) · [数据流 — 过渡动画](../../03_数据流分析/03_过渡动画/index.md)
