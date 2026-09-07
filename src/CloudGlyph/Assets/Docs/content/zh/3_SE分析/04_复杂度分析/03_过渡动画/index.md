# 复杂度分析 — 过渡动画

设 $P$ = 快照中记录的属性数，$k$ = 属性路径深度（表达式分段数）。采样是连续的（Stopwatch 驱动），因此没有预计算的帧数组：`ITransitionEffectCore.FPS` 作为最大采样率上限（让出间隔 = `1000 / FPS` ms），且永远不会物化出每属性帧列表。

## 构建快照（`.Property(...)` 调用）

$$O(P \cdot \bar{k})$$

每次 `.Property(lambda, value, options)` 把 lambda 解析为 `TransitionProperty`（路径分段上的 $O(k)$——`TransitionProperty.TryCreate` 解包并沿成员链遍历一次），把值（以及可选的插值选项）存入 `ConcurrentDictionary`（摊还 $O(1)$），并（若给了选项）再存一个选项条目。编译后的 getter/setter 委托在首次读写时惰性构建（$O(k)$ 编译一次），之后复用。对常见的单分段属性，这实际是每次调用 $O(1)$，即整张快照 $O(P)$。

## 采样器解析

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 是对 `NativeInterpolators`（`ConcurrentDictionary<Type, ISampler>`）的 `ConcurrentDictionary` 查找。按属性覆盖（`state.Interpolators`）再加一次常数检查。`RegisterInterpolator`/`UnregisterInterpolator` 是原子 `AddOrUpdate`/`TryRemove`，同样 $O(1)$。

## 更新器准备（`InterpolatorCore.Prepare`）

$$O(P) + O\!\left(\sum m_j\right)$$

`Prepare` 每段/每次动画只运行一次。对 $P$ 个已记录属性的每个：经编译 getter 读取当前值（由 `ProtectedGetValue` 编组，$O(1)$），解析一个 `ISampler`（$O(1)$；按属性覆盖 → 注册表 → 值类型 `ISampleable`），调用一次 `NormalizeStart`/`NormalizeEnd` 固定精确端点值，并把每个属性的 `(property, sampler, start, end, options)` 条目存入 `SamplerSet`。值类型 `ISampleable` 属性经由 `StructAssembler` 增加 $O(m_j)$，其中 $m_j$ = 声明的成员数（每个成员各一次注册表查找 + 一次当前值读取）。**不构建每属性帧列表。**

## 采样循环（`TransitionInterpreterCore.Execute`）

$$每次采样 O(P)$$

每次采样迭代求出一个缓动/钳制后的时间并通过 `SamplerSet.Apply` 应用，它遍历 $P$ 个已准备条目（每属性 $O(1)$）：

