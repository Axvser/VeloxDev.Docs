# 过渡动画 — 缓动与插值器

## 1. 选择内置缓动

`Eases`（命名空间 `VeloxDev.TransitionSystem`）是 `IEaseCalculator` 的静态工厂。把它赋给效果的 `Ease` 属性 —— `TransitionEffectCore.Ease` 默认是 `Eases.Default`（线性）：

| 组 | `In` | `Out` | `InOut` |
|---|---|---|---|
| linear | `Eases.Default` | — | — |
| Sine / Quad / Cubic / Quart / Quint / Expo / Circ / Back / Elastic / Bounce | `Eases.{Group}.In` | `Eases.{Group}.Out` | `Eases.{Group}.InOut` |

**三个方向的含义。** `In` 起步慢并加速，`Out` 起步快并收敛，`InOut` 两者兼有 —— 下图画出 `Cubic` 组，并以线性 `Eases.Default` 作参照：

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

**每个族都有图。** [缓动曲线](00_缓动曲线/index.md) 为每个族各画一张 —— 同族的 `In`、`Out`、`InOut` —— 另外把所有十个族的 `Out` 放在同一张图上比较。

例如 demo 使用 `Eases.Circ.InOut`、`Eases.Expo.Out`、`Eases.Back.Out` 与 `Eases.Bounce.Out`。每个内置 `Ease*` 类也都是 `public`，因此 `new EaseInOutCubic()` 等价于 `Eases.Cubic.InOut`。

```csharp
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> SlideAndFade =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800d)
            .Effect(e => e.Ease = Eases.Back.Out);   // fluent effect setter
}
```

**预期结果：** 得到一个 `Ease` 为 `Eases.Back.Out` 的效果；`Back` 曲线会越过目标再回落 —— 解释器把缓动后的值**不夹取**地交给采样器，因此由每个采样器决定能否外推（数值型可以）还是必须钉在端点。

## 2. 定义自定义缓动

缓动只有一个方法 —— `double Ease(double t)`，把归一化时间 `t ∈ [0,1]` 映射为缓动值。实现 `IEaseCalculator` 并把实例赋给 `Effect.Ease`：

```csharp
using VeloxDev.TransitionSystem;

public sealed class FlashEase : IEaseCalculator
{
    public double Ease(double t)
    {
        // A single light flash at the start of the transition.
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

**预期结果：** 在这一秒的效果期间，透明度经 `FlashEase.Ease` 采样，值先加速进入、接近终点时放缓，然后完成。

## 3. 定义或覆盖采样器（`ISampler`）

`Ease` 重塑*时间*；采样器（`ISampler`）在归一化端点之间重塑*值*。采样器是无状态单例，有三个方法：

- `NormalizeStart(start, end, options)` —— 在 `t <= 0` 写入的值（默认原样返回 `start`）。
- `NormalizeEnd(start, end, options)` —— 在 `t >= 1` 写入的值（默认原样返回 `end`）。
- `InsertFrame(target, property, ref working, start, end, options, t)` —— 在缓动时间 `t` 插值 `start → end` 并写入。实现**不得修改** `start` / `end`（它们与记录它们的过渡声明共享）。

引擎核心的注册位于 `InterpolatorCore` 的静态构造函数（注册表本身是私有的；只有 `RegisterInterpolator` / `UnregisterInterpolator` / `TryGetInterpolator` 能触达它），覆盖 `double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及在非 `netstandard2.0` 下的 `Vector2/3/4`、`Quaternion`。每个 GUI 适配器注册自己的框架采样器（例如 WPF 增加 `Brush`、`Thickness`、`CornerRadius`、`Transform`、`Effect`、`Point3D`、`Vector3D`）。自定义采样器经静态注册表 API 注册或移除：

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
        var s = t * t * (3 - 2 * t); // smoothstep: 3t^2 - 2t^3
        property.SetValue(target, d1 + (d2 - d1) * s);
    }
}
```

```csharp
// Process-wide opt-in: every double-typed property now interpolates with smoothstep.
InterpolatorCore.RegisterInterpolator(typeof(double), new SmoothStepDoubleSampler());
// InterpolatorCore.UnregisterInterpolator(typeof(double), out _);  // remove the override; double then has no sampler
```

注册对同一键是**最后写入者胜**，但**查找不是精确类型匹配**。`InterpolatorCore.TryGetInterpolator`（源：`Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs`）分三步解析属性类型：先**精确类型**，再**基类（由近及远）**，最后**接口（按全名序数排序）**。之所以有回退，是因为框架属性常常声明为适配器所注册类型的子类 —— WPF 注册 `Brush`，而属性可能声明为 `LinearGradientBrush` —— 只做精确匹配会让该属性无法动画（对引用类型末端还会以 `TransitionPathUnsampleableException` 失败）。由此有两条注册建议：

- **注册通用类型。** 通用类型必须处理整个家族，因为每个子类现在都会解析到它；一旦注册了基类或接口，具体类型注册就是多余的。
- **接口顺序是平局裁决，不是偏好。** 接口排最后，仅因反射自身顺序未定义而按名字排序：两个匹配接口谁赢是任意的，但每次都是同一个 —— 这点不是。

遍历**每个属性、每次动画开始时只跑一次**（`InterpolatorCore.Prepare`）—— 绝不逐帧。

旋转方向是唯一可以不写采样器就经 `Property` 传入的逐属性*选项*：表示角度的数值路径会遵守 `RotationDirection`（例如 `RotationDirection.CounterClockWise`），因为 `DoubleSampler.InsertFrame` 读取 `options` 实参并引导环绕（见[声明状态](../03_声明状态/index.md)）。

**预期结果：** 注册后，`typeof(double)` 的精确查找会返回你的采样器（最后写入者胜），下一次 `double` 属性的动画会使用 smoothstep，直到你注销它；反过来，注册在基类或接口上的采样器现在会服务其下所有属性类型。逐属性覆盖优先于注册表 —— 用 `TransitionCoreEx.Interpolator(propertyLambda, sampler)` 扩展（命名空间 `VeloxDev.TransitionSystem`）为单个属性指定不同采样器。
