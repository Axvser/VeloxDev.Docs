# API — 动态主题 · ThemeConfigAttribute 与契约

## 命名空间：`VeloxDev.DynamicTheme`

### 特性：`ThemeConfigAttribute<TConverter, TTheme1, ...>`

共有六种泛型元数，装饰类以把一个属性映射为每个主题类型下的一个转换值。特性可在一个类上重复（`AllowMultiple = true`），只作用于类，且不继承。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`。

| 主题数量 | 泛型参数 | 约束 |
|---|---|---|
| 2 | `<TConverter, TTheme1, TTheme2>` | `TConverter : class, IThemeValueConverter`；每个 `TThemeN : ITheme` |
| 3 | `<TConverter, TTheme1, TTheme2, TTheme3>` | 同上 |
| 4 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4>` | 同上 |
| 5 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5>` | 同上 |
| 6 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5, TTheme6>` | 同上 |
| 7 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5, TTheme6, TTheme7>` | 同上 |

每种元数声明一个构造函数：

`public ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2, ..., object?[] themeContextN)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `propertyName` | `string` | 目标属性名（如 `nameof(Background)`）。 |
| `themeContextN` | `object?[]` | 第 N 个主题对应的原始值参数，按泛型主题实参的顺序。 |

**示例：**
```csharp
// 来源：Demo（Examples/Theme/WPF/Demo/MainWindow.xaml.cs）
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
```

**说明：**
- `TConverter` 是把原始 `object?[]` 参数列表转换为属性平台类型的策略（如 `BrushConverter` → 一个 `Brush`；Avalonia 示例使用 `ObjectConverter`）。转换器实现随每个平台适配器一起提供，位于同一 `VeloxDev.DynamicTheme` 命名空间（见 [04 PlatformAdapters](../04_平台适配器/index.md)）。
- 特性本身只声明数据 —— 单独应用它不会产生任何行为。由主题源生成器消费以生成 `IThemeObject` 的 partial 实现。

### 源生成器：`Theme`（命名空间 `VeloxDev.Generators`）

`[Generator(LanguageNames.CSharp)] public class Theme : IIncrementalGenerator`

源码：`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。

该生成器响应 **partial 类** 上的 `[ThemeConfig<...>]`（当前支持 2 到 6 个主题类型的元数，即元数据元数 3–7），并为该类生成一段附加的 partial 声明：

- 当基类型尚未实现 `IThemeObject` 时，追加 `: IThemeObject`。
- 生成 `ExecuteThemeChanging(Type? oldValue, Type? newValue)` / `ExecuteThemeChanged(...)`：先调用基类实现（若存在），再调用 **partial 钩子** `partial void OnThemeChanging(Type? oldValue, Type? newValue)` / `partial void OnThemeChanged(...)` —— 只作无主体的声明，供用户在类的另一部分实现。WPF 示例通过实现 `OnThemeChanged` 弹出 `MessageBox`；Avalonia 示例则显示 `WindowNotificationManager` 通知。
- 生成 `InitializeTheme()`：经 `ThemeCache.RegisterType` 登记类型的静态值、调用 `ThemeManager.Register(this)`，并把当前主题的值应用到被装饰属性。两个示例都在 `InitializeComponent()` 之后调用 `InitializeTheme()`。
- 生成 `SetThemeValue<T>` / `RestoreThemeValue<T>`（运行时覆盖）与缓存访问器 `GetStaticThemeCache()` / `GetActiveThemeCache()`，以及 `UpdatePropertyToCurrentTheme` / `UpdateAllPropertiesToCurrentTheme` 辅助方法。

**说明：**
- 只实现 `IThemeObject` 而没有 `[ThemeConfig]` 的类不会被处理。
- 转换器在登记时通过 `Activator.CreateInstance` 内联实例化 —— 生成器不使用 `ThemeCache.RegisterConverter`。

---

### 接口：`ITheme`

`public interface ITheme`

主题类型的空标记接口。由 `Dark`、`Light` 及任何自定义主题类型实现。

源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/ITheme.cs`。

---

### 接口：`IThemeObject`

由源生成器为 partial 类上带有 `[ThemeConfig]` 的类实现。源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeObject.cs`。

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
- `InitializeTheme()` 必须在 `InitializeComponent()`（WPF/Avalonia）之后调用，以注册实例；两个示例都在 `LoadTheme()` 中调用。
- `SetThemeValue<T>` / `RestoreThemeValue<T>` 管理运行时覆盖：WPF 示例调用 `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })` 与 `RestoreThemeValue<Light>(nameof(Foreground))`，随后检查 `GetStaticThemeCache()` 与 `GetActiveThemeCache()`。
- 缓存结构为 `属性名 → PropertyInfo → 主题类型 → 值`。

---

### 接口：`IThemeValueConverter`

`public interface IThemeValueConverter`

将原始主题参数适配为平台值的策略。

源码：`Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeValueConverter.cs`。

| 成员 | 签名 |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**说明：**
- 平台适配器提供实现 —— `BrushConverter`、`ColorConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ThicknessConverter`、`ObjectConverter`（均位于适配器程序集的 `VeloxDev.DynamicTheme` 命名空间）——见 [04 PlatformAdapters](../04_平台适配器/index.md)。
- `ThemeCache` 也暴露一个转换器注册表（`RegisterConverter` / `GetConverter`），用于希望在多个类型间共享单个转换器实例的场景。
