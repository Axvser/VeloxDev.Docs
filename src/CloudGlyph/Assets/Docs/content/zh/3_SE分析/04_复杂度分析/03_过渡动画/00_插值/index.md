# 复杂度 — 过渡动画：插值

## 构建一次过渡（`.Property(...)` 调用）

$$
O(P \cdot \bar{k}) \;\Rightarrow\; O(P^2 \cdot k) \text{ per transition when the conflict check is counted}
$$

每个 `.Property(lambda, value, options)` 把 lambda 解析成一个 `TransitionProperty` —— 路径分段上的 $O(k)$，因为 `TransitionProperty.TryCreate` 只解包并遍历一次成员链 —— 把值（与可选 options）存进 `ConcurrentDictionary`（摊还 $O(1)$），随后跑父/子冲突检查，用 `IsDescendantOf` 双向比较新路径与**每一个**已声明键。每次比较在分段链上是 $O(k)$，所以声明一次过渡的全部 $P$ 条路径总代价是 $O(P^2 \cdot k)$ —— 对一次过渡携带的那几条路径可忽略，而这是把「一个对象、一条路径」变成构建期不变量而不是运行时惊喜的代价。

编译出的 getter/setter 委托在**首次读/写时惰性构建**（$O(k)$ 编译，一次）并复用。`FromProperty`（反射驱动的入口）按 `PropertyInfo` 记忆化，因此解析与编译对每个属性在进程里只付一次，而不是每次切换一次。

## 采样器解析

