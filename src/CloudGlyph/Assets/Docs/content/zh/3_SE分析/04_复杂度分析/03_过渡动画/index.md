# 复杂度分析 — 过渡动画

## 核心操作

设 $P$ = 快照中记录的属性数，$S$ = 当前效果的帧数：

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

### 构建快照（`.Property(...)` 调用）

$$O(P)$$

每次 `.Property(lambda, value)` 把表达式解析为 `TransitionProperty`（每次调用常数时间；`TryCreate` 只遍历一次 lambda 体），并插入状态的 `ConcurrentDictionary`（摊还 $O(1)$）。编译后的 getter/setter 委托在首次读写时惰性构建，之后复用。

### 插值器解析

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 是 `ConcurrentDictionary` 查找。按属性自定义插值器与 `IInterpolable` 回退各加一次常数检查。`RegisterInterpolator` 是原子 `AddOrUpdate`，同样 $O(1)$。

### 帧计算（`InterpolatorCore.Interpolate`）

$$O(P \cdot S)$$

对 $P$ 个属性中的每个，插值器产生一个 $S$ 元素帧列表：

| 插值器 | 每属性成本 | 说明 |
|---|---|---|
| 数值（`Double`/`Float`/`Int`/`Long`） | $O(S)$ | 线性遍历，每帧常数操作 |
| `ColorInterpolator`（ARGB 通道） | $O(4S) = O(S)$ | 每帧 4 个通道 lerp |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF`/`Vector2/3/4` | $O(S)$ | 分量级 lerp |
| `QuaternionInterpolator`（`Slerp`） | $O(S)$ | 每帧常数级三角运算（点积 + 可能取反 + `Slerp`） |
| 带 `RotationDirection` 的 `DoubleInterpolator` | $O(S)$ | 预计算一次 mod-360 delta，然后线性遍历 |

**关键说明：** 帧**列表**是提前（急切地）物化的。缓动不会重跑插值器 —— 解释器只重新索引同一数组，因此缓动每帧只增加 $O(1)$。

### 调度器查找（`FindOrCreate`）

$$O(1)$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` 执行 `ConditionalWeakTable` 查找（`MutualSchedulers`），或分配全新的非互斥调度器。`SemaphoreSlim.WaitAsync()` 门控串行化互斥调度器上的执行。

### 帧泵（`TransitionInterpreterCore.Execute`）

$$O(S) \text{ 次遍历 } P \text{ 个属性} \quad \Rightarrow \quad O(P \cdot S) \text{ 总工作量}$$

$S$ 次迭代中的每次通过 `InterpolatorOutputBase.SetValues` 执行 $P$ 次 `SetValue` 写入（编译委托，无每帧反射）。非 UI 线程启动时的 UI 线程调度每帧增加 $O(1)$。自动往返使帧遍历翻倍（$2S$）；`LoopTime` 再乘以它。墙钟时间受限于：

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime} \quad (\text{当 } \text{LoopTime} = \text{int.MaxValue} \text{ 时为永远})$$

解释器只预计算一次缓动索引列表：$O(S)$ 空间与时间。`WaitForFrameAsync` 每帧 $O(1)$。

### 状态捕获（`TransitionSnapshotHelper`）

发现过程（`DiscoverAnimatableProperties`）是对对象图的深度受限 DFS：

$$O(V \cdot d)$$

其中 $V$ = 可达的公共实例属性数（可读写、非索引），$d \le \text{maxDepth} = 4$（默认）。搜索拒绝下钻到基元类型、枚举、值类型、`string`、`object`、`IEnumerable` 与 `Delegate`。`CaptureAll` 以 `Interpolator.TryGetInterpolator(type, out _)` 作为「可动画」判定。每个捕获的属性随后经编译 getter 读取一次：$O(P)$ 读取成本。

### 内存占用

| 结构 | 复杂度 |
|---|---|
| 状态（`IFrameState`） | $O(P)$ 字典（values + interpolators + options） |
| 帧序列（`InterpolatorOutputBase.Frames`） | $O(P \cdot S)$ 中间值，过渡结束后释放 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable`（随目标回收，无泄漏） |
| 非互斥调度器表 | 每个目标 $O(N \cdot M)$，其中 $M$ = 并发的非互斥动画数 |
| 效果事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活的处理器目标 |

## 操作复杂度汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)`（表达式解析 + 字典插入） | 每属性 $O(1)$ |
| 插值一个属性 | $O(S)$ |
| 插值所有属性 | $O(P \cdot S)$ |
| 缓动索引列表预计算 | $O(S)$ |
| 帧写入（每帧） | $O(P)$ |
| 缓动索引查找 | 每帧 $O(1)$ |
| 调度器 `FindOrCreate`（CWT 查找） | $O(1)$ |
| `SnapshotAll` 发现（`DiscoverAnimatableProperties`） | 对象图上的 $O(V \cdot d)$ DFS |

## 说明

- 帧**只预计算一次**并**重新索引**以应用缓动 —— 昂贵的每属性工作在首帧之前完成一次，而非每帧执行。
- 长时循环（`LoopTime = int.MaxValue`）持有 $O(P \cdot S)$ 的帧序列内存，但每次迭代额外内存为常数。
- 对当前目标无效的属性路径由编译 getter 以 $O(1)$ 返回 `UnreadablePath` 哨兵，插值器跳过它而不是从错误的 `null` 插值。
- `TransitionProperty` 的 getter/setter 委托按属性惰性编译一次并跨帧复用，因此帧泵完全避免反射。

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionSnapshotHelper.cs`、`InterpolatorOutputCore.cs`、`TransitionScheduler.cs`、`TransitionProperty.cs`。
