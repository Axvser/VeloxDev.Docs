# 动态主题 — 准备一场带动画的切换

## 1. 安装平台插值器

`ThemeManager.Transition` 会通过平台接缝为每个目标解析一个 scheduler —— `InterpolatorCore.CreateScheduler(object target, ITransitionEffectCore effect)` —— 因为「用哪个 inspector、哪个 interpreter、哪个分发优先级来跑动画」正是与框架无关的核心层无法命名的那件事。接缝由适配器回答，因此请在首次带动画切换之前全局安装一次：

```csharp
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

这次调用**对带动画的切换是强制项，而且只对带动画的切换是强制项**。不安装它，切换依然会发生 —— 只是会立刻应用、没有动画、也不报错（未安装插值器时 `ThemeManager.RunSwitch` 退化为 `ApplyImmediately`）。`Jump<T>()` 从不需要它（见[带动画与即时切换](../01_带动画与即时切换/index.md)）。

`Interpolator` 是适配器类型，位于 `VeloxDev.TransitionSystem` 命名空间（`VeloxDev.WPF`、`VeloxDev.Avalonia`）。它的静态构造函数注册该框架的采样器 —— WPF 注册 `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D` 与 `Vector3D`；它的 `CreateScheduler` 只在收到的 effect 恰好是该平台自己的 `TransitionEffect` 时返回平台 scheduler，否则返回 `null`。只要有一个目标得到 `null`，整场切换就退化为瞬时应用。

该设置全局生效，所以两个规模示例都在 `App` 里设置一次（WPF 在 `OnStartup`、Avalonia 在 `OnFrameworkInitializationCompleted`），以保证任何元素注册之前它就已经就位。

**预期结果：** `SetPlatformInterpolator(new Interpolator())` 可对照适配器编译，之后的 `ThemeManager.Transition<T>(...)` 会做动画而不是瞬变。由 `ThemeTransitionTests.Switch_WithNoPlatformSeam_AppliesImmediately` 锁定 —— 它传入一个接缝回答 `null` 的插值器，并观察到切换立刻落地。

## 2. 决定每段动画从哪里出发

`StartModel`（`[Flags]` 枚举，默认 `Cache`）决定每个属性插值的起点：

- `StartModel.Cache` —— 该属性已缓存的值：先查实例的**活动**缓存（运行时覆盖，见[运行时覆盖与线程](../03_运行时覆盖与线程/index.md)），再查共享的静态缓存。这正是「从当前主题的值出发、到目标主题的值」这一语义的来源。
- `StartModel.Reflect` —— `PropertyInfo.GetValue(target)`：对象此刻恰好持有的值。

`ThemeManager` 会在启动之前把选定的起点写回目标，所以真正被当作起点动画的是缓存里那一份 —— 引擎自己的 `Prepare` 只能从目标上读起点。

```csharp
ThemeManager.StartModel = StartModel.Cache;
```

**预期结果：** 不设置时 `StartModel` 读回 `StartModel.Cache`。由 `ThemeBasicsTests.StartModel_DefaultIsCache` 与 `StartModel_FlagsEnum` 锁定。

## 3. 一处调用点

最简示例把上面几件事放进同一个方法，且在 `InitializeComponent()` 让窗口可用之后：

```csharp
private void LoadTheme()
{
    InitializeTheme(); // this call is required and must come after InitializeComponent()

    // [ Applies globally ]
    // If you do not use themed transitions, the interpolator does not need to be configured;
    // otherwise this call is mandatory.
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // [ Applies globally ]
    // When the theme changes, should the animation's starting state come from the cache, or
    // should reflection read the current state as the starting point?
    ThemeManager.StartModel = StartModel.Cache;
}
```

来源：`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs` 的 `LoadTheme`；Avalonia 版（`Examples/Theme/Avalonia Trimmed/Demo/Views/MainWindow.axaml.cs`）同名成员，方法体相同。

**预期结果：** `LoadTheme()` 之后窗口已注册、接缝已安装、起始模型已设定 —— 第一次 `Transition<T>` 就会做动画。

## 4. 选一个 effect

适配器在 `TransitionEffects` 里提供预设：`Theme`（0.46 秒）、`Hover`（0.32 秒）与 `Empty`（`TimeSpan.Zero`）。effect 会被每个目标在每一帧读取，因此请原样传入共享预设，并且不要在使用它的切换运行期间改动它。两个规模示例则自己构造一个足够长的 effect，好让控制按钮有东西可打断：

```csharp
// Long enough that pause and seek have something to interrupt.
private readonly TransitionEffect _effect = new() { Duration = TimeSpan.FromSeconds(3), FPS = 60 };
```

来源：`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的字段 `_effect`（Avalonia 示例的 `Views/MainWindow.axaml.cs` 声明了同样的字段）。`FPS` 是采样率上限，不是帧网格。

**预期结果：** `TransitionEffects.Theme.Duration` 为 0.46 秒，`TransitionEffects.Empty.Duration` 为 `TimeSpan.Zero`。
