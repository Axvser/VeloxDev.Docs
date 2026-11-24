# 过渡系统

命名空间：`VeloxDev.TransitionSystem`、`VeloxDev.Adapters.NativeSamplers`。

Jalium 适配器在 `DispatcherPriority` 上闭合共享过渡引擎，并注册 Jalium 媒体采样器。该平台没有 `VeloxDev.DynamicTheme` 转换器集合。

## 类：Transition

`public class Transition : TransitionCore` —— 共享效果声明的无类型基类。

## 类：Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, DispatcherPriority> where T : class`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Create()` | `Transition<T>` | 创建空过渡。 |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | 配置效果。 |
| `Effect(TransitionEffect effect)` | `Transition<T>` | 使用给定效果。 |
| `Property<TValue>(Expression<Func<T, TValue>>, TValue, object?)` | `Transition<T>` | 泛型目标。 |
| `Property(Expression<Func<T, Brush?>>, Brush?, object?)` | `Transition<T>` | 画刷目标。 |
| `Property(Expression<Func<T, Transform?>>, ICollection<Transform>, object?)` | `Transition<T>` | 变换集合；单项直接赋值以保留运行时类型。 |
| `Property(Expression<Func<T, Transform3D?>>, Transform3D?, object?)` | `Transition<T>` | 3D 变换目标。 |
| `Property(Expression<Func<T, Point>>, Point, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Rect>>, Rect, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Thickness>>, Thickness, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, CornerRadius>>, CornerRadius, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Size>>, Size, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Color>>, Color, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | 类型化重载。 |

## 类：State / TransitionEffect / TransitionEffects

| 类型 | 基类 | 公开接口 |
| --- | --- | --- |
| `State` | `StateCore` | 每次过渡的属性快照。 |
| `TransitionEffect` | `TransitionEffectCore<DispatcherPriority>` | 时长、缓动、FPS、循环、自动反向与优先级。 |
| `TransitionEffects` | static | `Empty`（零时长）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。 |

## 类：Interpolator

`public class Interpolator : InterpolatorCore`

在静态构造函数中按精确类型注册：`Point`、`Rect`、`Thickness`、`CornerRadius`、`Size`、`Color`、`Brush`、`SolidColorBrush`、`Transform` 与 `Media3D.Transform3D`。`Brush` 与 `SolidColorBrush` 都注册，声明为任一类型的画刷属性都能动画。

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` 只为 `DispatcherPriority` 效果创建调度器。

## 类：TransitionScheduler / TransitionInterpreter / UIThreadInspector

| 类型 | 基类 | 公开接口 |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | 继承的调度接口。 |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect, DispatcherPriority>` | 继承的解释器接口。 |
| `UIThreadInspector` | `TransitionHostBase<DispatcherPriority>` | `override ThreadRef ThreadFor(object target)`。 |

宿主类型报告 `DispatcherPriority`，过渡因此经 Jalium 调度器编组。

## 采样器

命名空间 `VeloxDev.Adapters.NativeSamplers`。每个采样器实现 `ISampler` 的 `NormalizeStart`、`NormalizeEnd` 与 `InsertFrame`。

| 类型 | 插值对象 |
| --- | --- |
| `BrushSampler` | `Brush`（及 `SolidColorBrush`）。 |
| `ColorSampler` | `Color`。 |
| `CornerRadiusSampler` | `CornerRadius`。 |
| `PointSampler` | `Point`。 |
| `RectSampler` | `Rect`。 |
| `SizeSampler` | `Size`。 |
| `ThicknessSampler` | `Thickness`。 |
| `TransformSampler` | `Transform`。 |
| `Transform3DSampler` | `Media3D.Transform3D`。 |

### 示例

```csharp
var transition = Transition<MyCard>.Create()
    .Effect(TransitionEffects.Hover)
    .Property(card => card.CornerRadius, new CornerRadius(12));
// Source: source
```
