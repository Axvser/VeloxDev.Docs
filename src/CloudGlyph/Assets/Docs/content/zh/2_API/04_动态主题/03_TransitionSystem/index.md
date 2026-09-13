# API — 动态主题 · 支撑引擎（TransitionSystem）

动态主题功能通过 TransitionSystem 引擎对主题属性做动画。一次主题切换完全不由 `ThemeManager` 计时：管理器自己按 `StartModel` 构建每个属性的起始/结束条目，然后把每个目标的 `StateCore` 交给平台的 `TransitionSchedulerCore`，由后者完成采样器解析与采样。本页记录 `ThemeManager` 实际消费的引擎表面；完整引擎由过渡动画功能记录。

> 引擎契约（`ITransitionProperty`、`ISampler`、`ISampleable`、`ITransitionEffectCore`、`IEaseCalculator`）位于 `VeloxDev.TransitionSystem`；基础类型与具体类型（`InterpolatorCore`、`TransitionSchedulerCore`、`TransitionCore`、`TransitionProperty`）位于 `VeloxDev.TransitionSystem.Abstractions`；共享 transport 的默认实现 `TimeSourceCore` 位于 `VeloxDev.Timing`。完整引擎参考位于过渡动画功能（`2_API/03_transition`）。

## 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 抽象类：`InterpolatorCore`

`public abstract class InterpolatorCore`

平台插值器的基类，也是静态的按类型采样器注册表的持有者。静态构造函数会预注册原生采样器：`double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及（在 `NETSTANDARD2_0` 之外）`Vector2`、`Vector3`、`Vector4`、`Quaternion`。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampler> NativeInterpolators { get; protected set; }` | 按类型注册的采样器表。 |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampler? sampler)` | 查找某类型已注册的采样器。 |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampler sampler)` | 注册采样器（原子的「后写者胜」）。 |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampler? sampler)` | 移除已注册的采样器。 |
| `Prepare`（实例、`virtual`，带优先级类型参数） | `public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspector<TPriorityCore> inspector)` | 把状态中的每个属性归一化进一个 `SamplerSet<TPriorityCore>`。由主题切换所走的 `TransitionSchedulerCore.Execute` 调用；`ThemeManager` 自己从不调用它。 |
| `CreateScheduler`（实例、`virtual`） | `public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` | 平台接缝：返回为 `target` 做动画的调度器；平台承载不了 `effect` 时返回 `null`。默认返回 `null`。 |

**说明：**
- `ThemeManager.PrepareSamplers` 通过 `InterpolatorCore.TryGetInterpolator` 按 `PropertyInfo.PropertyType` 解析属性的采样器。当该类型没有注册采样器时，该属性全程保持旧值，直到切换结束时才写入目标值。
- 平台适配器 `Interpolator` 继承 `InterpolatorCore`，在其静态构造函数中注册平台采样器，并重写 `CreateScheduler`（见 [04 PlatformAdapters](../04_平台适配器/index.md)）。
- `CreateScheduler` 之所以存在，是因为一场切换横跨许多运行时类型的目标，Core 无法为 `Transition<T>` 指名类型实参，而调度器由哪个 inspector、interpreter 与调度器优先级构成，是只有适配器知道的一件事。返回 `null` 对「该平台没有接入」和「该效果不属于该平台」都是诚实的答案；调用方随后做不带动画的切换，而不是启动一场画不出东西的运行。
- 重写必须走 `TransitionSchedulerCore<...>.FindOrCreate(target)`，不得直接构造调度器：只有那条路径会把它登记到目标名下，而后续的 `Transition.Pause` / `Seek` / `Exit` 正是靠它找到这个动画。

### 类：`TransitionSchedulerCore`

`public abstract class TransitionSchedulerCore : ITransitionSchedulerCore`

一场切换中每个目标的驱动者。`ThemeManager` 经 `InterpolatorCore.CreateScheduler` 为每个目标解析一个，并在其上运行该目标的 `StateCore`。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionScheduler.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | 从 `state` 准备出采样器集合，并运行解释器的采样循环。 |
| `Exit` | `void Exit()` | 取消该调度器上所有存活的动画。 |
| `Track` / `Untrack`（`internal`） | `void Track(TransitionRun run)` / `void Untrack(TransitionRun run)` | 按各自的 token source 登记一个 run，使后续的控制调用能找到它。 |

**说明：**
- 具体的平台类型是泛型 `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>`，适配器通过静态的 `FindOrCreate<T>(T source, bool CanMutualTask = true)` 创建它。
- `ThemeManager` 在 `Execute` 之前调用 `Track`、在切换结束时调用 `Untrack`：`Execute` 正是靠传进去的 token source 在调度器的活跃表里找回这个 run；没有登记过的 run 会在一条无人控制得住的时间轴上被采样。

### 类：`TimeSourceCore`

`public sealed class TimeSourceCore : ITimeSourceControl`

命名空间：`VeloxDev.Timing`。它是 `ITimeSourceControl` 的默认实现 —— 当多个动画必须共用同一条 transport 时，消费方传入的就是这个契约；创建它的是注册表调用 `TimerCore.CreateTimeSource<ITimeSourceControl>()`。

一条绝对的虚拟时间轴：它在哪里、以多快的速度前进，以及暂停时用来停住采样循环的闸门。`ThemeManager` 每场切换恰好创建一条 `ITimeSourceControl`，并把每个目标的 run 都锚定到它上面。

源码：`Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs`。

**说明：**
- 共用一条时间轴，正是既有控制面能原样作用于主题切换的原因：对任一个目标做暂停、定位或改速率都会移动整场切换，因为只有一个 transport 可移动。该控制面是同一命名空间下的 `TransitionCore` —— `Pause` / `Resume` / `Seek` / `SetRate` / `Position` / `Rate` / `Cycle` / `IsPaused` / `Exit`，每个都接一个目标。*验证依据：* `ThemeTransitionTests.Switch_EveryTargetIsAnchoredToTheSameTimeline`、`Switch_SeekIsReachableAndFinishesThePass`。
- `ThemeManager.CancelActiveSwitch` 会对它取消的每个 run 调用时间轴的 `Wake`（`internal`）：暂停中的循环停在时间轴的闸门上，而闸门不知道 token 这回事，少了这一步，被取消的切换会一直停在原地，直到有别的东西把它 resume 起来。

### 类：`TransitionProperty`

`public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

