# 声明与类型

声明主题化属性的特性、生成器实现的接口、两个内置主题、全局缓存以及生成器产出的成员。

## VeloxDev.DynamicTheme

### 类：ThemeConfigAttribute<TConverter, TTheme1, TTheme2 … TTheme7>

为某个属性声明它在二到七个主题中各自的值。共有六个泛型元数（`TTheme1`–`TTheme2` 到 `TTheme1`–`TTheme7`）。

**签名（双主题形式）：**
`public class ThemeConfigAttribute<TConverter, TTheme1, TTheme2> : Attribute where TConverter : class, IThemeValueConverter where TTheme1 : ITheme where TTheme2 : ITheme`

**构造函数：** `ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2)`——按声明顺序每主题一个值数组。

三、四、五、六、七主题形式各多一个 `object?[] themeContextN`。

**特性用法：** `AttributeTargets.Class`，`AllowMultiple = true`，`Inherited = false`。应用于声明（或继承）该属性的分部类。

每个上下文数组作为 `parameters` 参数传给转换器。转换器可以解释一个字符串、多个分量或类型标记；见[平台转换器](../02_平台转换器/index.md)。

### 接口：ITheme

一个主题定义的标记。自定义主题是一个空类。

**签名：** `public interface ITheme`

### 接口：IThemeObject

生成器在主题化类上实现的契约。

**签名：** `public interface IThemeObject`

| 成员 | 签名 | 说明 |
|---|---|---|
| `InitializeTheme` | `void InitializeTheme()` | 注册类型配置并应用当前主题的值。存在 `InitializeComponent()` 时必须在它之后运行。 |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` | 切换开始时运行正在变化钩子。 |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` | 切换落地后运行已变化钩子。 |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` | 为一个属性、一个主题写入实例级覆盖。 |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` | 移除覆盖并重新应用声明值。 |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` | 逐属性、逐主题的声明值。 |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` | 实例级覆盖。 |

### 接口：IThemeValueConverter

**签名：** `public interface IThemeValueConverter`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` | 为属性转换一个存储值；`null` 表示无法转换，该属性被跳过。 |

### 类：Light / Dark

两个内置主题，均实现 `ITheme`。

**签名：** `public class Light : ITheme`、`public class Dark : ITheme`

`ThemeManager.Current` 默认为 `typeof(Dark)`。

### 类：ThemeCache

进程级存储：静态的逐类型声明值表与弱的逐实例覆盖表。

**签名：** `public static class ThemeCache`

| 成员 | 签名 | 说明 |
|---|---|---|
| `InstanceCache` | `public sealed class InstanceCache` | 含 `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; }`。 |
| `IsTypeRegistered` | `static bool IsTypeRegistered(Type type)` | 类型的声明配置是否已注册。 |
| `RegisterType` | `static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)` | 注册声明值；重复注册被忽略。线程安全。 |
| `GetStaticForType` | `static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)` | 合并的声明值，从基类向上遍历，派生条目覆盖基类。 |
| `GetOrCreateActiveEntry` | `static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)` | 实例覆盖项，首次使用时创建。 |
| `TryGetActiveEntry` | `static InstanceCache? TryGetActiveEntry(IThemeObject instance)` | 覆盖项，或 `null`。 |
| `TryGetDefaultValue` | `static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)` | 查找声明值，沿基类型上溯。 |

实例表是 `ConditionalWeakTable`，缓存永不让主题对象保持存活。

## 生成的成员

对一个带一个或多个 `[ThemeConfig<…>]` 的分部类，生成器产出（文件 `{Class}_{Namespace}_ThemeConfig.g.cs`）：

| 成员 | 签名 | 说明 |
|---|---|---|
| `InitializeTheme` | `(virtual/override) void InitializeTheme()` | 注册类型一次，向 `ThemeManager` 注册实例，应用当前主题。基类已实现 `IThemeObject` 且带 `[ThemeConfig]` 时为 `override`。 |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` | 有基类实现时先调基类，再调 `OnThemeChanging`。 |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` | 有基类实现时先调基类，再调 `OnThemeChanged`。 |
| `OnThemeChanging` | `partial void OnThemeChanging(Type? oldValue, Type? newValue)` | 实现可选。 |
| `OnThemeChanged` | `partial void OnThemeChanged(Type? oldValue, Type? newValue)` | 实现可选。 |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` | 写入覆盖；若 `T` 是当前主题则重新应用该属性。 |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` | 移除覆盖并重新应用该属性。 |
| `GetStaticThemeCache` | `Dictionary<…> GetStaticThemeCache()` | 返回 `ThemeCache.GetStaticForType(GetType())`。 |
| `GetActiveThemeCache` | `Dictionary<…> GetActiveThemeCache()` | 返回实例覆盖表。 |
| `UpdatePropertyToCurrentTheme` | `void UpdatePropertyToCurrentTheme(string propertyName)` | 从覆盖或声明值重新应用一个属性。 |
| `UpdateAllPropertiesToCurrentTheme` | `void UpdateAllPropertiesToCurrentTheme()` | 重新应用所有声明属性。 |

没有基类实现时，生成的类还会实现 `IThemeObject`。

## 示例

```csharp
using System;
using System.Windows;
using VeloxDev.DynamicTheme;

[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class ThemedWindow : Window
{
    public ThemedWindow() => InitializeTheme();

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
        => Console.WriteLine($"{oldValue?.Name} -> {newValue?.Name}");
}
```

`BrushConverter` 是 WPF 适配器的转换器；见[平台转换器](../02_平台转换器/index.md)。完整可运行窗口见[快速开始](../../../1_快速开始/13_运行时主题/index.md)。
