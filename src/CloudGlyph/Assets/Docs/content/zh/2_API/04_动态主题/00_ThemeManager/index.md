# API — 动态主题 · ThemeManager

## 命名空间：`VeloxDev.DynamicTheme`

### 类：`ThemeManager`

主题状态与切换的静态入口。所有成员均为静态。活跃实例通过 `ConditionalWeakTable<IThemeObject, ...>` 加上 `List<WeakReference<IThemeObject>>` 跟踪，因此注册不会产生泄漏。管理器自己不负责计时：带动画的切换由平台的 `TransitionSchedulerCore` 运行，它按目标经 `InterpolatorCore.CreateScheduler` 解析，而一场切换的所有目标都锚定在同一个 `TransitionTimeline` 上。每次切换前后仍会对每个已注册对象触发生命周期回调。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`。

##### 属性

| 名称 | 类型 | 描述 |
|---|---|---|
| `Current` | `Type` | 当前主题类型。默认：`typeof(Dark)`。setter 为 `internal`；外部调用方通过 `Transition`/`Jump`/`SetCurrent` 切换。 |
| `StartModel` | `StartModel` | 带动画的切换中，动画起始值的获取方式。默认：`StartModel.Cache`。 |

#### ThemeManager.SetPlatformInterpolator

**签名：**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| 参数 | 类型 | 描述 |
|---|---|---|
| `interpolator` | `T` | 平台插值器实例（如适配器的 `new Interpolator()`）。 |

**返回：** `void`

**示例：**
```csharp
// 来源：Demo（Examples/Theme/WPF/Demo/App.xaml.cs）
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

**说明：**
- 在任何带动画的过渡之前必须调用一次，以便主题属性类型能解析到平台采样器。`InterpolatorCore` 声明于 `VeloxDev.TransitionSystem.Abstractions`；具体适配器类型是位于 `VeloxDev.TransitionSystem` 的平台 `Interpolator`（见 [04 PlatformAdapters](../04_PlatformAdapters/index.md)）。
- 除了强制适配器执行采样器注册，它还是不带动画就无法成立的那一环：`Transition` 通过 `InterpolatorCore.CreateScheduler` 向该实例索取调度器（`ThemeManager.cs`，`RunSwitch`）。未设置时切换依然发生——只是瞬时完成、没有动画。
- 若某属性类型没有已注册的采样器，带动画的切换仍会运行，但该属性全程保持旧值，直到切换结束时才被写入目标值（`ThemeManager.cs`，`ApplyHeldValues`）。

#### ThemeManager.SetCurrent

**签名：**
`public static void SetCurrent<T>() where T : ITheme`

**返回：** `void`

**示例：**
```csharp
// 来源：Test（ThemeBasicsTests.ThemeManager_SetCurrent_Changes）
ThemeManager.SetCurrent<Light>();
```

**说明：**
- 将 `Current` 设为 `typeof(T)`，不触发任何主题变更回调，也不应用任何值。可见的切换请优先使用 `Transition<T>` / `Jump<T>`。

#### ThemeManager.Register

**签名：**
`public static void Register(IThemeObject target)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `target` | `IThemeObject` | 支持主题的对象。 |

**返回：** `void`

**说明：**
- 将目标加入活跃缓存与 `WeakReference` 列表。对已注册的目标再次调用 `Register` 是无操作（由 `ConditionalWeakTable` 查找保证）。
- 通常由生成的 `InitializeTheme()` 自动调用；见 [02 ThemeConfigAttribute](../02_ThemeConfigAttribute/index.md)。

#### ThemeManager.Unregister

**签名：**
`public static void Unregister(IThemeObject target)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `target` | `IThemeObject` | 支持主题的对象。 |

**返回：** `void`

**说明：**
- 移除目标的活跃缓存条目，并从跟踪列表中移除其 `WeakReference`。

#### ThemeManager.Transition<T>

**签名：**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`

| 参数 | 类型 | 描述 |
|---|---|---|
| `effect` | `ITransitionEffectCore` | 过渡效果（缓动与时长）。 |

**返回：** `void`（委托给 `Type` 重载，后者为 `async void`）

**示例：**
```csharp
// 来源：Demo（Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs，ReverseThemeWithAnimation）
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**说明：**
- 委托给 `Transition(typeof(T), effect)`。

#### ThemeManager.Transition(Type, ITransitionEffectCore)

