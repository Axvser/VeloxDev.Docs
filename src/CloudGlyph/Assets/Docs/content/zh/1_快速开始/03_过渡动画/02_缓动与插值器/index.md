# Transition — 缓动与插值器

## 1. 选用内置缓动

`Eases`（命名空间 `VeloxDev.TransitionSystem`）是返回 `IEaseCalculator` 的静态工厂。把它赋给效果的 `Ease` 属性 —— `TransitionEffectCore.Ease` 默认为 `Eases.Default`（线性）：

| 分组 | `In` | `Out` | `InOut` |
|---|---|---|---|
| 线性 | `Eases.Default` | — | — |
| Sine / Quad / Cubic / Quart / Quint / Expo / Circ / Back / Elastic / Bounce | `Eases.{Group}.In` | `Eases.{Group}.Out` | `Eases.{Group}.InOut` |

**三种方向分别意味着什么。** `In` 起步慢、随后加速，`Out` 起步快、随后落定，`InOut` 两者兼有 —— 下面以 `Cubic` 分组为例画出，并以线性斜坡（`Eases.Default`）作为参照：

```plot
{
  "title": "Cubic — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x^3", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^3", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? 4*x^3 : 1 - (-2*x + 2)^3/2", "color": "#f472b6" }
  ]
}
```

**每一族都画了出来。** [缓动曲线图](00_缓动曲线图/index.md) 为每一族各给一张图（该族的 `In`、`Out`、`InOut` 同框），并把十个族的 `Out` 曲线画在同一坐标系里便于比较。

例如示例用到了 `Eases.Circ.InOut`、`Eases.Expo.Out`、`Eases.Back.Out` 与 `Eases.Bounce.Out`。所有内置 `Ease*` 类也都是 `public` 的，因此 `new EaseInOutCubic()` 等价于 `Eases.Cubic.InOut`。

```csharp
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> SlideAndFade =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Effect(e => e.Ease = Eases.Back.Out);   // 流式效果设置器
}
```

**预期结果：** 效果对象的 `Ease` 是 `Eases.Back.Out`；`Back` 曲线会先冲过目标再回弹落定，写入值前帧采样器会把 `t` 钳制到 `[0,1]`。

## 2. 定义自定义缓动

缓动就是一个方法 —— `double Ease(double t)`，把归一化时间 `t ∈ [0,1]` 映射为缓动后的值。实现 `IEaseCalculator` 并把实例赋给 `Effect.Ease`：

```csharp
using VeloxDev.TransitionSystem;

public sealed class FlashEase : IEaseCalculator
{
    public double Ease(double t)
    {
        // 在过渡开始处做一次闪动。
        return t < 0.5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2;
    }
}
```

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 1)
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(1),
        Ease = new FlashEase(),
    });
```

**预期结果：** 在这一秒的效果期间，透明度经由 `FlashEase.Ease` 采样：值先加速升高、末端趋稳，然后完成。

## 3. 定义或覆盖采样器（`ISampler`）

`Ease` 重塑*时间*，而采样器（`ISampler`）重塑归一化端点之间的*值*。采样器是无状态单例，含三个方法：

- `NormalizeStart(start, end, options)` —— 在 `t <= 0` 时写入的值（默认原样返回 `start`）。
- `NormalizeEnd(start, end, options)` —— 在 `t >= 1` 时写入的值（默认原样返回 `end`）。
- `InsertFrame(target, property, ref working, start, end, options, t)` —— 在缓动时间 `t` 插值 `start → end` 并写入目标。实现**绝不能修改** `start` / `end`（它们与快照共享）。

引擎核心注册表在 `InterpolatorCore`（`NativeInterpolators` 字典）中，覆盖 `double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及 —— `netstandard2.0` 之外 —— `Vector2/3/4`、`Quaternion`。每个 GUI 适配器再注册各自的框架采样器（例如 WPF 增加 `Brush`、`Thickness`、`CornerRadius`、`Transform`、`DropShadowEffect`、`Point3D`、`Vector3D`）。自定义采样器用静态注册表 API 增删：

```csharp
using VeloxDev.TransitionSystem;

public sealed class SmoothStepDoubleSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        if (t <= 0) { property.SetValue(target, start); return; }
        if (t >= 1) { property.SetValue(target, end); return; }

        var d1 = (double)(start ?? 0d);
        var d2 = (double)(end ?? d1);
        var s = t * t * (3 - 2 * t); // smoothstep：3t^2 - 2t^3
        property.SetValue(target, d1 + (d2 - d1) * s);
    }
}
```

```csharp
// 进程级可选：此后所有 double 类型属性都用 smoothstep 插值。
InterpolatorCore.RegisterInterpolator(typeof(double), new SmoothStepDoubleSampler());
// InterpolatorCore.UnregisterInterpolator(typeof(double), out _);  // 恢复默认
```

注册是按你写入的键「后写者胜」，但**查找并不是精确类型匹配**。`InterpolatorCore.TryGetInterpolator`（源码：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`）分三步解析属性类型：先**精确类型**，再**由近及远的基类**，最后**按全名（序数）排序的接口**。这条回退路径的存在理由：框架属性常常声明为适配器所注册类型的子类 —— WPF 注册的是 `Brush`，而属性可能声明为 `LinearGradientBrush` —— 只认精确匹配会让该属性悄悄不动（叶子是引用类型时，还会因此抛出 `TransitionPathUnsampleableException`）。由此有两条对自定义注册的结论：

- **注册通用类型。** 一旦注册了通用类型，它就必须处理整个家族，因为其下每个子类现在都会解析到它；而在已有基类或接口注册的前提下，再注册具体类型是多余的。
- **接口顺序只是决胜规则，不是偏好。** 接口排在最后并按键名排序，仅仅因为反射自身的顺序是未定义的：两个都匹配的接口谁胜出是任意的，但每次都胜出同一个则不是。

这次遍历**每个属性只在动画启动时走一次**（`InterpolatorCore.Prepare`），绝不逐帧执行。

旋转方向是不必编写采样器即可经 `Property` 传入的**逐属性选项**：表示角度的数值路径会尊重 `RotationDirection`（如 `RotationDirection.CounterClockWise`），因为 `DoubleSampler.InsertFrame` 会读取 `options` 参数并处理环绕（见 [定义状态快照](../03_声明状态/index.md)）。

**预期结果：** 注册后对 `typeof(double)` 的精确查找返回该采样器（后写者胜），因此下一次动画 `double` 类型属性即使用 smoothstep，直到你注销它 —— 反过来说，注册在基类或接口上的采样器现在也会服务其下每个属性类型。逐属性覆盖优先于注册表 —— 若只需某个属性以不同方式动画，先用 `.Property(...)` 再用 `TransitionCoreEx.Interpolator(propertyLambda, sampler)` 扩展附加。
