# 过渡与主题桥接

MAUI 适配器贡献过渡管道与运行时主题值转换器的平台一半。它们的成员级 API 属于过渡动画与运行时主题功能；本页列出此程序集提供的类型。

## 命名空间

- `VeloxDev.TransitionSystem` —— 过渡管道的闭合。
- `VeloxDev.Adapters.NativeSamplers` —— MAUI 采样器。
- `VeloxDev.DynamicTheme` —— 主题值转换器。

均位于程序集 `VeloxDev.MAUI`。

## 过渡系统

| 类型 | 职责 |
| --- | --- |
| `Transition` | 非泛型过渡声明基类。 |
| `Transition<T>` | 以目标类型闭合的类型化声明。 |
| `TransitionEffect` / `TransitionEffects` | 效果声明与预定义效果。 |
| `TransitionInterpreter` | 把声明应用到 MAUI 目标；此处为 `partial`。 |
| `TransitionScheduler` | 在 MAUI 调度器上驱动帧（此适配器上非泛型）。 |
| `Interpolator` | 采样器分发。 |
| `UIThreadInspector` | 报告 UI 线程亲和性。 |
| `State` | 捕获的可动画状态。 |

### 原生采样器

`BrushSampler`、`ColorSampler`、`CornerRadiusSampler`、`PointSampler`、`PointFSampler`、`RectSampler`、`RectFSampler`、`SizeSampler`、`SizeFSampler`、`ShadowSampler`、`ThicknessSampler`、`TransformSampler`。

带 `…F` 的采样器使用 `Microsoft.Maui.Graphics` 的浮点结构；`ShadowSampler` 为 MAUI 独有。

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
using Microsoft.Maui.Controls.Shapes;
using VeloxDev.TransitionSystem;

var transition = Transition<Rectangle>.Create()
    .Property(x => x.Opacity, 0.5);
```

**预期结果：** 面向 Core 写一次的声明可通过这些闭包在 MAUI 上运行。其特色采样器是浮点 `…F` 组与 `ShadowSampler`。
