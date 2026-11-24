# 过渡与主题

命名空间：`VeloxDev.TransitionSystem`、`VeloxDev.Adapters.NativeSamplers`、`VeloxDev.DynamicTheme`。

Razor 适配器在 `NonPriority` 上运行共享过渡引擎，并注册一个字符串采样器，因此以 CSS 字符串写出的颜色也能动画。主题转换器产出 Razor 视图可渲染的值。

## 类：Transition

`public class Transition : TransitionCore` —— 共享效果声明的无类型基类。

## 类：Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, NonPriority> where T : class`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Create()` | `Transition<T>` | 创建空过渡。 |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | 配置效果。 |
| `Effect(TransitionEffect effect)` | `Transition<T>` | 使用给定效果。 |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, string?>>, string?, object?)` | `Transition<T>` | 字符串/CSS 颜色目标。 |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, decimal>>, decimal, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Point>>, Point, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, PointF>>, PointF, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Size>>, Size, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, SizeF>>, SizeF, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Color>>, Color, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Rectangle>>, Rectangle, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, RectangleF>>, RectangleF, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Vector2>>, Vector2, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Vector3>>, Vector3, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Vector4>>, Vector4, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Quaternion>>, Quaternion, object?)` | `Transition<T>` | 类型化重载。 |

## 类：State / TransitionEffect / TransitionEffects

| 类型 | 基类 | 公开接口 |
| --- | --- | --- |
| `State` | `StateCore` | 每次过渡的属性快照。 |
| `TransitionEffect` | `TransitionEffectCore` | 时长、缓动、FPS、循环与自动反向设置。 |
| `TransitionEffects` | static | `Empty`（零时长）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。 |

## 类：Interpolator

`public class Interpolator : InterpolatorCore`

在静态构造函数中为 `string` 注册 `StringSampler`。

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` 只为 `NonPriority` 效果创建调度器。

## 类：TransitionScheduler / TransitionInterpreter / UIThreadInspector

| 类型 | 基类 | 公开接口 |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | 继承的调度接口。 |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect>` | 继承的解释器接口。 |
| `UIThreadInspector` | `TransitionHostBase<NonPriority>` | `static void CaptureUIThread()`、`static void NotifyShutdown()`、`override bool IsAlive`、`override ThreadRef ThreadFor(object target)`。 |

`CaptureUIThread()` 记录渲染线程；`NotifyShutdown()` 把宿主标为已停止，挂起的调度器随之结束。Blazor 宿主应在电路开始与结束时各调用一次。

## 类：StringSampler

`public class StringSampler : ISampler` —— 命名空间 `VeloxDev.Adapters.NativeSamplers`。

实现 `NormalizeStart`、`NormalizeEnd` 与 `InsertFrame`。它逐通道插值 CSS 颜色字符串（3/4/6/8 位十六进制、`rgb()`、`rgba()` 或已知颜色名）；非颜色字符串保持起值直到终点帧。

## 主题转换器

命名空间 `VeloxDev.DynamicTheme`。每个实现 `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`，无法转换时返回 `null`。

| 转换器 | 输出 | 接受的参数 |
| --- | --- | --- |
| `DoubleConverter` | `double` | `double`、`int`、`float`、不变文化数字字符串，或任意 `IConvertible`。 |
| `StringConverter` | `string?` | `parameters[0]?.ToString()`。 |
| `IntConverter` | `int` | `int`、`double`、`float`、不变文化数字字符串，或任意 `IConvertible`。 |
| `BoolConverter` | `bool` | `bool`、可解析字符串，或 `int`（`0` 为 false）。 |

### 示例

```csharp
var transition = Transition<MyViewModel>.Create()
    .Effect(TransitionEffects.Theme)
    .Property(vm => vm.Accent, "#FF38BDF8");
// Source: source
```
