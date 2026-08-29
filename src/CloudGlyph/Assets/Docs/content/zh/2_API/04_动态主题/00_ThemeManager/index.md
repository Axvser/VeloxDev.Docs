# API — 动态主题 · ThemeManager

## 命名空间：`VeloxDev.DynamicTheme`

### 类：`ThemeManager`

主题状态与切换的静态入口。所有成员均为静态。活跃实例通过 `ConditionalWeakTable<IThemeObject, ...>` 加上 `List<WeakReference<IThemeObject>>` 跟踪，因此注册不会产生泄漏。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`。

##### 属性

| 名称 | 类型 | 描述 |
|---|---|---|
| `Current` | `Type` | 当前主题类型。默认：`typeof(Dark)`。setter 为 `internal`。 |
| `StartModel` | `StartModel` | 带动画的切换中，动画起始值的获取方式。默认：`StartModel.Cache`。 |

#### ThemeManager.SetPlatformInterpolator

**签名：**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| 参数 | 类型 | 描述 |
|---|---|---|
| `interpolator` | `T` | 平台插值器实例（如适配器的 `new Interpolator()`）。 |

**返回：** `void`

**示例：**
```text
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

**说明：**
- 带动画的主题过渡必需，注册一次即可。若未配置，`Transition<T>` 仍会运行，但没有已注册插值器的属性会退化为简单的两帧切换。

#### ThemeManager.SetCurrent

**签名：**
`public static void SetCurrent<T>() where T : ITheme`

**返回：** `void`

**示例：**
```text
// 来源：Test（ThemeBasicsTests.ThemeManager_SetCurrent_Changes）
ThemeManager.SetCurrent<Light>();
```

**说明：**
- 将 `Current` 设为 `typeof(T)`，且不触发任何主题变更回调。主要在内部使用；外部请优先使用 `Transition<T>` / `Jump<T>`。

#### ThemeManager.Register

**签名：**
`public static void Register(IThemeObject target)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `target` | `IThemeObject` | 支持主题的对象（通常由生成的 `InitializeTheme()` 自动注册）。 |

**返回：** `void`

**说明：**
- 将目标加入活跃缓存与 `WeakReference` 列表。对已注册的目标再次调用 `Register` 是无操作。
- 通过 `ConditionalWeakTable` 查找防止重复注册。

#### ThemeManager.Unregister

**签名：**
`public static void Unregister(IThemeObject target)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `target` | `IThemeObject` | 支持主题的对象。 |

**返回：** `void`

**说明：**
- 移除目标的活跃缓存条目，并从列表中移除其 `WeakReference`。

#### ThemeManager.Transition<T>

**签名：**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`

| 参数 | 类型 | 描述 |
|---|---|---|
| `effect` | `ITransitionEffectCore` | 过渡效果（FPS、时长、缓动）。 |

**返回：** `void`（异步）

**示例：**
```text
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**说明：**
- 委托给 `Transition(typeof(T), effect)`。
- 无效的主题类型会被忽略并输出调试信息。

#### ThemeManager.Transition(Type, ITransitionEffectCore)

**签名：**
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `themeType` | `Type` | 目标主题类型。 |
| `effect` | `ITransitionEffectCore` | 过渡效果（FPS、时长、缓动）。 |

**返回：** `void`（异步）

**异常：** 未声明 —— 无效的 `themeType`（`themeType == Current` 或不可赋值为 `ITheme`）会被忽略，并输出 `Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")`。

**说明：**
- 取消正在运行的过渡，清理失效的 `WeakReference`，然后对每个已注册对象调用 `ExecuteThemeChanging(old, new)`。
- 准备每属性采样器（`PrepareSamplers`），并驱动 Stopwatch 采样循环（`ExecuteTransition`），持续整个效果的时长。
- 最后一次采样后，设置 `Current = themeType`，并对每个已注册对象调用 `ExecuteThemeChanged(old, new)`。

#### ThemeManager.Jump<T>

**签名：**
`public static void Jump<T>() where T : ITheme`

**返回：** `void`

**示例：**
```text
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
ThemeManager.Jump<Dark>();
```

**说明：**
- 委托给 `Jump(typeof(T))`。无动画立即切换。

#### ThemeManager.Jump(Type)

**签名：**
`public static async void Jump(Type themeType)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `themeType` | `Type` | 目标主题类型。 |

**返回：** `void`（异步）

**异常：** 未声明 —— 无效的 `themeType` 会像 `Transition` 一样被忽略并输出调试信息。

**说明：**
- 运行零时长程（`durationMs = 0`），因此首次采样即 `rawT = 1`，所有属性都直接设置为目标主题的值，无插值。切换前触发 `ExecuteThemeChanging`，切换后触发 `ExecuteThemeChanged`。

---

## 枚举：`StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`。

| 值 | 描述 |
|---|---|
| `Reflect` | 通过反射（`PropertyInfo.GetValue`）读取对象当前属性值作为动画起始值。 |
| `Cache` | 使用当前主题的缓存值作为动画起始值。 |

**说明：**
- 默认是 `StartModel.Cache`（由 `ThemeBasicsTests.StartModel_DefaultIsCache` 验证）。
- 它是 `[Flags]` 枚举 —— `StartModel.Reflect | StartModel.Cache` 是合法的组合（由 `ThemeBasicsTests.StartModel_FlagsEnum` 验证）。

---

## 类：`Dark` / `Light`

`public class Dark : ITheme` — 实现 `ITheme` 的空标记类型。
`public class Light : ITheme` — 实现 `ITheme` 的空标记类型。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/Dark.cs`、`Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`。

**说明：**
- `ThemeManager.Current` 默认是 `typeof(Dark)`（由 `ThemeBasicsTests.Dark_ImplementsITheme`、`Light_ImplementsITheme`、`ThemeManager_DefaultCurrent_IsDark` 验证）。
