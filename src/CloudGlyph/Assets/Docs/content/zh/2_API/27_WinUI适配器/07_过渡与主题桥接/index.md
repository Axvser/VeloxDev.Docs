# 过渡与主题桥接

WinUI 适配器贡献过渡管道与运行时主题值转换器的平台一半。它们的成员级 API 属于过渡动画与运行时主题功能；本页列出此程序集提供的类型。

## 命名空间

- `VeloxDev.TransitionSystem` —— 过渡管道的闭合。
- `VeloxDev.Adapters.NativeSamplers` —— WinUI 采样器。
- `VeloxDev.DynamicTheme` —— 主题值转换器。

均位于程序集 `VeloxDev.WinUI`。

## 过渡系统

| 类型 | 职责 |
| --- | --- |
| `Transition` | 非泛型过渡声明基类。 |
| `Transition<T>` | 以目标类型闭合的类型化声明。 |
| `TransitionEffect` / `TransitionEffects` | 效果声明与预定义效果（此适配器上是普通类，不是静态类）。 |
| `TransitionInterpreter` | 把声明应用到 WinUI 目标；此处为 `partial`。 |
| `TransitionScheduler<TTarget>` | 在 WinUI 调度器上驱动帧。 |
| `Interpolator` | 采样器分发。 |
| `UIThreadInspector` | 报告 UI 线程亲和性。 |
| `State` | 捕获的可动画状态。 |

### 原生采样器

`BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`GridLengthSampler`、`PointSampler`、`ProjectionSampler`、`RectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler`。

## 主题转换器

| 类型 | 转换目标 |
| --- | --- |
| `BrushConverter` | 主题值 → `Brush` |
| `ColorConverter` | 主题值 → `Color` |
| `CornerRadiusConverter` | 主题值 → `CornerRadius` |
| `DoubleConverter` | 主题值 → `double` |
| `ObjectConverter` | 主题值 → `object` |
| `PointConverter` | 主题值 → `Point` |
| `ThicknessConverter` | 主题值 → `Thickness` |

```csharp
using Microsoft.UI.Xaml.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**预期结果：** WinUI 程序集提供这些类型，使面向 Core 写一次的声明在 WinUI 上运行。其特色采样器是 `GridLengthSampler` 与 `ProjectionSampler`；投影采样器用于动画化 WinUI 组合效果所需的 `Projection`。
