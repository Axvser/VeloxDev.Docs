# 过渡与主题桥接

WPF 适配器还承载两个 Core 系统的平台一半：过渡管道与运行时主题值转换器。它们的成员级 API 属于过渡动画与运行时主题这两个功能；本页列出 WPF 程序集贡献的类型，便于适配器读者不必翻工程就能找到。

## 命名空间

- `VeloxDev.TransitionSystem` —— 过渡管道的闭合。
- `VeloxDev.Adapters.NativeSamplers` —— WPF 采样器。
- `VeloxDev.DynamicTheme` —— 主题值转换器。

均位于程序集 `VeloxDev.WPF`。

## 过渡系统

| 类型 | 职责 |
| --- | --- |
| `Transition` | 非泛型过渡声明基类。 |
| `Transition<T>` | 以目标类型闭合的类型化声明。 |
| `TransitionEffect` / `TransitionEffects` | 效果声明与预定义效果集。 |
| `TransitionInterpreter` | 把声明应用到 WPF 目标。 |
| `TransitionScheduler` | 在 WPF 调度器上驱动帧。 |
| `Interpolator` | WPF 采样器分发。 |
| `UIThreadInspector` | 判断调用线程是否为 UI 线程。 |
| `State` | 捕获的可动画状态。 |

### 原生采样器

`BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`DropShadowEffectSampler`、`PointSampler`、`Point3DSampler`、`RectSampler`、`SizeSampler`、`ThicknessSampler`、`TransformSampler`、`VectorSampler`、`Vector3DSampler`。

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
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**预期结果：** WPF 程序集提供这些类型，使在 Core 中写一次的过渡或主题声明无需第二层平台包装即可在 WPF 上运行。采样器差异是 WPF 独有的 `DropShadowEffectSampler`、`Point3DSampler`、`VectorSampler` 与 `Vector3DSampler`；其他适配器提供不同的集合。