**签名：**
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `themeType` | `Type` | 目标主题类型。 |
| `effect` | `ITransitionEffectCore` | 驱动这场切换的过渡效果。它必须是平台自己的效果类型，`InterpolatorCore.CreateScheduler` 才会接受它。 |

**返回：** `void`（异步——方法本身是 `async void`）

**异常：** 未声明 —— 无效的 `themeType`（`themeType == Current`，或不可赋值为 `ITheme`）会被忽略，并输出 `Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")`。切换内部抛出的异常由 `Transition` 自己捕获并输出 `Debug.WriteLine("[ThemeManager] Error during theme transition: ...")`；`async void` 的调用方接不到它。

**说明：**
- 先取消在飞的切换（`CancelActiveSwitch`），清理失效的 `WeakReference`，然后对每个已注册对象调用 `ExecuteThemeChanging(oldValue, newValue)`。
- 等待私有的 `async Task<bool> RunSwitch`：它用 `PrepareSamplers` 构建每个目标的条目，经 `InterpolatorCore.CreateScheduler` 解析每个目标的调度器，并让它们全部跑在同一个共享的 `TransitionTimeline` 上。当切换被取消或被后续切换顶替时 `RunSwitch` 返回 `false`，此时 `Transition` 不宣布任何变更，也不改动 `Current`。
- 未设置平台插值器、没有任何目标含有可动画属性，或平台调度器拒绝该效果时，退化为瞬时切换（`ApplyImmediately`），而不是启动一场画不出东西的动画。
- `RunSwitch` 之所以是私有的 `async Task<bool>`，正是因为 `Transition` 是 `async void`：适配器的采样器与调度器抛出的异常会在它内部被捕获（`Debug.WriteLine("[ThemeManager] Error during transition execution: ...")`），而不是逃逸到进程里。
- 完成后设置 `Current = themeType`，并对每个已注册对象调用 `ExecuteThemeChanged(oldValue, newValue)`。

#### ThemeManager.Jump<T>

**签名：**
`public static void Jump<T>() where T : ITheme`

**返回：** `void`

**示例：**
```csharp
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
ThemeManager.Jump<Dark>();
```

**说明：**
- 委托给 `Jump(typeof(T))`。无动画立即切换，并取消在飞的动画切换。

#### ThemeManager.Jump(Type)

**签名：**
`public static void Jump(Type themeType)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `themeType` | `Type` | 目标主题类型。 |

**返回：** `void`（同步）

**异常：** 未声明 —— 无效的 `themeType` 会像 `Transition` 一样被忽略并输出调试信息。

**说明：**
- 应用之前先取消在飞的切换（`CancelActiveSwitch`），因此跳跃是顶替正在运行的 `Transition`，而不是与它竞速。
- 通过 `ApplyImmediately` 直接写终值：没有时间轴、没有效果、没有采样。因此它既不依赖 `SetPlatformInterpolator`，也不受平台 `ITransitionEffect<TPriority>` 类型的约束。
- 切换前触发 `ExecuteThemeChanging`，切换后触发 `ExecuteThemeChanged`，并更新 `Current`。

---

## 枚举：`StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

声明于 `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`。

| 值 | 描述 |
|---|---|
| `Reflect` | 通过反射（`PropertyInfo.GetValue`）读取对象当前属性值作为动画起始值。 |
| `Cache` | 使用当前主题的缓存值作为动画起始值（优先动态缓存，其次静态默认值）。 |

**说明：**
- 默认是 `StartModel.Cache`（由 `ThemeBasicsTests.StartModel_DefaultIsCache` 验证）。
- 两个示例都在任何切换之前显式设置 `ThemeManager.StartModel = StartModel.Cache;`。
- 它标记为 `[Flags]` —— `StartModel.Reflect | StartModel.Cache` 是合法的组合值（由 `ThemeBasicsTests.StartModel_FlagsEnum` 验证）。

---

## 类：`Dark` / `Light`

`public class Dark : ITheme` — 实现 `ITheme` 的空标记类型。
`public class Light : ITheme` — 实现 `ITheme` 的空标记类型。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/Dark.cs`、`Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`。

**说明：**
- `ThemeManager.Current` 默认是 `typeof(Dark)`；两者都实现 `ITheme`（由 `ThemeBasicsTests.Dark_ImplementsITheme`、`Light_ImplementsITheme`、`ThemeManager_DefaultCurrent_IsDark` 验证）。
- 两个示例只把它们作为泛型实参使用（`Transition<Light>`、`ThemeConfig<..., Light, Dark>`）；两个示例都不派生它们。
