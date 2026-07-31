# 复杂度分析 — 过渡动画系统

## 核心操作

设 $P$ = 快照中记录的属性数，$S$ = 当前效果的帧数：

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

### 构建快照（`.Property(...)` 调用）

$$O(P)$$

每次 `.Property(lambda, value)` 把表达式解析为 `TransitionProperty`（每次调用常数时间，`TryCreate` 只遍历一次 lambda 体），并插入状态的 `ConcurrentDictionary`（摊还 $O(1)$）。

### 插值器解析

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 是 `ConcurrentDictionary` 查找。按属性自定义插值器与 `IInterpolable` 回退各加一次常数检查。

### 帧计算（`Interpolator.Interpolate`）

$$O(P \cdot S)$$

对 $P$ 个属性中的每个，插值器产生一个 $S$ 元素帧列表：

- 数值插值器：每属性 $O(S)$。
- `ColorInterpolator`（ARGB 通道）：$O(4S) = O(S)$。
- `QuaternionInterpolator`（`Slerp`）：$O(S)$，每帧常数级三角运算。

### 帧应用（解释器循环）

$$O(P \cdot S) \quad \text{计算}，\quad O(S) \quad \text{墙钟时间}$$

$S$ 次迭代中的每次执行 $P$ 次 `SetValue` 写入。非 UI 线程启动时的 UI 线程调度每帧增加 $O(1)$。总墙钟时间受 `Duration` 约束（循环时乘以 `LoopTime`）：

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime}$$

### 内存占用

| 结构 | 复杂度 |
|---|---|
| 状态（`IFrameState`） | $O(P)$ 字典 |
| 帧序列 | $O(P \cdot S)$ 中间值，过渡结束后释放 |
| 互斥调度器表 | $O(N)$ 个目标，经 `ConditionalWeakTable`（随目标回收） |
| 效果事件（`WeakDelegate`） | $O(H)$ 个处理器，$H$ = 存活的处理器目标 |

## 操作复杂度汇总

| 操作 | 复杂度 |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` | $O(1)$ |
| `.Property(...)`（表达式解析） | 每属性 $O(1)$ |
| 插值一个属性 | $O(S)$ |
| 插值所有属性 | $O(P \cdot S)$ |
| 帧写入（每帧） | $O(P)$ |
| 缓动索引查找 | 每帧 $O(1)$ |
| `SnapshotAll` 发现（`DiscoverAnimatableProperties`） | 对 $V$ 个可达属性 BFS，深度 $d$：$O(V \cdot d)$ |

## 说明

- 缓动通过**重新索引**预计算帧数组实现，每帧增加 $O(1)$，而不是重新求值。
- 长时循环（`LoopTime = int.MaxValue`）持有 $O(P \cdot S)$ 的帧序列内存，但每次迭代额外内存为常数。
- `TransitionSnapshotHelper.CaptureAll` 以 `Interpolator.TryGetInterpolator(type, out _)` 作为「可动画」判定；发现开销为对象图上的 $O(V \cdot d)$。

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionSnapshotHelper.cs`、`InterpolatorOutputCore.cs`。
