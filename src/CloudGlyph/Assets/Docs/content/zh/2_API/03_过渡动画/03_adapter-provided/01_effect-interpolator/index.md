# Transition — 适配器：`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`

每个适配器提供一个 `Interpolator` 注册表子类、带平台默认值的效果描述符、一组预设效果，以及分段状态 `State`。全部位于适配器程序集的 `VeloxDev.TransitionSystem` 命名空间。

### 类：`Interpolator : InterpolatorCore`

适配器注册表子类。它继承引擎默认值（见 [01_abstractions](../../01_abstractions/index.md)），静态构造函数额外注册平台值类型：

| 适配器 | 平台采样器注册（`RegisterInterpolator(typeof(X), ...)`） |
|---|---|
| WPF | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D` |
| Avalonia | `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength` |
| WinUI | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Projection`、`Size`、`Rect`、`GridLength`、`Color` |
| MAUI | `Brush`、`Thickness`、`Point`、`PointF`、`CornerRadius`、`Transform`、`Color`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow` |
| WinForms | `Padding` |
| Razor | `string`（经 `StringSampler`） |
| Jalium | `Point`、`Rect`、`Thickness`、`CornerRadius`、`Size`、`Color`、`Brush`、`SolidColorBrush`、`Transform`、`Jalium.UI.Media.Media3D.Transform3D` |

**说明：**
- 被注册的采样器实现 `ISampler`，由同一适配器在 `PlatformAdapters/Samplers/*.cs` 下发布（各适配器程序集内命名空间 `VeloxDev.Adapters.NativeSamplers`）。画刷 / 变换类引用类型目标的插值不会修改快照共享的 start/end 实例（见 [00_transitionsystem/00_sampling-capture](../../00_transitionsystem/00_sampling-capture/index.md) 的 `ISampler` 契约）。
- 注册是*叠加于* `InterpolatorCore` 静态构造函数预置的引擎默认采样器之上——因此数值、`System.Drawing` 与（非 `netstandard2.0`）`System.Numerics` 类型总能插值。

### 类：`TransitionEffect` — 优先级默认值

各适配器的效果子类 `TransitionEffectCore`（MAUI、WinForms、Razor）或 `TransitionEffectCore<TPriorityCore>`（WPF、Avalonia、Jalium、WinUI）。存在优先级时设置覆盖基类零值的默认值：

| 适配器 | 基类型 | 默认 `Priority` |
|---|---|---|
| WPF | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Avalonia | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Jalium | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| WinUI | `TransitionEffectCore<DispatcherQueuePriority>` | `DispatcherQueuePriority.High` |
| MAUI / WinForms / Razor | `TransitionEffectCore` | —（无优先级） |

全部时序成员（`Duration`、`IsAutoReverse`、`LoopTime`、`Ease`、`FPS`）继承自 `TransitionEffectCore`（见 [01_abstractions](../../01_abstractions/index.md)）。

### 类：`TransitionEffects` — 预设

每适配器一个效果工厂，暴露三个读写静态预设：

```csharp
public static class TransitionEffects       // WinUI 上为实例类，但静态成员相同
{
    public static TransitionEffect Empty { get; set; }   // Duration = 0
    public static TransitionEffect Theme { get; set; }   // Duration = 0.46 s
    public static TransitionEffect Hover { get; set; }   // Duration = 0.32 s
}
```

**说明：**
- 除 WinUI 外，每个适配器的 `TransitionEffects` 都是 `static class`。WinUI 上该类型是普通类，但其成员仍是静态的，用法一致。
- *验证依据：* WPF 示例 `Animation0`/`CreateResetRec0` 传入 `.Effect(TransitionEffects.Empty)`。

### 类：`State : StateCore`

`StateCore` 的空子类；它是适配器 `Transition<T>` 所用的 `TStateCore` 类型参数，因此 `transition.GetState()` 返回这个具体 `State`（一个 `IFrameState`）。全部行为继承自 `StateCore`（见 [01_abstractions](../../01_abstractions/index.md)）。