`ITransitionProperty` 的编译版 getter/setter 实现。属性路径由一个或多个 `PropertyInfo` 段组成；读写经由惰性编译的委托。当中间对象非空但其运行时类型与路径不匹配时，读返回哨兵 `UnreadablePath`，写返回 `false`，调用方据此跳过该属性而不是把它当作 null/identity 处理。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `UnreadablePath` | `public static readonly object UnreadablePath` | 路径对当前目标无效时 `GetValue` 返回的哨兵。 |
| `FromProperty` | `public static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | 单个属性的**记忆化**单段路径：同一个 `PropertyInfo` 永远得到同一个实例。 |
| `Members<TSource>` | `public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 从表达式构建可读可写的成员路径（供 `ISampleable` 使用）。 |
| `ReadableMembers<TSource>` | `public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 构建可读成员路径（供结构体 `ISampleable` 组装）。 |
| `Combine` | `public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix)` | 把两个路径拼接为一个。 |
| `TryCreate` | `public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | 把表达式树解析为路径。 |
| `Path` | `string Path` | 以点号连接的段名。 |
| `PropertyType` / `PropertyInfo` / `Segments` | `Type` / `PropertyInfo` / `IReadOnlyList<PropertyInfo>` | 类型、末段属性信息、完整段列表。 |
| `CanRead` / `CanWrite` | `bool` | 各段可读性 / 末段可写性。 |
| `GetValue` / `SetValue` | `object? GetValue(object target)` / `bool SetValue(object target, object? value)` | 编译版路径读写。 |

**说明：**
- `ThemeManager.PrepareSamplers` 用 `TransitionProperty.FromProperty(propertyInfo)` 包装每个动画属性，随后通过 `SetValue` 写入起始/结束值。
- `FromProperty` 是反射驱动的入口：主题系统在*每一场*切换中，为每个已注册目标的每个主题属性重建一条路径，而声明式路径只构建一次并存在字段里。因此它走一个静态的 `ConcurrentDictionary<PropertyInfo, TransitionProperty>`，返回**共享**实例而不重新构造，使每条路径的 getter/setter 表达式按属性编译一次，而不是每场切换编译一次。提交 `58ae23b3` 实测：在 1000 个双属性元素上，未记忆化的代价是首帧前约 1.6 s 的 UI 线程停顿与 29 MB 分配，记忆化后约为 10 ms 与 6 MB。
- 共享是安全的：路径不可变，而没有要冻结的索引实参时 `BindTo` 返回实例自身——这里永远如此。惰性编译是幂等的，并发首次使用最多编译两次、丢弃一次。

## 命名空间：`VeloxDev.TransitionSystem`

### 接口：`ITransitionProperty`