$$
O(1)\ \text{on a hit} \quad\Rightarrow\quad O(B + I)\ \text{on a miss}
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` 先在注册表里试精确类型（一次哈希查找）。未命中时它最近优先走基类链（$B$ 个祖先），然后走该类型的接口，保留全名按序（ordinal）最小的命中（$I$ 个接口）。接口显式排序，因为反射不保证顺序，所以决胜规则必须被点名。

这条链每个属性每次动画走一次，绝不逐帧：`Prepare` 每条已声明路径解析一次，而帧路径只读 `SamplerSet` 已持有的 `ISampler`。逐属性覆盖在两段之前加一次常数时间检查，而 `RegisterInterpolator` / `UnregisterInterpolator` 是原子的 `AddOrUpdate` / `TryRemove`，$O(1)$。

## 准备（`InterpolatorCore.Prepare`）

$$
O(P) + O\!\left(\sum_{j} m_j\right)
$$

`Prepare` 每分段跑一次。对 $P$ 条已记录路径，它把路径绑到目标（`BindTo` —— 无冻结索引实参时返回自身，否则 $O(k)$）、经编译后的 getter **在目标线程上**读当前值（$O(1)$）、解析一个 `ISampler`（上面那个三段）、调用一次 `NormalizeStart` / `NormalizeEnd`，并存一条条目。一个值类型 `ISampleable` 属性另加 $O(m_j)$，即声明成员数，每个成员一次注册表查找与一次取值。**不构建任何逐属性帧列表。**

## 一帧

趟位置是趟锚点沿源的距离：

$$
\text{rawT} = \frac{\text{ms}(\text{Timeline.Ticks} - \text{Run.PassAnchor})}{D}, \qquad D = \text{effect.Duration.TotalMilliseconds}
$$

$$
\text{easedT} = \begin{cases} 1 & \text{forward pass, } \text{rawT} \ge 1 \\[2pt] 0 & \text{reverse pass, } \text{rawT} \ge 1 \\[2pt] \text{Ease}(\text{rawT}) & \text{otherwise (forward)} \\[2pt] \text{Ease}(1 - \text{rawT}) & \text{otherwise (reverse)} \end{cases}
$$

而写出的值是采样器自己的事，但每个数值采样器都是一次线性插值：

$$
\text{value}(t) = s + (e - s) \cdot t
$$

注意 `easedT` **不被夹取**：`Back` 峰值约 $1.10$、`Elastic` 约 $1.37$，夹取会把两条曲线都压平。每个采样器自行决定越界的 $t$ 意味着什么。

每采样成本是 $O(P)$ —— 每条已准备条目一次 `InsertFrame`，各 $O(1)$（一次线性插值、一次逐分量插值或一次 `Slerp`）—— 外加缓动求值本身的 $O(1)$。

## 过冲的代价

缓动时间落在 $[0, 1]$ 之外是合法的，而它遭遇什么按值类别决定：

- **外推类**（`double`、`float`、`int`、`long`、`Point`、`PointF`、`Vector*`、`Rectangle` 的位置、`Thickness`）只是带着插值越过端点再回来。这就是为什么一次过渡的 `Duration` 与它的过冲彼此独立：200 px 行程上约 $\pm 3.8\%$ 的过冲约为 7.6 px，是常数成本。
- **受限通道类**（`Color`、`Size`、`SizeF`、`Rectangle`、`RectangleF`）经 `BoundedProgress`，它找出让每个已加入通道都留在范围内、且后来者绝不放松的最大进度。设通道为 $\{(s_j, e_j)\}$、界为 $[m, M]$：

$$
\text{progress} = \max\!\Big(t \; \text{clamped iteratively:} \; \forall j,\; \frac{\min(M - s_j,\; m - s_j)}{e_j - s_j} \le \text{progress} \le \frac{\max(M - s_j,\; m - s_j)}{e_j - s_j}\Big)
$$

`Add` 把它实现为每通道两次比较，因此整组是 $C$ 个通道的 $O(C)$ —— 常数，且加通道的顺序无关，因为 `Add` 只会收紧。该组剩余的过冲被丢弃。对 $[0, 1]$ 内的缓动时间，结果恰是那个时间，因此范围内的动画只付这次比较、别无所付。
- **固定范围类**（`Quaternion`）根本无法过冲：`Quaternion.Slerp` 定义在 $[0, 1]$ 上，且采样器在恰好 $t = 0$ / $t = 1$ 时返回调用方自己的实例。

`ColorSampler` 的情形最有教益。$R$、$G$、$B$ 共享一个 $[0, 255]$ 进度，因此过冲不能改变色相；alpha 保留完整缓动时间，因为它自成一个单通道范围，放进来会让本已不透明的 opacity 截断颜色的过冲。通道**饱和**而不是回绕，因为裸 `(byte)` 转换会把 $300$ 变成 $44$：

$$
\text{Channel}(v) = \begin{cases} 0 & v \le 0 \\ 255 & v \ge 255 \\ \lfloor v \rfloor & \text{otherwise} \end{cases}
$$

## 一次有限运行的墙钟时间

采样次数**不**由 `FPS` 决定；它是由时间轴派生的 $\text{elapsed} / D$，被 $1000 / \text{FPS}$ 毫秒的让出节流。一段时长 $D$ 的趟因此至多发出 $D \cdot \text{FPS} / 1000$ 次采样，各 $O(P)$。自动反向让趟数翻倍；`LoopTime` 增加重复；`Repeat` 让链倍增。

$$
T_{\text{wall}} \approx \frac{D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])}{\text{rate}} \times R
$$

其中 $R$ 是最外层循环的 `Repeat` 迭代次数（无 `Repeat` 的链 $R = 1$，`Repeat(count)` 则 $R = \text{count} + 1$），而除非 `Transition.SetRate` 改过，$\text{rate} = 1$ —— 速率缩放已流逝时间，因此它除墙钟而不动每趟采样次数。

## 逐帧分配

| 路径 | 每采样分配 |
|---|---|
| 缓动时间进入 `Apply` | $0$ —— 每目标一个缓存闭包，时间经一个 `Interlocked` 字段传递 |
| 数值 / 值类型采样器 | $0$ —— 计算并赋值 |
| 带 `working` 暂存的引用类型采样器 | 首个中间帧之后 $0$ —— 暂存只创建一次并复用 |
| 等待 | 首帧之后 $0$ —— 每条循环一个 `Timer`，不是每帧一个 |

两个例外正是 `AUTO TEST` 存在要抓的：一个必须逐帧分配框架对象的适配器采样器（混合非纯色 WPF `Brush` 是有记录的那个），以及一个产出框架拒绝的值的采样器 —— 这就是一致性套件同时检查**接缝**（一条真实过渡运行）与算术的原因。

> 来源：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`、`TransitionInterpreter.cs`、`TransitionProperty.cs`、`BoundedProgress.cs`、`Eases.cs`、`NativeSamplers/{ColorSampler,SizeSampler,QuaternionSampler}.cs`、`Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,SamplerConformanceTests,EaseOvershootTests}.cs`、`Examples/Transition/AUTO TEST/Conformance/ClosedForm.cs`。
