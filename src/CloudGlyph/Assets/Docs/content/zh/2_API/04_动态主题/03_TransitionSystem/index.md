# API — 动态主题 · 支撑引擎（TransitionSystem）

动态主题功能通过 TransitionSystem 引擎驱动其动画。`InterpolatorCore` 以及 `ITransitionEffectCore`/`IEaseCalculator` 契约与过渡动画功能共享；主题功能使用它们来采样主题属性值并控制切换时序。

> 命名空间说明：`ISampler`、`ISampleable`、`ITransitionEffectCore`、`IEaseCalculator` 与 `Eases` 声明于 `VeloxDev.TransitionSystem`；抽象的 `InterpolatorCore` 与具体的 `SamplerSet` 声明于 `VeloxDev.TransitionSystem.Abstractions`。

## 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 抽象类：`InterpolatorCore`

`public abstract class InterpolatorCore`

所有值采样器的基类 —— 先前的帧插值器层级（`IValueInterpolator`、`IInterpolable`、泛型 `InterpolatorCore<TOutputCore[, TPriorityCore]>` 形式、`InterpolatorOutputBase`）已移除，`InterpolatorCore` 现在是单一非泛型类。静态构造函数会为原始类型与 BCL 类型预注册原生采样器：`double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及（在 `NETSTANDARD2_0` 之外）`Vector2`、`Vector3`、`Vector4`、`Quaternion`。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`。

##### 静态成员

| 成员 | 签名 | 描述 |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampleable> NativeInterpolators { get; protected set; }` | 按类型注册的采样器表。 |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampleable? sampleable)` | 查找某类型的采样器。 |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampleable sampleable)` | 注册采样器（原子的「添加或更新」）。 |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampleable? sampleable)` | 移除采样器。 |

**实例成员：** `public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` —— 每次动画只归一化一次首/末帧：读取每个属性的当前值（start）与目标值（end），解析 `ISampleable`（按属性自定义 → 注册的原生 → 值本身是 `ISampleable`），并调用 `Normalize(start, end, options)` 得到无状态 `ISampler` 逐属性存入 `SamplerSet`。取代旧的 `Interpolate(...) IFrameSequenceCore` 实例方法。

**说明：**
- 平台 `Interpolator`（适配器）继承自非泛型 `InterpolatorCore`，并在其静态构造函数中注册平台采样器。
- `RegisterInterpolator` 是「后写者胜」且原子（`AddOrUpdate`）。

### 类：`SamplerSet`

`public sealed class SamplerSet`

已准备的每属性采样容器（取代 `IFrameSequence` + `InterpolatorOutputBase` + `FrameUpdaterSet`）。每个属性持有 `(ITransitionProperty, ISampler, start, end, options)`。非泛型：只持有 Core 级 inspector，优先级经 `IUIThreadInspectorCore.ProtectedInvoke` 的 `object?` 重载传递。动画的取消令牌经 `SetCancellation` 附加，使 `Apply` 具备原 `ICancellableFrameSequence` 的过期帧守卫。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/SamplerSet.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `Apply` | `public void Apply(object target, double t, object? priority = default)` | 经 UI 线程 marshal 后逐个调用 `sampler.Update(target, property, start, end, options, t)`；当动画被取消或应用不再存活时立即返回，因此已排队的过期帧永远不会覆盖重置结果。 |
| `CanSetValue` | `public bool CanSetValue()` | `inspector.IsAppAlive()` 时为 `true`。 |

## 命名空间：`VeloxDev.TransitionSystem`

### 接口：`ISampler`

`public interface ISampler { void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t); }`

无状态、线程安全、共享单例采样处理器：不返回值，直接更新属性。语义：`t <= 0` 写精确 `start`；`t >= 1` 写精确 `end`；`0 < t < 1` 时值类型算好即赋、引用类型**原地修改** `start` 现有实例（不 new）。取代 `IValueInterpolator` / `IInterpolable` / `IInPlaceSampler` / `IFrameUpdater`。

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`。

### 接口：`ISampleable`

`public interface ISampleable { ISampler Normalize(object? start, object? end, object? options); }`

可采样定义（类型级）：用户自定义类型实现它即可直接用于动画，无需注册采样器。`Normalize` 归一化 start/end/options——解释器创建并知晓 `FrameState` 时对每个动画属性调用一次，返回该类型的无状态 `ISampler`；`start` 为 target 上的现值（引用类型即现有实例，供原地修改），`end` 为目标值。取代 `IInPlaceSampler` / `IFrameUpdater` / `IFrameUpdaterProducer`（引用类型的原地修改逻辑现在在各自 `ISampler.Update` 内）。

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`。

### 接口：`ITransitionEffectCore`

`public interface ITransitionEffectCore`

描述过渡效果：帧率、时长、循环/缓动以及生命周期事件。

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
- 默认 `FPS` 为 60；默认 `Duration` 为零；默认 `Ease` 为 `Eases.Default`。
- `FPS` 是**最大采样率上限** —— 解释器的采样循环是 Stopwatch 驱动的（`t = elapsed / Duration`），不会按 `FPS` 逐帧步进；yield 间隔为 `1000 / FPS` ms。
- `TransitionEffectCore`（基实现）为适配器的 `TransitionEffect` 提供支撑。

### 接口：`IEaseCalculator`

`public interface IEaseCalculator { double Ease(double t); }`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs`。

**说明：**
- 实现把归一化时间 `t ∈ [0, 1]` 映射为缓动后的值。

### 静态类：`Eases`

`IEaseCalculator` 策略的工厂。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`。

| 成员 | 描述 |
|---|---|
| `Default` | `IEaseCalculator` — 线性（`t → t`）。 |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | 嵌套静态类，每个都暴露 `In`、`Out`、`InOut` 成员，返回 `IEaseCalculator`。 |

**说明：**
- `EaseDefault` 是 `Eases.Default` 背后的具体类。
- `ThemeManager.Jump` 的零时长程使用 `Eases.Default`。
