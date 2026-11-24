# 主题管理器

`ThemeManager` 保存当前主题、已注册主题对象的弱集合，以及正在进行的切换。命名空间 `VeloxDev.DynamicTheme`。

## VeloxDev.DynamicTheme

### 枚举：StartModel

选择切换从哪个值出发。

**签名：** `[Flags] public enum StartModel : int`

| 成员 | 值 | 含义 |
|---|---|---|
| `Reflect` | 1 | 从对象上读取属性当前值。 |
| `Cache` | 2 | 从当前主题的缓存值出发。默认值。 |

### 类：ThemeManager

**签名：** `public class ThemeManager`

**属性**

| 成员 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `Current` | `static Type { get; internal set; }` | `typeof(Dark)` | 当前主题。过渡与跳变路径只在切换落地后推进它。 |
| `StartModel` | `static StartModel { get; set; }` | `StartModel.Cache` | 切换如何取得起始值。 |

**方法**

| 成员 | 签名 | 说明 |
|---|---|---|
| `SetPlatformInterpolator<T>` | `static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore` | 一次性提供适配器插值器。没有它切换仍会落地，但立即完成、没有动画。 |
| `SetCurrent<T>` | `static void SetCurrent<T>() where T : ITheme` | 只设置 `Current`，不触碰任何已注册对象。 |
| `Register` | `static void Register(IThemeObject target)` | 弱引用地添加目标。由生成的 `InitializeTheme` 调用。 |
| `Unregister` | `static void Unregister(IThemeObject target)` | 移除目标。 |
| `Transition` | `static void Transition(Type themeType, ITransitionEffectCore effect)` | 把所有存活目标动画到 `themeType`。 |
| `Transition<T>` | `static void Transition<T>(ITransitionEffectCore effect) where T : ITheme` | 泛型形式。 |
| `Jump` | `static void Jump(Type themeType)` | 一次性写入所有终值；不需要插值器或效果。 |
| `Jump<T>` | `static void Jump<T>() where T : ITheme` | 泛型形式。 |

**行为说明**

- `Transition` 是 `async void` 表面：动画结束前就返回。调用方通过 `OnThemeChanged` 或效果的 `Completed` / `Finally` 事件观察完成。
- 新的过渡或跳变会取消上一次切换。每次切换前会清理不再被引用的目标；注册表是 `ConditionalWeakTable` / `WeakReference` 集合，因此已关闭窗口不会被保持存活。
- 一次切换中的每个目标锚定到同一条共享时间轴。对任一目标调用 `Transition.Pause`、`Resume`、`SetRate` 会移动整场切换；`Seek` 只重锚该目标的运行，`Exit` 只取消该目标的运行。
- 效果实例由每个目标逐帧读取。每次切换使用专用 `TransitionEffect`，或使用共享的 `TransitionEffects` 实例，并避免在使用它的切换运行期间修改它。
- 值没有采样器（或路径无法读取）的属性在动画期间被跳过，并在结束时写入；降级经效果的 `Warn` 事件报告。
- 被取代或取消的切换不会改变 `Current`；`OnThemeChanged` 也不会为未落地的切换运行。

### 生成的生命周期钩子顺序

| 步骤 | 钩子 |
|---|---|
| 切换开始 | `OnThemeChanging(oldTheme, newTheme)` |
| 动画（或跳变）写入值 | — |
| 切换落地 | `OnThemeChanged(oldTheme, newTheme)`，此时 `ThemeManager.Current` 已推进 |

## 示例

```csharp
using System;
using System.Windows.Controls;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.StartModel = StartModel.Cache;

// 动画切换。
ThemeManager.Transition<Light>(TransitionEffects.Theme);

// 瞬时切换。
ThemeManager.Jump<Dark>();

// 整场传输，按任一目标寻址。
Transition.Pause(window, IncludeMutual: true, IncludeNoMutual: true);
Transition.SetRate(window, 0.5d, IncludeMutual: true, IncludeNoMutual: true);
Transition.Exit(window, IncludeMutual: true, IncludeNoMutual: true);
```

`Interpolator` 与 `TransitionEffects` 是适配器类型；见[平台转换器](../02_平台转换器/index.md)，过渡侧见[平台适配类型](../../12_过渡动画/04_平台适配类型/index.md)。

## 错误处理

切换路径自行捕获失败。调度器或解释器的异常写入 `Debug`，切换不会落地（`Current` 不推进，已变化钩子不运行）。无效主题类型——不能赋给 `ITheme`，或等于 `Current`——被忽略并跳到当前主题。