| 采样器 | 每次采样成本 | 说明 |
|---|---|---|
| 数值（`Double`/`Float`/`Int`/`Long`） | $O(1)$ | 一次 lerp |
| `ColorSampler`（ARGB 通道） | $O(1)$ | 4 个通道 lerp |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF` | $O(1)$ | 分量级 lerp |
| `Vector2`/`Vector3`/`Vector4` | $O(1)$ | 分量级 lerp |
| `QuaternionSampler`（`Slerp`，可选方向取反） | $O(1)$ | 常数级三角运算 |
| 带 `RotationDirection` 的 `DoubleSampler` | $O(1)$ | 每次调用一次 mod-360 delta，然后一次 lerp |

**端点都是 $O(1)$ 替换：** `t <= 0` 写入精确的归一化起点，`t >= 1` 写入精确的归一化终点（不采样）。中间帧调用 `InsertFrame`，引用类型在其中突变每个动画一个的 `working` 暂存（首次中间帧调用时惰性创建并复用）——快照捕获的共享 `start`/`end` 绝不突变。值类型算好即赋。复杂的适配器兜底（例如 WPF 混合非纯色 `Brush`）会按帧分配，但常见的纯色/变换路径是零分配的。

采样次数**不是**由 `FPS` 决定的——它是 Stopwatch 推导的 `elapsed / duration`，由 `1000 / FPS` ms 让出节流（节流阀，而非计时依据）。因此时长为 $D$ 的一程最多发出 $D \cdot \text{FPS}/1000$ 次采样，每次 $O(P)$。自动往返使程数翻倍；`LoopTime` 追加重复（`cycle ≤ LoopTime`）。有限运行的墙钟时间近似为

$$T_{\text{wall}} \approx D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])$$

（当 $\text{LoopTime} = \text{int.MaxValue}$ 时为永远）。不预计算缓动索引列表（$O(1)$ 额外空间），也不做逐帧 `Task.Delay` 校准。

## 调度器查找（`FindOrCreate`）

$$O(1)$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 执行 `ConditionalWeakTable` 查找（`MutualSchedulers`），或分配全新的非互斥调度器。`SemaphoreSlim.WaitAsync()` 门控串行化调度器上的执行；每目标的 `NoMutualSchedulers` 列表操作为 $O(M)$，其中 $M$ = 并发的非互斥动画数。

## 状态捕获（`TransitionSnapshotHelper`）

快照发现（`DiscoverAnimatableProperties`）是对对象图的递归 DFS，由对象重访集合与祖先**类型**守卫约束（无固定深度上限）：

$$O(V \cdot d)$$

其中 $V$ = 可达的复合对象/被枚举属性数，$d$ = 路径深度（实际受祖先类型守卫约束——成员类型已在当前路径上即停止递归）。搜索拒绝下钻到基元类型、枚举、值类型、`string`、`object`、`IEnumerable` 与 `Delegate`，且是 `ISampleable` 感知的：把引用类型 `ISampleable` 展开成声明成员路径，把值类型 `ISampleable` 当作整条路径捕获（之后由 `StructAssembler` 装配）。`CaptureAll`/`CaptureAllExcept` 以 `Interpolator.TryGetInterpolator(type, out _)`（或 `ISampler` 实现者）作为「可动画」判定。每个捕获的属性随后经编译 getter 读取一次：$O(P)$ 读取成本。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 状态（`IFrameState`） | $O(P)$ 字典（values + interpolators + options） |
| 已准备的采样器集（`SamplerSet`） | $O(P)$ —— 每属性一个 `(property, sampler, start, end, options)` 条目；无帧列表 |
| `SamplerSet` 每属性 `Working` 暂存 | $O(P)$ —— 每次动画惰性分配一次，跨帧复用 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable`（随目标回收，无泄漏） |
| 非互斥调度器表 | 每目标 $O(N + M)$，其中 $M$ = 并发的非互斥动画数 |
| 效果事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活的处理器目标 |

## 操作复杂度汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)`（表达式解析 + 字典插入） | 每属性 $O(k)$（单分段路径 $O(1)$） |
| `Prepare` 一个属性（读当前值 + 解析采样器 + 归一化端点） | $O(1)$（值类型 `ISampleable` 成员装配另加 $O(m_j)$） |
| `Prepare` 所有属性（`InterpolatorCore.Prepare`） | $O(P) + O(\sum m_j)$ |
| 采样一个属性（`ISampler.InsertFrame` / 暂存突变） | $O(1)$ |
| 一次采样应用到所有属性（`SamplerSet.Apply`） | $O(P)$ |
| 一次采样的缓动 + 钳制 | $O(1)$ |
| 端点写入（t <= 0 / t >= 1） | $O(1)$ 替换，不采样 |
| 调度器 `FindOrCreate`（CWT 查找） | $O(1)$ |
| `SnapshotAll` 发现（`DiscoverAnimatableProperties`） | 对象图上的 $O(V \cdot d)$ DFS |

## 说明

- 采样器**只准备一次**；每次采样只针对捕获的 start/end/options 重新求值缓动后的时间——无需构建、存储或重新索引帧列表。
- 引用类型经每个动画一个的 `working` 暂存插值，因此常见快速路径每次采样零分配（即使 `LoopTime = int.MaxValue`，每次迭代额外内存也是常数）。
- `SamplerSet.Apply` 为每个目标复用一个缓存闭包，并经由一个 `Interlocked` 读取的字段传递缓动时间，因此每次采样的编组不分配闭包。
- 对当前目标无效的属性路径由编译 getter 以 $O(1)$ 返回 `UnreadablePath` 哨兵，`Prepare` 跳过它而不是从错误的 `null` 采样。
- `TransitionProperty` 的 getter/setter 委托按属性惰性编译一次并跨采样复用，因此采样循环完全避免反射。

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionSnapshotHelper.cs`、`SamplerSet.cs`、`TransitionScheduler.cs`、`TransitionProperty.cs`、`StructAssembler.cs`、`NativeSamplers/*.cs`。

相关分析：[设计模式 — 过渡动画](../../02_设计模式分析/03_过渡动画/index.md) · [数据流 — 过渡动画](../../03_数据流分析/03_过渡动画/index.md)
