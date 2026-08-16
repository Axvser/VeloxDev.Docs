# API — Dynamic Theme · ThemeCache

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeCache`

Central store of theme property values. It eliminates per-class generated static dictionaries by storing all theme data in one location, keyed by the declaring type. Thread-safe (guarded by an internal lock).

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.

##### Storage Model

- **Static (default) per-type configuration:** `Type → (propertyName → (PropertyInfo, (themeType → value)))`, stored in a `Dictionary<Type, Dictionary<string, PropertyEntry>>`.
- **Active (runtime-override) per-instance cache:** `ConditionalWeakTable<IThemeObject, InstanceCache>` — no strong references, so overrides never leak.
- **Shared converter registry:** `Dictionary<string, IThemeValueConverter>` with an incrementing key index.

##### Methods

#### ThemeCache.IsTypeRegistered

**Signature:**
`public static bool IsTypeRegistered(Type type)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type to look up. |

**Returns:** `bool` — `true` if `type` has cached theme properties in the static cache.

**Notes:**
- Takes the internal lock; safe to call from multiple threads.

#### ThemeCache.RegisterType

**Signature:**
`public static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type. |
| `properties` | `Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)>` | The type's theme property configuration. |

**Returns:** `void`

**Notes:**
- Thread-safe; duplicate registration of the same `type` is silently ignored.
- Called from generated `IThemeObject.InitializeTheme()` implementations.

#### ThemeCache.RegisterConverter

**Signature:**
`public static string RegisterConverter(IThemeValueConverter converter)`

| Parameter | Type | Description |
|---|---|---|
| `converter` | `IThemeValueConverter` | A converter instance to reuse across types. |

**Returns:** `string` — the generated key (format `__velox_global_converter_{n}__`).

**Notes:**
- The key is later passed to `GetConverter`.

#### ThemeCache.GetConverter

**Signature:**
`public static IThemeValueConverter? GetConverter(string key)`

| Parameter | Type | Description |
|---|---|---|
| `key` | `string` | The converter key returned by `RegisterConverter`. |

**Returns:** `IThemeValueConverter?` — the converter, or `null` if the key is unknown.

#### ThemeCache.GetStaticForType

**Signature:**
`public static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type. |

**Returns:** `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>>` — a merged dictionary of all theme properties for `type` and its base types (walking the inheritance chain).

**Notes:**
- Derived properties override base ones of the same name.

#### ThemeCache.GetOrCreateActiveEntry

**Signature:**
`public static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `IThemeObject` | The theme-aware instance. |

**Returns:** `InstanceCache` — the per-instance runtime override cache, creating a new entry if none exists.

**Notes:**
- Backed by `ConditionalWeakTable.GetValue`, so the entry is created once per instance and collected with the instance.

#### ThemeCache.TryGetActiveEntry

**Signature:**
`public static InstanceCache? TryGetActiveEntry(IThemeObject instance)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `IThemeObject` | The theme-aware instance. |

**Returns:** `InstanceCache?` — the active override cache, or `null` if the instance is not registered.

#### ThemeCache.RemoveActiveEntry

**Signature:**
`public static void RemoveActiveEntry(IThemeObject instance)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `IThemeObject` | The theme-aware instance. |

**Returns:** `void`

**Notes:**
- Removes the instance's active cache entry.

#### ThemeCache.TryGetDefaultValue

**Signature:**
`public static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type. |
| `propertyName` | `string` | The property name. |
| `themeType` | `Type` | The theme type. |
| `value` | `out object?` | Receives the default value when found. |

**Returns:** `bool` — `true` if a default value was found for the given type/property/theme.

**Notes:**
- Walks the inheritance chain (`type.BaseType`) when the type has no own entry.

---

## Nested Type: `ThemeCache.InstanceCache`

`public sealed class InstanceCache`

| Member | Signature | Description |
|---|---|---|
| `Overrides` | `public Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; }` | Runtime overrides: property name → property → theme → value. Initialized to an empty dictionary. |

**Notes:**
- Only properties that were actually modified at runtime are stored here; during a theme switch dynamic content overrides static content.
