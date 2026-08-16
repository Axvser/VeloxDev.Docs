# API — 动态主题 · 支撑引擎（TransitionSystem）

动态主题功能通过 TransitionSystem 引擎驱动其动画。`InterpolatorCore` 以及 `ITransitionEffectCore`/`IEaseCalculator` 契约与过渡动画功能共享；主题功能使用它们来插值主题属性值并控制切换时序。

> 命名空间说明：`ITransitionEffectCore`、`IEaseCalculator` 与 `Eases` 声明于 `VeloxDev.TransitionSystem`；抽象的 `InterpolatorCore` 及其泛型派生形式声明于 `VeloxDev.TransitionSystem.Abstractions`。

## 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 抽象类：`InterpolatorCore`

`public abstract class InterpolatorCore : IFrameInterpolatorCore`

所有帧插值器的基类。静态构造函数会为原始类型与 BCL 类型预注册原生插值器：`double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及（在 `NETSTANDARD2_0` 之外）`Vector2`、`Vector3`、`Vector4`、`Quaternion`。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`。

##### 静态成员

| 成员 | 签名 | 描述 |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` | 按类型注册的值插值器表。 |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` | 查找某类型的插值器。 |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` | 注册插值器（原子的「添加或更新」）。 |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` | 移除插值器。 |

**实例成员：** `public abstract IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector);`

**泛型派生形式**（同样声明于 `VeloxDev.TransitionSystem.Abstractions`）：
- `public abstract class InterpolatorCore<TOutputCore> : InterpolatorCore, IFrameInterpolator where TOutputCore : IFrameSequence, new()`
- `public abstract class InterpolatorCore<TOutputCore, TPriorityCore> : InterpolatorCore, IFrameInterpolator<TPriorityCore> where TOutputCore : IFrameSequence<TPriorityCore>, new()`

**说明：**
- 平台 `Interpolator`（适配器）继承自 `InterpolatorCore<InterpolatorOutput, DispatcherPriority>`，并在其静态构造函数中注册平台类型。
- `RegisterInterpolator` 是「后写者胜」且原子（`AddOrUpdate`）。

## 命名空间：`VeloxDev.TransitionSystem`

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
- `ThemeManager.Jump` 的单帧使用 `Eases.Default`。
