# API — 动态主题 · ThemeConfigAttribute 与契约

## 命名空间：`VeloxDev.DynamicTheme`

### 特性：`ThemeConfigAttribute<TConverter, TTheme1, ...>`

共有六种泛型元数，装饰类以将一个属性映射为每个主题下的一个值。源生成器 `VeloxDev.Generators.Theme` 读取这些特性，并在装饰类上生成 `IThemeObject` 实现。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`。

| 元数 | 泛型参数 | 约束 |
|---|---|---|
| 2 个主题 | `<TConverter, TTheme1, TTheme2>` | `TConverter : class, IThemeValueConverter`；`TTheme1, TTheme2 : ITheme` |
| 3 个主题 | `<TConverter, TTheme1, TTheme2, TTheme3>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |
| 4 个主题 | `<TConverter, TTheme1..TTheme4>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |
| 5 个主题 | `<TConverter, TTheme1..TTheme5>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |
| 6 个主题 | `<TConverter, TTheme1..TTheme6>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |
| 7 个主题 | `<TConverter, TTheme1..TTheme7>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |

**构造函数**（每种元数一个）：

`public ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2, ..., object?[] themeContextN)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `propertyName` | `string` | 目标属性名（如 `nameof(Background)`）。 |
| `themeContextN` | `object?[]` | 第 N 个主题对应的值参数，按泛型主题参数的顺序。 |

**特性元数据：** `[AttributeUsage(AttributeTargets.Class, AllowMultiple = true, Inherited = false)]`。

**示例：**
```text
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
```

**说明：**
- `TConverter` 是策略，负责把原始 `object?[]` 参数转换为属性的平台类型（如 `BrushConverter` → `Brush`）。
- 每个特性最少两个主题，最多支持七个主题。

---

### 接口：`ITheme`

`public interface ITheme`

主题类型的空标记接口。由 `Dark`、`Light` 及任何自定义主题类型实现。

源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/ITheme.cs`。

---

### 接口：`IThemeObject`

由源生成器为任何带有 `[ThemeConfig]` 的类实现。生成器还会产生 `partial void OnThemeChanging(Type? oldValue, Type? newValue)` / `partial void OnThemeChanged(Type? oldValue, Type? newValue)` 钩子。

源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeObject.cs`。

| 成员 | 签名 |
|---|---|
| `InitializeTheme` | `void InitializeTheme()` |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` |

**说明：**
- `InitializeTheme()` 必须在 `InitializeComponent()`（WPF/Avalonia）之后调用，以注册实例。
- `SetThemeValue<T>` / `RestoreThemeValue<T>` 是运行时值覆盖；WPF 示例中出现 `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })`。
- 缓存结构为 `属性名 → PropertyInfo → 主题类型 → 值`。

---

### 接口：`IThemeValueConverter`

`public interface IThemeValueConverter`

将原始主题参数适配为平台类型的策略。

源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeValueConverter.cs`。

| 成员 | 签名 |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**说明：**
- 平台适配器提供实现：`BrushConverter`、`ColorConverter`、`ThicknessConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ObjectConverter`（均在命名空间 `VeloxDev.DynamicTheme` 中）。
- `ThemeCache` 的转换器注册表允许转换器只注册一次并在多个类型间复用（`RegisterConverter` / `GetConverter`）。
