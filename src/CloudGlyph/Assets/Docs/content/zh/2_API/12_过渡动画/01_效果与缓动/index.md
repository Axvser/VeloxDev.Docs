# 效果与缓动

效果携带时序、循环与生命周期事件；缓动曲线把归一化时间映射为进度。两者都在 `VeloxDev.TransitionSystem`。

## VeloxDev.TransitionSystem

### 接口：ITransitionEffectCore

**签名：** `public interface ITransitionEffectCore`

| 成员 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `FPS` | `int` | `60` | 目标帧率。 |
| `Duration` | `TimeSpan` | `TimeSpan.Zero` | 一趟的长度。 |
| `IsAutoReverse` | `bool` | `false` | 到达末尾后反向播放。 |
| `LoopTime` | `int` | `0` | 额外重复次数。 |
| `Ease` | `IEaseCalculator` | `Eases.Default` | 缓动曲线。 |

**事件：** `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`——均为 `EventHandler<TransitionEventArgs>`；`Warn`——`EventHandler<TransitionEventArgs<WarnStage, string>>`；`Error`——`EventHandler<TransitionEventArgs<ErrorStage, Exception>>`。

**方法：** `InvokeAwake`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCompleted`、`InvokeCancled`、`InvokeFinally`、`InvokeWarn`、`InvokeError`（触发对应事件），以及 `ITransitionEffectCore Clone()`。

`Invoke*` 名称是接口自身的；`InvokeCancled` 保留历史拼写。

### 接口：ITransitionEffect<TPriorityCore>

**签名：** `public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Priority` | `TPriorityCore { get; set; }` | 调度优先级。 |
| `Clone` | `new ITransitionEffect<TPriorityCore> Clone()` | 效果的副本。 |

### 类：TransitionEffectCore

默认效果，携带 `NonPriority` 优先级。

**签名：** `public class TransitionEffectCore : ITransitionEffectCore, ITransitionEffect<NonPriority>`

公开成员：`FPS`（60）、`Duration`（0）、`IsAutoReverse`（`false`）、`LoopTime`（0）、`Ease`（`Eases.Default`）、十个事件、九个 `Invoke*` 方法与 `Clone()`。`Priority` 成员为显式实现，始终是 `default`。

### 类：TransitionEffectCore<TPriorityCore>

适配器派生用的强类型基类。

**签名：** `public class TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Priority` | `virtual TPriorityCore Priority { get; set; }` | 平台调度优先级。 |
| `Clone` | `new ITransitionEffect<TPriorityCore> Clone()` | 复制时序、循环与处理器。 |

### 接口：IEaseCalculator

**签名：** `public interface IEaseCalculator`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Ease` | `double Ease(double t)` | 把 `[0,1]` 内的归一化时间 `t` 映射为进度。`Back` 与 `Elastic` 可能离开 `[0,1]`。 |

### 类：Eases

内置曲线。每个属性返回一个新的计算器，因此一条曲线可赋给多个效果而互不共享状态。

**签名：** `public static class Eases`

| 家族 | 成员 |
|---|---|
| `Eases.Default` | 恒等 |
| `Sine` | `In`、`Out`、`InOut` |
| `Quad` | `In`、`Out`、`InOut` |
| `Cubic` | `In`、`Out`、`InOut` |
| `Quart` | `In`、`Out`、`InOut` |
| `Quint` | `In`、`Out`、`InOut` |
| `Expo` | `In`、`Out`、`InOut` |
| `Circ` | `In`、`Out`、`InOut` |
| `Back` | `In`、`Out`、`InOut` |
| `Elastic` | `In`、`Out`、`InOut` |
| `Bounce` | `In`、`Out`、`InOut` |

每个嵌套家族都是 `static class`，其 `In`、`Out`、`InOut` 属性返回 `IEaseCalculator`。

### 曲线类

`Eases` 的每个成员构造下列公开类之一。它们都实现 `IEaseCalculator` 并暴露 `double Ease(double t)`。

| 家族 | 类 |
|---|---|
| Default | `EaseDefault` |
| Sine | `EaseInSine`、`EaseOutSine`、`EaseInOutSine` |
| Quad | `EaseInQuad`、`EaseOutQuad`、`EaseInOutQuad` |
| Cubic | `EaseInCubic`、`EaseOutCubic`、`EaseInOutCubic` |
| Quart | `EaseInQuart`、`EaseOutQuart`、`EaseInOutQuart` |
| Quint | `EaseInQuint`、`EaseOutQuint`、`EaseInOutQuint` |
| Expo | `EaseInExpo`、`EaseOutExpo`、`EaseInOutExpo` |
| Circ | `EaseInCirc`、`EaseOutCirc`、`EaseInOutCirc` |
| Back | `EaseInBack`、`EaseOutBack`、`EaseInOutBack` |
| Elastic | `EaseInElastic`、`EaseOutElastic`、`EaseInOutElastic` |
| Bounce | `EaseInBounce`、`EaseOutBounce`、`EaseInOutBounce` |

`Back` 与 `Elastic` 刻意过冲。采样器必须接受大于 1 的进度；夹住它的值类型会丢失过冲。

### 类：TransitionEventArgs

不携带阶段专有值的事件载荷，扩展 `TimeLineEventArgs`（`Handled`、`DeltaTime`、`TotalTime`）。

**签名：** `public class TransitionEventArgs : TimeLineEventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Loop` | `int { get; internal set; }` | 当前段正在播放的重复序号，从 0 开始。 |
| `Cycle` | `long { get; internal set; }` | 该目标累计播放的段数。 |

### 类：TransitionEventArgs<TStage, TValue>

`Warn` 与 `Error` 的载荷。

**签名：** `public class TransitionEventArgs<TStage, TValue> : TransitionEventArgs`（命名空间 `VeloxDev.TransitionSystem`）

| 成员 | 类型 | 说明 |
|---|---|---|
| `Stage` | `TStage` | 报告步骤。 |
| `Value` | `TValue` | `Warn` 的消息，`Error` 的异常。 |

### 枚举

**`ErrorStage`：** `Sampling`、`Run`、`Marshaling`、`Awake`、`Prepare`、`Start`、`Update`、`LateUpdate`、`Completed`、`Canceled`、`Finally`。前五个是引擎自身步骤；其余表示该事件的订阅者抛出异常。

**`WarnStage`：** `Unreadable`、`Unsampled`、`Dropped`。每个阶段与实例最多报告一次。

## 示例

```csharp
using System;
using VeloxDev.TransitionSystem;

var effect = new TransitionEffect
{
    Duration = TimeSpan.FromSeconds(0.46),
    FPS = 60,
    Ease = Eases.Back.Out,
    IsAutoReverse = true,
    LoopTime = 2
};

effect.Warn += (_, e) => Console.WriteLine($"warn {e.Stage}: {e.Value}");
effect.Error += (_, e) => Console.WriteLine($"error {e.Stage}: {e.Value.Value}");
```

`TransitionEffect` 是 WPF 适配器对 `TransitionEffectCore<DispatcherPriority>` 的子类；见[平台适配类型](../04_平台适配类型/index.md)。
