# 动态主题 — 带动画与即时切换

## 1. 带动画切换 —— `Transition`

```csharp
public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme
public static async void Transition(Type themeType, ITransitionEffectCore effect)
```

`Transition<T>` 转发到 `Type` 重载，后者是 `async void`：当每个已注册目标都被「准备、写起点、排程」之后它就返回给调用方 —— 它的第一个 await 是对各目标 run 的汇合 —— 并且只在 run 真正落地时才推进 `ThemeManager.Current`。正因为是 `async void`，run 内部的异常通过 `Debug.WriteLine` 报告而不是抛给调用方；没有任何东西 await 这次调用。

两种切换方式共用同一组前置判断：目标主题就是当前主题、或类型未实现 `ITheme` 时，切换在产生任何效果之前就被拒绝。

```csharp
private static void ReverseThemeWithAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
    {
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    }
    else
    {
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
    }
}
```

来源：`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs` 的 `ReverseThemeWithAnimation`（`Examples/Theme/Avalonia Trimmed/Demo/Views/MainWindow.axaml.cs` 中完全一致）。

**预期结果：** 已映射属性在 `TransitionEffects.Theme`（0.46 秒）内插值到目标主题，并精确落在声明的终值上 —— 末帧被钉在终点，因此结果不依赖缓动曲线是否恰好返回 `1`。由 `ThemeTransitionTests.Switch_LandsExactlyOnTheTargetValue` 锁定。

## 2. 即时切换 —— `Jump`

```csharp
public static void Jump(Type themeType)
public static void Jump<T>() where T : ITheme
```

`Jump(Type)` 是**同步 `void`** —— 它没有时间轴也没有 effect，整场切换在调用返回前就已结束。它会：

1. 先取消正在飞行的切换（`CancelActiveSwitch`）；
2. 向每个已注册目标发出 `ExecuteThemeChanging(old, new)`；
3. 通过 `ApplyImmediately` 写入所有目标值；
4. 推进 `ThemeManager.Current` 并发出 `ExecuteThemeChanged(old, new)`。

因为没有时间轴也没有 effect，`Jump` 不受平台 `ITransitionEffect<TPriority>` 类型的约束，也**不需要** `SetPlatformInterpolator` —— 它是自足的。同时它会跳过从未向 `ThemeManager` 注册过的目标。

```csharp
private static void ReverseThemeWithOutAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
    {
        ThemeManager.Jump<Light>();
    }
    else
    {
        ThemeManager.Jump<Dark>();
    }
}
```

来源：`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs` 的 `ReverseThemeWithOutAnimation`。

**预期结果：** 调用返回时已映射属性就持有目标主题的值；从未注册过的目标不会被写入。由 `ThemeTransitionTests.Jump_WritesTheTargetValue` 与 `Jump_SkipsAnUnregisteredTarget` 锁定。

## 3. 钩子与 `SetCurrent`

两条路径都会通知每个已注册 `IThemeObject` 的同两个成员：值开始变化前触发 `ExecuteThemeChanging(old, new)`，目标值应用后触发 `ExecuteThemeChanged(old, new)`。生成器把它们暴露为可实现的 partial 钩子 —— 实现它们本身就是全部的订阅机制，没有可挂处理函数的事件：

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

来源：`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`；Avalonia 版改为弹出一条窗口通知。

`ExecuteThemeChanged` 只对真正落地的切换触发。被后一次切换顶掉的切换 —— `Transition` 在新切换开始时取消正在运行的那一场 —— 既不推进 `Current` 也不宣告结束，因此 `OnThemeChanging` 被看到的次数可能多于 `OnThemeChanged`。规模示例故意把两个钩子打到同一行 UI 上，好让这个差别可见，并把被顶掉的切换标为 `被中断`。

`SetCurrent<T>()` 只设置 `ThemeManager.Current`，别的什么都不做：不触发回调、不写任何值。用它可以在任何元素注册之前预置起始主题 —— 两个规模示例都在 `App` 中、紧接安装插值器之后调用它，好让每个元素初始化时应用的值就是该主题的值。

**预期结果：** 每次落地的切换都会以新旧主题类型各调用一次 `OnThemeChanged`；`SetCurrent<Dark>()` 会翻转 `ThemeManager.Current` 而不触碰已注册对象。由 `ThemeBasicsTests.ThemeManager_SetCurrent_Changes` 锁定。
