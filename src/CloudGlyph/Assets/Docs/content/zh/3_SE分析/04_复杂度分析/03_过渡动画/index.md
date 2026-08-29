# 复杂度分析 — 过渡动画

## 核心操作

设 $P$ = 快照中记录的属性数。采样是连续的（Stopwatch 驱动），因此没有预计算的帧数：`ITransitionEffectCore.FPS` 作为最大采样率上限（yield 间隔 = `1000 / FPS` ms），且永远不会物化出每属性 $S$ 元素的帧列表。

### 构建快照（`.Property(...)` 调用）

$$O(P)$$

每次 `.Property(lambda, value)` 把表达式解析为 `TransitionProperty`（每次调用常数时间；`TryCreate` 只遍历一次 lambda 体），并插入状态的 `ConcurrentDictionary`（摊还 $O(1)$）。编译后的 getter/setter 委托在首次读写时惰性构建，之后复用。

### 采样器解析

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 是对 `NativeInterpolators`（`ConcurrentDictionary<Type, ISampleable>`）的 `ConcurrentDictionary` 查找。按属性自定义 `ISampleable`（`state.Interpolators`）与起始/结束值本身是 `ISampleable` 的自回退各加一次常数检查。`RegisterInterpolator` 是原子 `AddOrUpdate`，同样 $O(1)$。

### 更新器准备（`InterpolatorCore.Prepare`）

$$O(P)$$

`Prepare` 每次动画只运行一次。对 $P$ 个属性中的每个：经编译 getter 读取当前值（`ProtectedGetValue`，$O(1)$），解析 `ISampleable`（$O(1)$），并调用 `Normalize(start, end, options)` 得到无状态 `ISampler` 存入 `SamplerSet`。**不构建每属性帧列表** —— 每次采样的值在采样时惰性计算。

### 采样循环（`TransitionInterpreterCore.Execute`）

$$每次采样 O(P)$$

每次采样迭代求出一个缓动/钳制后的时间 `t ∈ [0,1]`，并通过 `SamplerSet.Apply` 应用，它遍历 $P$ 个已准备的采样器。每个属性的工作为 $O(1)$：

| 采样器 | 每次采样成本 | 说明 |
|---|---|---|
| 数值（`Double`/`Float`/`Int`/`Long`） | $O(1)$ | 一次 lerp |
| `ColorSampler`（ARGB 通道） | $O(1)$ | 4 个通道 lerp |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF`/`Vector2/3/4` | $O(1)$ | 分量级 lerp |
| `QuaternionSampler`（`Slerp`） | $O(1)$ | 常数级三角运算（点积 + 可能取反 + `Slerp`） |
| 带 `RotationDirection` 的 `DoubleSampler` | $O(1)$ | 每次调用一次 mod-360 delta，然后一次 lerp |

**端点都是 $O(1)$ 替换：** `t <= 0` 写入精确的起始值，`t >= 1` 写入精确的结束值（不采样）。引用类型由采样器在 `Update` 内**原地**突变 `start` 现有实例，因此中间采样零分配；值类型算好即赋。

采样次数**不是**由 `FPS` 决定的 —— 它是 Stopwatch 推导的 `elapsed / duration`，仅由粗糙的 1 ms `Task.Delay` 让出节流（不是计时依据）。因此一趟最多发出约 `Duration / 1ms` 次采样，每次 $O(P)$。自动往返使程数翻倍；`LoopTime` 再乘以它。墙钟时间受限于：

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime} \quad (\text{当 } \text{LoopTime} = \text{int.MaxValue} \text{ 时为永远})$$

不预计算缓动索引列表（$O(1)$ 额外空间），也没有逐帧 `Task.Delay` 校准。

### 调度器查找（`FindOrCreate`）

$$O(1)$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 执行 `ConditionalWeakTable` 查找（`MutualSchedulers`），或分配全新的非互斥调度器。`SemaphoreSlim.WaitAsync()` 门控串行化互斥调度器上的执行。

### 状态捕获（`TransitionSnapshotHelper`）

发现过程（`DiscoverAnimatableProperties`）是对对象图的深度受限 DFS：

$$O(V \cdot d)$$

其中 $V$ = 可达的公共实例属性数（可读写、非索引），$d \le \text{maxDepth} = 4$（默认）。搜索拒绝下钻到基元类型、枚举、值类型、`string`、`object`、`IEnumerable` 与 `Delegate`。`CaptureAll` 以 `Interpolator.TryGetInterpolator(type, out _)` 作为「可动画」判定。每个捕获的属性随后经编译 getter 读取一次：$O(P)$ 读取成本。

### 内存占用

| 结构 | 复杂度 |
|---|---|
| 状态（`IFrameState`） | $O(P)$ 字典（values + interpolators + options） |
| 已准备的采样器集（`SamplerSet`） | $O(P)$ —— 每个属性一个 `ISampler`（捕获 start/end/options）；无帧列表 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable`（随目标回收，无泄漏） |
| 非互斥调度器表 | 每个目标 $O(N \cdot M)$，其中 $M$ = 并发的非互斥动画数 |
| 效果事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活的处理器目标 |

## 操作复杂度汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)`（表达式解析 + 字典插入） | 每属性 $O(1)$ |
| `Prepare` 一个属性（读当前值 + 解析采样器 + 创建更新器） | $O(1)$ |
| `Prepare` 所有属性（`InterpolatorCore.Prepare`） | $O(P)$ |
| 采样一个属性（`ISampler.Update` / 原地突变） | $O(1)$ |
| 一次采样应用到所有属性（`SamplerSet.Apply`） | $O(P)$ |
| 一次采样的缓动 + 钳制 | $O(1)$ |
| 端点写入（t <= 0 / t >= 1） | $O(1)$ 替换，不采样 |
| 调度器 `FindOrCreate`（CWT 查找） | $O(1)$ |
| `SnapshotAll` 发现（`DiscoverAnimatableProperties`） | 对象图上的 $O(V \cdot d)$ DFS |

## 说明

- `SamplerSet` **只准备一次**（$O(P)$）；每次采样只针对捕获的 start/end/options 重新求值缓动后的时间 —— 无需构建、存储或重新索引帧列表，也没有急切生成的 `count` 个装箱对象。
- 引用类型由采样器在 `Update` 内**原地**突变 `start` 现有实例，因此中间采样每次零分配（即使 `LoopTime = int.MaxValue`，每次迭代额外内存也是常数）。
- 对当前目标无效的属性路径由编译 getter 以 $O(1)$ 返回 `UnreadablePath` 哨兵，`Prepare` 跳过它而不是从错误的 `null` 采样。
- `TransitionProperty` 的 getter/setter 委托按属性惰性编译一次并跨采样复用，因此采样循环完全避免反射。

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionSnapshotHelper.cs`、`SamplerSet.cs`、`TransitionScheduler.cs`、`TransitionProperty.cs`。
