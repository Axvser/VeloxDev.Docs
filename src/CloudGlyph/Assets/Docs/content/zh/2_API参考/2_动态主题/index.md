# 动态主题 — API 参考

## 命名空间：`VeloxDev.DynamicTheme`

### 类：`ThemeManager`

主题状态与切换的静态入口。所有成员均为静态。

##### 属性

| 名称 | 类型 | 描述 |
|---|---|---|
| `Current` | `Type` | 当前主题类型。默认：`typeof(Dark)`。 |
| `StartModel` | `StartModel` | 带动画的切换中，动画起始值的获取方式。默认：`StartModel.Cache`。 |

##### 方法

#### ThemeManager.SetPlatformInterpolator

**签名：**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| 参数 | 类型 | 描述 |
|---|---|---|
| `interpolator` | `T` | 平台插值器实例（如适配器的 `new Interpolator()`）。 |

**返回：** `void`

**说明：**
- 带动画的主题过渡必需，注册一次即可。

#### ThemeManager.SetCurrent

**签名：**
`public static void SetCurrent<T>() where T : ITheme`

**返回：** `void`

**说明：**
- 将 `Current` 设为 `typeof(T)`。主要在内部使用；外部请优先使用 `Transition<T>` / `Jump<T>`。

#### ThemeManager.Register / Unregister

**签名：**
`public static void Register(IThemeObject target)`
`public static void Unregister(IThemeObject target)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `target` | `IThemeObject` | 支持主题的对象（通常由 `InitializeTheme()` 自动注册）。 |

**返回：** `void`

**说明：**
- 活跃实例通过 `ConditionalWeakTable` + `WeakReference` 跟踪，不会产生泄漏。

#### ThemeManager.Transition

**签名：**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `themeType` / `T` | `Type` / `ITheme` | 目标主题。 |
| `effect` | `ITransitionEffectCore` | 过渡效果（FPS、时长、缓动）。 |

**返回：** `void`（异步）

**异常：** 无 — 无效的主题类型会被忽略并输出调试信息。

**示例：**
```text
// 来源：Demo
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**说明：**
- 对所有已注册对象的主题属性逐帧插值，完成后触发 `ExecuteThemeChanged`。

#### ThemeManager.Jump

**签名：**
`public static void Jump<T>() where T : ITheme`
`public static async void Jump(Type themeType)`

**返回：** `void`

**示例：**
```text
// 来源：Demo
ThemeManager.Jump<Dark>();
```

**说明：**
- 无动画立即切换。

---

### 枚举：`StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

| 值 | 描述 |
|---|---|
| `Reflect` | 通过反射读取对象当前属性值作为动画起始状态。 |
| `Cache` | 使用当前主题的缓存值作为动画起始状态。 |

---

### 类：`Dark` / `Light`

`public class Dark : ITheme` — 实现 `ITheme` 的空标记类型。

---

### 类：`ThemeCache`

主题属性值的集中存储。

##### 方法

| 成员 | 签名 | 描述 |
|---|---|---|
| `IsTypeRegistered` | `public static bool IsTypeRegistered(Type type)` | 该类型是否已缓存主题属性。 |
| `RegisterType` | `public static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)` | 注册某类型的主题属性。 |
| `RegisterConverter` | `public static string RegisterConverter(IThemeValueConverter converter)` | 注册转换器并返回其键。 |
| `GetConverter` | `public static IThemeValueConverter? GetConverter(string key)` | 按键查找转换器。 |
| `GetStaticForType` | `public static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)` | 某类型的静态默认值。 |
| `GetOrCreateActiveEntry` | `public static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)` | 某实例的活跃（运行时）覆盖值。 |
| `TryGetActiveEntry` | `public static InstanceCache? TryGetActiveEntry(IThemeObject instance)` | |
| `RemoveActiveEntry` | `public static void RemoveActiveEntry(IThemeObject instance)` | |
| `TryGetDefaultValue` | `public static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)` | |

##### 嵌套类型

`public sealed class InstanceCache { public Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; } = []; }`

---

### 特性：`ThemeConfigAttribute<TConverter, TTheme1, ...>`

共有六种泛型元数：`<TConverter, TTheme1..TTheme2>` 至 `<TConverter, TTheme1..TTheme7>`，其中 `TConverter : class, IThemeValueConverter`，每个 `TThemeN : ITheme`。

**构造函数：**
`(string propertyName, object?[] themeContext1, object?[] themeContext2, ... , object?[] themeContextN)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `propertyName` | `string` | 目标属性名（如 `nameof(Background)`）。 |
| `themeContextN` | `object?[]` | 第 N 个主题对应的值参数。 |

**特性标记：** `AttributeTargets.Class`、`AllowMultiple = true`、`Inherited = false`。

**示例：**
```text
// 来源：Demo
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
```

---

### 接口：`ITheme`

`public interface ITheme` — 主题类型的空标记接口。

---

### 接口：`IThemeObject`

由源生成器为任何带有 `[ThemeConfig]` 的类实现。

| 成员 | 签名 |
|---|---|
| `InitializeTheme` | `void InitializeTheme()` |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` |

---

### 接口：`IThemeValueConverter`

| 成员 | 签名 |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**说明：**
- 平台适配器提供实现：`BrushConverter`、`ColorConverter`、`ThicknessConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ObjectConverter`。

---

## 命名空间：`VeloxDev.TransitionSystem`（支撑引擎，被主题使用）

### 抽象类：`InterpolatorCore`

`public abstract class InterpolatorCore : IFrameInterpolatorCore`

##### 静态成员

| 成员 | 签名 | 描述 |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` | 按类型注册的插值器表。 |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` | |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` | |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` | |

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; }` |
| `Duration` | `TimeSpan Duration { get; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; }` |
| `LoopTime` | `int LoopTime { get; }` |
| `Ease` | `IEaseCalculator Ease { get; }` |
| 事件 | `Awaked / Start / Update / LateUpdate / Canceled / Completed / Finally` — `EventHandler<TransitionEventArgs>` |
| `Clone` | `ITransitionEffectCore Clone()` |

### 接口：`IEaseCalculator`

`public interface IEaseCalculator { double Ease(double t); }`

### 静态类：`Eases`

提供 `Default`，以及 `Sine`、`Quad`、`Cubic`、`Quart`、`Quint`、`Expo`、`Circ`、`Back`、`Elastic`、`Bounce` — 每个都带有 `In` / `Out` / `InOut` 成员，返回 `IEaseCalculator`。

---

## 命名空间：平台适配器（`VeloxDev.WPF` / `VeloxDev.Avalonia`）

### 类：`Interpolator`

`public class Interpolator : InterpolatorCore<InterpolatorOutput, DispatcherPriority>`

- WPF 静态构造函数注册 `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D` 的插值器。
- Avalonia 注册 `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength`。

### 类：`TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>` — `Priority = DispatcherPriority.Render`。

### 静态类：`TransitionEffects`

| 成员 | 值 |
|---|---|
| `Empty` | `Duration = TimeSpan.Zero` |
| `Theme` | `Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `Duration = TimeSpan.FromSeconds(0.32)` |

### 值转换器

`DoubleConverter`、`PointConverter`、`ThicknessConverter`、`CornerRadiusConverter`、`ColorConverter`、`BrushConverter`、`ObjectConverter` — 全部实现 `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`。
