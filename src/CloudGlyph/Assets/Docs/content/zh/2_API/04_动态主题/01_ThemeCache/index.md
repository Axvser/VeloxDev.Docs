# API — 动态主题 · ThemeCache

## 命名空间：`VeloxDev.DynamicTheme`

### 类：`ThemeCache`

主题属性值的集中存储。它通过将全部主题数据保存在一个以声明类型为键的位置，消除了按类生成的静态字典。线程安全（由内部锁保护）。

源码：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`。

##### 存储模型

- **静态（默认）按类型配置：** `Type → (propertyName → (PropertyInfo, (themeType → value)))`，存储于 `Dictionary<Type, Dictionary<string, PropertyEntry>>`。
- **活跃（运行时覆盖）按实例缓存：** `ConditionalWeakTable<IThemeObject, InstanceCache>` —— 无强引用，因此覆盖从不泄漏。
- **共享转换器注册表：** `Dictionary<string, IThemeValueConverter>`，带递增的键索引。

##### 方法

#### ThemeCache.IsTypeRegistered

**签名：**
`public static bool IsTypeRegistered(Type type)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `type` | `Type` | 要查找的声明类型。 |

**返回：** `bool` — 若 `type` 在静态缓存中已缓存主题属性则为 `true`。

**说明：**
- 持有内部锁；可安全地从多线程调用。

#### ThemeCache.RegisterType

**签名：**
`public static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `type` | `Type` | 声明类型。 |
| `properties` | `Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)>` | 该类型的主题属性配置。 |

**返回：** `void`

**说明：**
- 线程安全；同一 `type` 的重复注册会被静默忽略。
- 由生成的 `IThemeObject.InitializeTheme()` 实现调用。

#### ThemeCache.RegisterConverter

**签名：**
`public static string RegisterConverter(IThemeValueConverter converter)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `converter` | `IThemeValueConverter` | 要在多个类型间复用的转换器实例。 |

**返回：** `string` — 生成的键（格式 `__velox_global_converter_{n}__`）。

**说明：**
- 该键之后传给 `GetConverter`。

#### ThemeCache.GetConverter

**签名：**
`public static IThemeValueConverter? GetConverter(string key)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `key` | `string` | 由 `RegisterConverter` 返回的转换器键。 |

**返回：** `IThemeValueConverter?` — 转换器，若键未知则为 `null`。

#### ThemeCache.GetStaticForType

**签名：**
`public static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `type` | `Type` | 声明类型。 |

**返回：** `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>>` — 该类型及其基类的全部主题属性的合并字典（沿继承链收集）。

**说明：**
- 派生类同名属性会覆盖基类属性。

#### ThemeCache.GetOrCreateActiveEntry

**签名：**
`public static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `instance` | `IThemeObject` | 支持主题的实例。 |

**返回：** `InstanceCache` — 该实例的运行时覆盖缓存，若不存在则创建。

**说明：**
- 由 `ConditionalWeakTable.GetValue` 支持，因此每个实例只创建一次条目，并随实例一起被回收。

#### ThemeCache.TryGetActiveEntry

**签名：**
`public static InstanceCache? TryGetActiveEntry(IThemeObject instance)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `instance` | `IThemeObject` | 支持主题的实例。 |

**返回：** `InstanceCache?` — 活跃覆盖缓存，若实例未注册则为 `null`。

#### ThemeCache.RemoveActiveEntry

**签名：**
`public static void RemoveActiveEntry(IThemeObject instance)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `instance` | `IThemeObject` | 支持主题的实例。 |

**返回：** `void`

**说明：**
- 移除实例的活跃缓存条目。

#### ThemeCache.TryGetDefaultValue

**签名：**
`public static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)`

| 参数 | 类型 | 描述 |
|---|---|---|
| `type` | `Type` | 声明类型。 |
| `propertyName` | `string` | 属性名。 |
| `themeType` | `Type` | 主题类型。 |
| `value` | `out object?` | 找到时接收默认值。 |

**返回：** `bool` — 若为给定类型/属性/主题找到默认值则为 `true`。

**说明：**
- 当类型自身没有条目时，会沿继承链（`type.BaseType`）查找。

---

## 嵌套类型：`ThemeCache.InstanceCache`

`public sealed class InstanceCache`

| 成员 | 签名 | 描述 |
|---|---|---|
| `Overrides` | `public Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; }` | 运行时覆盖：属性名 → 属性 → 主题 → 值。初始化为空字典。 |

**说明：**
- 只有运行时实际被修改过的属性才会存储在这里；切换主题时，动态内容会覆盖静态内容。
