# 过渡动画 — 适配器：`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`

每个适配器提供一个 `Interpolator` 注册表子类、一个带平台默认值的 `Effect` 描述符、一组预设 effect，以及一个 `State` 已声明状态容器。它们都在适配器程序集的 `VeloxDev.TransitionSystem` 命名空间里。

### 类：`Interpolator : InterpolatorCore`

适配器注册表子类。它继承引擎默认值（见 [abstractions](../../01_abstractions/01_引擎/index.md)），静态构造函数另外注册平台值类型：

| 适配器 | 平台采样器注册（`RegisterInterpolator(typeof(X), ...)`） |
|---|---|
| WPF | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`Effect`（`DropShadowEffectSampler`）、`Point3D`、`Vector3D` |
| Avalonia | `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength` |
| WinUI | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Projection`、`Size`、`Rect`、`GridLength`、`Color` |
| MAUI | `Brush`、`Thickness`、`Point`、`PointF`、`CornerRadius`、`Transform`、`Color`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow` |
| WinForms | `Padding` |
| Razor | `string`（经 `StringSampler`） |
| Jalium | `Point`、`Rect`、`Thickness`、`CornerRadius`、`Size`、`Color`、`Brush`、`SolidColorBrush`、`Transform`、`Jalium.UI.Media.Media3D.Transform3D` |

**说明：**
- 注册的采样器实现 `ISampler`，由同一适配器在 `PlatformAdapters/Samplers/*.cs` 下提供（各适配器程序集内的命名空间 `VeloxDev.Adapters.NativeSamplers`）。画刷 / 变换类引用目标被插值时不会修改过渡声明共享的起止实例（见 [transitionsystem/sampling-capture](../../00_transitionsystem/00_采样与捕获/index.md) 的 `ISampler` 契约）。
- WPF 注册**抽象基类** `Effect`，而不是具体的 `DropShadowEffect`：WPF 自己的 `UIElement.Effect` 依赖属性就声明为 `Effect`，而查找只向上走，注册具体类型会让所有声明为 `Effect` 的路径一条键都查不到、静默不被采样。这正是注册表的通用规则 —— 注册通用类型。
- 注册是在 `InterpolatorCore` 静态构造函数播下的引擎默认采样器**之外**追加，因此数值、`System.Drawing` 与（非 `netstandard2.0`）`System.Numerics` 类型始终能插值。

### 重写：`Interpolator.CreateScheduler`

每个适配器还重写 `InterpolatorCore.CreateScheduler`（见 [abstractions](../../01_abstractions/01_引擎/index.md)）。WPF、Avalonia、Jalium 一字不差地这么写：

```csharp
public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)
    => effect is ITransitionEffect<DispatcherPriority>
        ? (TransitionSchedulerCore)TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>.FindOrCreate(target)
        : null;
```

WinUI 换成 `DispatcherQueuePriority`；MAUI、WinForms、Razor 换成 `NonPriority`。它是主题系统赖以运行的接缝 —— 一次主题切换横跨多种运行时类型的目标，因此 Core 无法命名 `Transition<T>` 的类型实参，而构成一个调度器的宿主 / 解释器 / 优先级是只有平台知道的那一件事。`null` 分支是「这个 effect 不属于本平台」的诚实答案（把一个 `DispatcherPriority` 的 effect 交给 WinUI 的插值器），镜像调度器自己运行前所做的那次强制转换；调用方于是不带动画地完成切换，而不是启动一次什么都画不出来的运行。走 `FindOrCreate`——绝不 `new`——才把调度器登记在目标名下，使后来的 `Transition.Pause` / `Transition.Seek` / `Transition.Exit(target)` 能找得到它（见 [ui-inspector](../02_UI线程检查器/index.md)）。*核验：* 各适配器的 `PlatformAdapters/Interpolator.cs`。

### 类：`TransitionEffect` —— 优先级默认值

各适配器的 effect 派生 `TransitionEffectCore`（MAUI、WinForms、Razor）或 `TransitionEffectCore<TPriorityCore>`（WPF、Avalonia、Jalium、WinUI）。有优先级的地方，它设置一个覆盖基类零值的默认值：

| 适配器 | 基类型 | `Priority` 默认值 |
|---|---|---|
| WPF | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Avalonia | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Jalium | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| WinUI | `TransitionEffectCore<DispatcherQueuePriority>` | `DispatcherQueuePriority.High` |
| MAUI / WinForms / Razor | `TransitionEffectCore` | ——（无优先级） |

所有计时成员（`Duration`、`IsAutoReverse`、`LoopTime`、`Ease`、`FPS`）以及全部九个事件都继承自 `TransitionEffectCore`。除七个生命周期事件（`Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`）外，继承来的集合还包括两个**诊断**事件：

```csharp
var effect = new TransitionEffect { Duration = TimeSpan.FromSeconds(1) };

effect.Warn += (_, e) =>
    Console.WriteLine($"降级 @{e.Stage}：{e.Message}");   // 某帧被丢弃、某路径被跳过、属性无采样器

effect.Error += (_, e) =>
    Console.WriteLine($"失败 @{e.Stage}：{e.Exception}");  // 回调 / 采样器 / 宿主 / Prepare 抛异常
```

**说明：** 每个阶段每次运行至多报一次，因此一个采不到值的属性不会以帧率刷屏；在任一实参上置 `Handled = true` 即要求终止该趟（`TransitionEventArgs` 携带 `Stage`、`Message`、`Exception` —— 见 [timeline](../../04_timeline/index.md)）。什么都不报的运行是常态。

### 类：`TransitionEffects` —— 预设

各适配器的 effect 工厂，暴露三个可读写的静态预设：

```csharp
public static class TransitionEffects       // （WinUI 上是普通类，但成员仍是静态的）
{
    public static TransitionEffect Empty { get; set; }   // Duration = 0
    public static TransitionEffect Theme { get; set; }   // Duration = 0.46 秒
    public static TransitionEffect Hover { get; set; }   // Duration = 0.32 秒
}
```

**说明：**
- 除 WinUI 外，`TransitionEffects` 都是 `static class`。WinUI 上该类型是普通类但成员仍是静态的，用法一致。
- *核验：* WPF 演示 `Animation0`/`CreateResetRec0` 传入 `.Effect(TransitionEffects.Empty)`。

### 类：`State : StateCore`

`StateCore` 的空子类；它是适配器 `Transition<T>` 用的 `TStateCore` 类型实参，因此 `GetState()` 返回这个具体 `State`（一个 `IFrameState`）。所有行为继承自 `StateCore`（见 [abstractions](../../01_abstractions/00_构建器/index.md)）。