`public interface ITransitionProperty`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionProperty.cs`。

| 成员 | 签名 |
|---|---|
| `Path` | `string Path { get; }` |
| `PropertyType` | `Type PropertyType { get; }` |
| `PropertyInfo` | `PropertyInfo PropertyInfo { get; }` |
| `Segments` | `IReadOnlyList<PropertyInfo> Segments { get; }` |
| `CanRead` / `CanWrite` | `bool CanRead { get; }` / `bool CanWrite { get; }` |
| `GetValue` | `object? GetValue(object target)` |
| `SetValue` | `bool SetValue(object target, object? value)` |

### 接口：`ISampler`

`public interface ISampler`

无状态、线程安全的采样器。采样器通常是注册在 `InterpolatorCore.NativeInterpolators` 中的共享单例。一次运行开始时，`InterpolatorCore.Prepare` 对每个属性调用一次 `NormalizeStart` / `NormalizeEnd`，随后由解释器在每个采样帧调用一次 `InsertFrame`。

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | 在 `t <= 0` 时写入的值。可返回副本，使目标永不同名共享的起始实例。 |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | 在 `t >= 1` 时写入的值。同样可返回副本。 |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | 计算 `t ∈ [0, 1]` 处的插值帧并写入 `target` 上的 `property`。`working` 是每次动画可复用的临时对象（在首个中间帧经 `ref` 惰性创建）。 |

**说明：**
- 端点在 `InsertFrame` 内部处理；实现不得修改传入的 `start` / `end` 实参。
- 主题切换所用的采样器在 `InterpolatorCore.Prepare` 内部按属性类型经 `InterpolatorCore.TryGetInterpolator` 解析。

### 接口：`ISampleable`

`public interface ISampleable { IReadOnlyList<ITransitionProperty> GetAnimatableMembers(); object? CreateFrameValue(IReadOnlyList<object?> memberValues); }`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`。

**说明：**
- **只服务值类型（结构体）**：声明某个结构体的哪些成员可动画（一层）以及如何从插值后的成员重建一个值。供过渡动画功能的 `Prepare` 阶段用于没有注册采样器的结构体；引用类型不走这条路（用逐成员显式路径或专用 `ISampler`）。
- 该装配确实参与主题切换：调度器所运行的 `InterpolatorCore.Prepare` 在值类型没有注册采样器时会回退到结构体 `ISampleable` 装配。`ThemeManager` 自己只查注册表，且仅用于判断某属性有没有采样器（`ThemeManager.cs`，`PrepareSamplers`）。

### 接口：`ITransitionEffectCore`

`public interface ITransitionEffectCore`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionEffect.cs`。

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; set; }` |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }` |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| 事件 | `event EventHandler<TransitionEventArgs> Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` |
| 触发方法 | `void InvokeAwake(object, TransitionEventArgs)`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCompleted`、`InvokeCancled`、`InvokeFinally` |
| `Clone` | `ITransitionEffectCore Clone()` |

**说明：**
- 由于主题切换运行在过渡系统上，整个效果都会被尊重：`Duration` 与 `Ease` 决定一程的时长与缓动，`FPS` 限制采样率，`IsAutoReverse` 追加反程，`LoopTime` 重复，生命周期事件照常触发。*验证依据：* `ThemeTransitionTests.Switch_HonoursAutoReverseAndLoopTime`。
- 效果按传入原样使用，且被每个目标逐帧读取，因此它必须是平台自己的效果类型，且在使用它的切换运行期间不得被修改。效果类型还决定平台能否承载这场切换：`InterpolatorCore.CreateScheduler` 对不属于自己的 `ITransitionEffect<TPriority>` 返回 `null`。
- 基实现 `TransitionEffectCore` 的默认值：`FPS = 60`、`Duration = 0 ms`、`Ease = Eases.Default`、`IsAutoReverse = false`、`LoopTime = 0`。适配器预设见 [04 PlatformAdapters](../04_平台适配器/index.md)。

### 接口：`IEaseCalculator` 与静态类：`Eases`

`public interface IEaseCalculator { double Ease(double t); }`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs` 与 `Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`。

| 成员 | 描述 |
|---|---|
| `Eases.Default` | `IEaseCalculator` — 线性（`Ease(t) = t`，由 `EaseDefault` 支撑）。它是 `TransitionEffectCore.Ease` 的默认值；不带任何一程的 `ThemeManager.Jump` 从不读取它。 |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | 嵌套静态类，每个都暴露 `In`、`Out`、`InOut` 成员，返回 `IEaseCalculator`。 |

**说明：**
- 完整缓动目录记录在过渡动画功能的 Eases 章节（`2_API/03_transition`）。
