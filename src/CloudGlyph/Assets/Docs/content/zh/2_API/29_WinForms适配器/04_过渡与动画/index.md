# 过渡与动画

命名空间：`VeloxDev.TransitionSystem`、`VeloxDev.Adapters.NativeSamplers`、`VeloxDev.WinForms.XamlAnimation`。

WinForms 适配器在 Easel 视觉之上闭合共享过渡引擎。流畅声明、链式与缓动家族与 Transition Animation 记录的接口相同；本页列出适配器的具体类型与 Easel 桥。

## 类：Transition

`public class Transition : TransitionCore` —— 共享效果声明的无类型基类。

## 类：Transition\<T\>

`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, NonPriority> where T : class`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Create()` | `Transition<T>` | 创建空过渡。 |
| `Effect(Action<TransitionEffect> effectSetter)` | `Transition<T>` | 配置效果。 |
| `Effect(TransitionEffect effect)` | `Transition<T>` | 使用给定效果。 |
| `Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null)` | `Transition<T>` | 设置属性目标。 |
| `Property(Expression<Func<T, int>>, int, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, double>>, double, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, float>>, float, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, decimal>>, decimal, object?)` | `Transition<T>` | 类型化重载。 |
| `Property(Expression<Func<T, Padding>>, Padding, object?)` | `Transition<T>` | 类型化重载。 |
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

类型化重载只是重载解析辅助；它们都把值存进 `State`。

## 类：State

`public class State : StateCore` —— 每次过渡的属性快照。

## 类：TransitionEffect

`public class TransitionEffect : TransitionEffectCore` —— 时长、缓动、FPS、循环与自动反向设置。

## 类：TransitionEffects

`public static class TransitionEffects`

| 成员 | 类型 | 默认 |
| --- | --- | --- |
| `Empty` | `TransitionEffect` | 零时长；值直接跳变。 |
| `Theme` | `TransitionEffect` | 0.46 秒。 |
| `Hover` | `TransitionEffect` | 0.32 秒。 |

## 类：Interpolator

`public class Interpolator : InterpolatorCore`

在静态构造函数中注册 Easel 与 `System.Drawing` 采样器：`Padding`、`Thickness`、`Easel.Brush`、`Matrix`、`Easel.Transform3D` 与 `RectangleF?`。

`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` 只在效果声明 `NonPriority` 时创建调度器。

## 类：TransitionScheduler / TransitionInterpreter / UIThreadInspector

| 类型 | 基类 | 公开接口 |
| --- | --- | --- |
| `TransitionScheduler` | `TransitionSchedulerCore<...>` | 仅继承的调度接口。 |
| `TransitionInterpreter` | `TransitionInterpreterCore<TransitionEffect>` | 继承的解释器接口；持有 `PostedFramePacer`。 |
| `UIThreadInspector` | `TransitionHostBase<NonPriority>` | `static void CaptureUIThread()`、`override bool IsAlive`、`override ThreadRef ThreadFor(object target)`。 |

`UIThreadInspector.CaptureUIThread()` 记录 WinForms UI 线程，之后的过渡据此编组。它不在 `Application.Run` 之前的 WinForms UI 线程上调用时抛 `InvalidOperationException`。

## 采样器

命名空间 `VeloxDev.Adapters.NativeSamplers`。每个采样器实现 `ISampler` 的 `NormalizeStart`、`NormalizeEnd` 与 `InsertFrame`。

| 类型 | 插值对象 |
| --- | --- |
| `BrushSampler` | Easel `Brush`。 |
| `MatrixSampler` | `System.Drawing.Drawing2D.Matrix`。 |
| `NullableRectangleFSampler` | `RectangleF?`。 |
| `PaddingSampler` | `Padding`。 |
| `ThicknessSampler` | `Easel.Controls.Thickness`。 |
| `Transform3DSampler` | `Easel.Transform3D`。 |

## 类：EaselAnimationBootstrap

`public static class EaselAnimationBootstrap` —— 命名空间 `VeloxDev.WinForms.XamlAnimation`。

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `EnsureRegistered()` | `void` | 宿主未提供后端时，装入 VeloxDev 动画器。 |

代码第一次执行本程序集时，模块初始化器会调用 `EnsureRegistered`。只为动画后端安装包、从不触碰其他类型的宿主，应在启动时主动调用一次。

### 示例

```csharp
EaselAnimationBootstrap.EnsureRegistered();
// Source: source
```

### 备注

- 桥使用 `Transition<EaselVisualElement>`，运行因此被登记，`TransitionCore.Exit` 能停掉它们。
- `CanAnimate` 查注册表前必须先跑 `Interpolator` 的静态构造函数；动画器会显式触发。

## 主题值转换器

面向 `System.Drawing` 的 `VeloxDev.DynamicTheme` 转换器列在[主题转换器](../05_主题转换器/index.md)。
