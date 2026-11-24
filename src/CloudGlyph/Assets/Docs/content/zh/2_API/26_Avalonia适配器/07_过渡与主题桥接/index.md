# 过渡与主题桥接

Avalonia 适配器贡献过渡管道与运行时主题值转换器的平台一半。它们的成员级 API 属于过渡动画与运行时主题功能；本页列出此程序集提供的类型。

## 命名空间

- `VeloxDev.TransitionSystem` —— 过渡管道的闭合。
- `VeloxDev.Adapters.NativeSamplers` —— Avalonia 采样器。
- `VeloxDev.DynamicTheme` —— 主题值转换器。

均位于程序集 `VeloxDev.Avalonia`。

## 过渡系统

| 类型 | 职责 |
| --- | --- |
| `Transition` | 非泛型过渡声明基类。 |
| `Transition<T>` | 以目标类型闭合的类型化声明。 |
| `TransitionEffect` / `TransitionEffects` | 效果声明与预定义效果。 |
| `TransitionInterpreter` | 把声明应用到 Avalonia 目标。 |
| `TransitionScheduler<TTarget>` | 在 Avalonia 调度器上驱动帧。 |
| `Interpolator` | 采样器分发。 |
| `UIThreadInspector` | 报告 UI 线程亲和性。 |
| `State` | 捕获的可动画状态。 |

### 原生采样器

`BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`BoxShadowsSampler`、`GridLengthSampler`、`PointSampler`、`PixelPointSampler`、`PixelRectSampler`、`PixelSizeSampler`、`RelativePointSampler`、`RelativeRectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler`。

## 主题转换器

| 类型 | 转换目标 |
| --- | --- |
| `BrushConverter` | 主题值 → `IBrush` |
| `ColorConverter` | 主题值 → `Color` |
| `CornerRadiusConverter` | 主题值 → `CornerRadius` |
| `DoubleConverter` | 主题值 → `double` |
| `ObjectConverter` | 主题值 → `object` |
| `PointConverter` | 主题值 → `Point` |
| `ThicknessConverter` | 主题值 → `Thickness` |

```csharp
using Avalonia.Controls.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**预期结果：** 面向 Core 写一次的过渡或主题声明可通过这些闭包在 Avalonia 上运行。Avalonia 独有的采样器是阴影、网格长度、像素与相对坐标几组；WPF 提供的列表不同。
