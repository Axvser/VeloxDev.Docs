# 复杂度 — 过渡动画：插值

## 构建一次过渡（`.Property(...)` 调用）

$$
O(P \cdot \bar{k}) \;\Rightarrow\; O(P^2 \cdot k) \text{ per transition when the conflict check is counted}
$$

每次 `.Property(lambda, value, options)` 把 lambda 解析成 `TransitionProperty` —— 分段上 $O(k)$，因为 `TransitionProperty.TryCreate` 只解包并遍历一次成员链 —— 把值（与可选 options）存入 `ConcurrentDictionary`（摊还 $O(1)$），然后运行父/子冲突检查：把新路径与**每个**已声明键用 `IsDescendantOf` 双向比较。每次比较在分段链上是 $O(k)$，因此声明一次过渡的全部 $P$ 条路径总共 $O(P^2 \cdot k)$ —— 对一次过渡携带的少量路径可忽略，这是把「一个对象一条路径」变成构建期不变量而非运行时惊喜的代价。

编译后的 getter/setter 委托**首次读/写时惰性构建**（一次 $O(k)$ 编译）并复用。`FromProperty`（反射驱动入口）按 `PropertyInfo` 记忆化，因此解析与编译对每个属性在进程内只付一次，而不是每次切换一次。

## 采样器解析

$$
O(1)\ \text{on a hit} \quad\Rightarrow\quad O(B + I)\ \text{on a miss}
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 先在注册表里试精确类型（一次哈希查找）。未命中时，它遍历基类链（由近及远，$B$ 个祖先），再遍历类型的接口，保留全名序数最小者（$I$ 个接口）。接口被显式排序，因为反射不承诺顺序，平局裁决必须被点名。

遍历成本是 $O(B + I)$，**每属性每次动画一次**，绝不逐帧：`Prepare` 解析每条声明路径一次，帧路径只读取 `SamplerSet` 已持有的 `ISampler`。逐属性覆盖在两段之前增加一次常数检查，`RegisterInterpolator` / `UnregisterInterpolator` 是原子的 `AddOrUpdate` / `TryRemove`，$O(1)$。

## 准备（`InterpolatorCore.Prepare`）

$$
O(P) + O\!\left(\sum_{j} m_j\right)
$$

`Prepare` 每段跑一次。对 $P$ 条记录路径中的每条，它把路径绑定到目标（`BindTo` —— 无冻结索引实参时是恒等，否则 $O(k)$），在目标线程上经编译 getter 读取当前值（$O(1)$），解析 `ISampler`（上面三段），调用一次 `NormalizeStart` / `NormalizeEnd`，并存入一个条目。一个值类型 `ISampleable` 属性增加 $O(m_j)$，即声明成员数，每个成员一次注册表查找与一次值读取。**不构建任何逐属性帧列表。**

## 一帧

趟位置是趟锚点进入源的距离：

$$
\text{rawT} = \frac{\text{ms}(\text{Timeline.Ticks} - \text{Run.PassAnchor})}{D}, \qquad D = \text{effect.Duration.TotalMilliseconds}
$$

$$
\text{easedT} = \begin{cases} 1 & \text{forward pass, } \text{rawT} \ge 1 \\[2pt] 0 & \text{reverse pass, } \text{rawT} \ge 1 \\[2pt] \text{Ease}(\text{rawT}) & \text{otherwise (forward)} \\[2pt] \text{Ease}(1 - \text{rawT}) & \text{otherwise (reverse)} \end{cases}
$$

写入的值是采样器自己的事，但每个数值采样器都是 lerp：

$$
\text{value}(t) = s + (e - s) \cdot t
$$

注意 `easedT` **不**被夹取：`Back` 峰值约 $1.10$、`Elastic` 约 $1.37$，夹取会把两条曲线压平。每个采样器决定越界 $t$ 的含义。

每采样成本是 $O(P)$ —— 每个已准备条目一次 `InsertFrame`，各 $O(1)$（一次 lerp、一次分量 lerp 或一次 `Slerp`）—— 外加缓动求值本身的 $O(1)$。

## 过冲的代价

$[0, 1]$ 之外的缓动时间合法，其后果按值类别决定：

