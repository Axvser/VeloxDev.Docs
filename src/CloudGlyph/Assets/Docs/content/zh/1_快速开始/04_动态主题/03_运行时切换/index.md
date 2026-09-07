# 动态主题 — 运行时切换

## 1. 准备带动画的切换

主题切换由 TransitionSystem 引擎对属性值逐帧插值。引擎要通过平台 `Interpolator` 为每个属性的运行时类型解析采样器，因此首次带动画切换前要先安装一个（该设置全局生效，只需调用一次）。通常在[声明与注册](../02_声明与注册/index.md)中与注册一并完成：

```csharp
private void LoadTheme()
{
    InitializeTheme();

    // 全局：仅带动画切换需要。Interpolator 是适配器提供的类型。
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // 全局：每次动画从哪里取起始值？
    ThemeManager.StartModel = StartModel.Cache;
}
```

`StartModel` 决定动画起始值（枚举 `StartModel`，默认 `Cache`）：`Cache` 从该属性已缓存的主题值起插值，`Reflect` 则通过反射读取对象当前属性值。`Interpolator` 与 `TransitionEffects` 来自你的平台适配器（命名空间 `VeloxDev.TransitionSystem`）；示例使用 `TransitionEffects.Theme` 预设：

```csharp
TransitionEffects.Theme.Duration // 0.46 秒
TransitionEffects.Empty.Duration // TimeSpan.Zero
```

**预期结果：** `ThemeManager.SetPlatformInterpolator(new Interpolator())` 可对照适配器编译，`StartModel` 读回 `StartModel.Cache`（由 `ThemeBasicsTests.StartModel_DefaultIsCache` 锁定）。

## 2. 带动画 vs 即时切换

用 `Transition<T>(effect)` **带动画**切换到另一主题：

```csharp
private static void ReverseThemeWithAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

或用 `Jump<T>()` **不带插值**地切换：

```csharp
private static void ReverseThemeWithOutAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

两者都会通知每个已注册的 `IThemeObject`：值开始变化前触发 `ExecuteThemeChanging(old, new)`，目标值应用后触发 `ExecuteThemeChanged(old, new)`。生成器把这两点暴露为可实现的 partial 钩子 —— 示例中的 `OnThemeChanged` 弹出一个消息框：

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

`SetCurrent<T>()` 只更新 `ThemeManager.Current`、不触碰任何已注册对象 —— 适合在窗口注册前预置起始主题。

**预期结果：** 点击切换按钮后，已映射属性在 `TransitionEffects.Theme`（0.46 秒）内动画到目标主题；`Jump<T>()` 立即应用目标值；partial 钩子以 `(oldValue, newValue)` 触发。

## 3. 运行时覆盖与 UI 线程说明

生成的 API 还允许你在运行时覆盖/恢复某个实例、某个主题下的值：

```csharp
// 覆盖 Light 下 Background 的值；若 Light 为当前主题则立即重新应用
SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" });

// 移除覆盖；恢复使用静态的 Light 值
RestoreThemeValue<Light>(nameof(Foreground));
```

`SetThemeValue<T>` 把针对主题 `T` 的实例级覆盖记入该实例的活动缓存，若 `T` 恰好是当前主题则立即重新应用属性；否则等切到 `T` 时再生效（活动值优先于静态 `ThemeCache` 值）。`GetStaticThemeCache()` 与 `GetActiveThemeCache()` 可查看两个缓存。

**UI 线程说明。** 桌面应用中，请在 **UI 线程**上应用初始主题并发起切换。`ThemeManager.Transition` 内部的动画循环每帧 await 后，会在发起切换时所在的同步上下文上恢复——通常是发起切换所在窗口的 dispatcher——因此每次逐帧属性写入都回到 UI 线程。若从不含 UI 同步上下文的线程发起切换，帧会在线程池线程上执行，对 UI 绑定属性不安全。`Jump<T>()` 不带插值地应用值，并且（在没有并发切换占用内部锁时）在调用线程上完成。

**预期结果：** 当 `Light` 为当前主题时，`SetThemeValue` 的覆盖立即可见；`RestoreThemeValue` 让属性回到其静态的 `Light` 值。
