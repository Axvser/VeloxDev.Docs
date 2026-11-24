# 平台适配类型

每个适配器都在自己的框架上提供同一套角色：流式 `Transition<T>`、`State`、带平台采样器的 `Interpolator`、`TransitionEffect` 与 `TransitionEffects`，以及调度器/解释器/宿主三件套。下列公开形状以 WPF 适配器为准；其余六个适配器镜像这些名称与流式表面。

## VeloxDev.TransitionSystem（每个适配器）

### 类：Transition（非泛型）

非泛型入口，派生自 `TransitionCore`。其静态成员（`Pause`、`Resume`、`SetRate`、`Seek`、`Exit`、`Position`、`Cycle`、`IsPaused`、`Rate`）无需命名目标类型即可操作任意目标。

**签名：** `public class Transition : TransitionCore`

### 类：Transition<T>（泛型）

**签名：**
`public class Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, DispatcherPriority> where T : class`

`DispatcherPriority` 是 WPF 的优先级类型；Avalonia、WinUI 与 MAUI 使用各自的调度优先级类型，其余适配器提供自己的类型。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Create` | `static Transition<T> Create()` | 开始一条空链。 |
| `Effect` | `Transition<T> Effect(Action<TransitionEffect> effectSetter)` | 通过 setter 配置效果。 |
| `Effect` | `Transition<T> Effect(TransitionEffect effect)` | 使用给定效果。 |
| `Property<TValue>` | `Transition<T> Property<TValue>(Expression<Func<T, TValue>> propertyLambda, TValue newValue, object? interpolationOptions = null)` | 设置一个属性的终值；选项传给采样器。 |

WPF 适配器为目标框架的值类型增加了封闭重载，使 lambda 无需显式转换即可绑定。下表是 WPF 集合；各适配器声明其框架所需的对应版本。

| 值类型 | 说明 |
|---|---|
| `double`、`int`、`float`、`decimal` | 原语采样器 |
| `Point`、`Size`、`Rect`、`Vector`、`Color`、`Thickness`、`CornerRadius` | WPF 值类型 |
| `Point3D`、`Vector3D` | 3D 值类型 |
| `Brush?`、`DropShadowEffect?`、`Transform?` | 有专用采样器的引用类型 |
| `Transform` 集合 | 重载接收 `ICollection<Transform>`；单元素直接赋值以保留运行时类型，多元素包成 `TransformGroup` |
| `System.Drawing.Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF` | `System.Drawing` 对应类型 |
| `System.Numerics.Vector2`、`Vector3`、`Vector4`、`Quaternion` | `netstandard2.0` 上不包含 |

`interpolationOptions` 按属性存储，并原样传给 `ISampler.InsertFrame`。

### 类：State

`public class State : StateCore`——适配器的具体帧状态。

### 类：Interpolator

适配器的采样器注册表，派生自 `InterpolatorCore`。

**签名：** `public class Interpolator : InterpolatorCore`

静态构造函数注册平台采样器。WPF 注册 `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`Effect`（不是 `DropShadowEffect`，以便声明为 `Effect` 的属性也能解析）、`Point3D` 与 `Vector3D`。它覆盖 `CreateScheduler`，在效果属于该平台优先级时返回平台调度器。

### 类：TransitionEffect

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>`——WPF 效果，`Priority` 默认 `DispatcherPriority.Render`。

### 类：TransitionEffects

共享效果实例。

**签名：** `public static class TransitionEffects`

| 成员 | 类型 | 值 |
|---|---|---|
| `Empty` | `static TransitionEffect { get; set; }` | `Duration = 0` |
| `Theme` | `static TransitionEffect { get; set; }` | `Duration = 0.46 s` |
| `Hover` | `static TransitionEffect { get; set; }` | `Duration = 0.32 s` |

这些实例逐帧读取；使用它们的切换正在运行时不要修改。

### 类：TransitionInterpreter

`public class TransitionInterpreter : TransitionInterpreterCore<TransitionEffect, DispatcherPriority>`

### 类：TransitionScheduler

`public class TransitionScheduler : TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>`

### 类：UIThreadInspector

`public class UIThreadInspector : TransitionHostBase<DispatcherPriority>`——把目标映射到其 Dispatcher 并把工作投递回去的宿主。

## 适配器可用性

七个适配器都声明 `Transition`、`Transition<T>`、`State`、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`TransitionInterpreter`、`TransitionScheduler` 与 `UIThreadInspector`。

| 适配器 | 平台采样器类型（命名空间 `VeloxDev.Adapters.NativeSamplers`） |
|---|---|
| WPF | `BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`DropShadowEffectSampler`、`Point3DSampler`、`PointSampler`、`RectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler`、`Vector3DSampler`、`VectorSampler` |
| Avalonia | `BoxShadowsSampler`、`BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`GridLengthSampler`、`PixelPointSampler`、`PixelRectSampler`、`PixelSizeSampler`、`PointSampler`、`RelativePointSampler`、`RelativeRectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler` |
| WinUI | `BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`GridLengthSampler`、`PointSampler`、`ProjectionSampler`、`RectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler` |
| MAUI | `BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`PointFSampler`、`PointSampler`、`RectFSampler`、`RectSampler`、`ShadowSampler`、`SizeFSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler` |
| WinForms | `BrushSampler`、`MatrixSampler`、`NullableRectangleFSampler`、`PaddingSampler`、`ThicknessSampler`、`Transform3DSampler` |
| Razor | `StringSampler` |
| Jalium | `BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`PointSampler`、`RectSampler`、`SizeSampler`、`ThicknessSampler`、`Transform3DSampler`、`TransformSampler` |

## 示例

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle { RenderTransform = new TranslateTransform() };

Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.4d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
    .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
    .Effect(TransitionEffects.Hover)
    .Execute(box);

Transition.SetRate(box, 0.5d);
```

完整窗口见[过渡动画快速开始](../../../1_快速开始/12_过渡动画/index.md)。