- **可外推类**（`double`、`float`、`int`、`long`、`Point`、`PointF`、`Vector*`、`Rectangle` 位置、`Thickness`）只需让 lerp 越过端点再回来。这就是过渡的 `Duration` 与过冲彼此独立的原因：200 px 行程上 $\pm 3.8\%$ 的过冲约 7.6 px，成本恒定。
- **有界通道类**（`Color`、`Size`、`SizeF`、`Rectangle`、`RectangleF`）经 `BoundedProgress`，找出让每个已加入通道都留在范围内的最大进度。给定通道 $\{(s_j, e_j)\}$ 与界限 $[m, M]$：

$$
\text{progress} = \max\!\Big(t \; \text{clamped iteratively:} \; \forall j,\; \frac{\min(M - s_j,\; m - s_j)}{e_j - s_j} \le \text{progress} \le \frac{\max(M - s_j,\; m - s_j)}{e_j - s_j}\Big)
$$

`Add` 对每个通道实现为两次比较，因此整组对 $C$ 个通道是 $O(C)$ —— 常数，且加通道顺序无关，因为 `Add` 只会收紧。剩余过冲对整组丢弃。对 $[0, 1]$ 内的缓动时间，结果恰好就是那个时间，因此范围正常的动画只付比较成本。
- **固定范围类**（`Quaternion`）根本无法过冲：`Quaternion.Slerp` 定义在 $[0, 1]$ 上，采样器在恰好 $t = 0$ / $t = 1$ 时返回调用方自己的实例。

`ColorSampler` 是最有教益的例子。$R$、$G$、$B$ 共享一个 $[0, 255]$ 进度，因此过冲无法偏移色相；alpha 保留完整缓动时间，因为它自成一个单通道范围，放进来会让本已不透明的 opacity 截断颜色的过冲。通道**饱和**而不是回绕，因为裸 `(byte)` 转换会把 $300$ 变成 $44$：

$$
\text{Channel}(v) = \begin{cases} 0 & v \le 0 \\ 255 & v \ge 255 \\ \lfloor v \rfloor & \text{otherwise} \end{cases}
$$

## 一次有限运行的墙钟时间

采样数**不**由 `FPS` 决定；它是时间轴推导的 $\text{elapsed} / D$，被 $1000 / \text{FPS}$ 毫秒的让出节流。因此一次时长 $D$ 的趟最多发出 $D \cdot \text{FPS} / 1000$ 个采样，每个 $O(P)$。自动反向使趟数翻倍；`LoopTime` 增加重复；`Repeat` 乘整条链。

$$
T_{\text{wall}} \approx \frac{D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])}{\text{rate}} \times R
$$

其中 $R$ 是最外层循环的 `Repeat` 迭代数（无 `Repeat` 的链 $R = 1$，`Repeat(count)` 的 $R = \text{count} + 1$），$\text{rate} = 1$ 除非 `Transition.SetRate` 改过 —— 速率缩放经过时间，因此它除墙钟时间而不改变每趟采样数。

## 逐帧分配

| 路径 | 每采样分配 |
|---|---|
| 进入 `Apply` 的缓动时间 | $0$ —— 每个目标一个缓存闭包，时间经 `Interlocked` 字段传递 |
| 数值 / 值类型采样器 | $0$ —— 计算并赋值 |
| 带 `working` 暂存的引用类型采样器 | 首个中间帧之后 $0$ —— 暂存创建一次并复用 |
| 等待 | 首帧之后 $0$ —— 每个循环一个 `Timer`，不是每帧一个 |

两个例外正是 `AUTO TEST` 要抓的：每帧必须分配框架对象的适配器采样器（混合非纯色 `WPF` `Brush` 是已记录的例子），以及产生框架拒绝的值的采样器 —— 这就是一致性套件既检查**结合点**（真实过渡运行）也检查算术的原因。

> 源：`Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionProperty.cs`、`BoundedProgress.cs`、`Eases.cs`、`NativeSamplers/{ColorSampler,SizeSampler,QuaternionSampler}.cs`、`Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,SamplerConformanceTests,EaseOvershootTests}.cs`、`Examples/Transition/AUTO TEST/Conformance/ClosedForm.cs`。
