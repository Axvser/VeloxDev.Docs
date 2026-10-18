# API — Dynamic Theme · ThemeCache

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeCache`

Central store of theme property values. It eliminates per-class generated static dictionaries by storing all theme data in one location, keyed by the declaring type. All members are static; the static store and its registration path are guarded by an internal lock, and the per-instance store is a `ConditionalWeakTable`.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.

#### Storage Model

- **Static (default) per-type configuration:** `Type → (propertyName → PropertyEntry(PropertyInfo, (themeType → value)))`, stored in a `Dictionary<Type, Dictionary<string, PropertyEntry>>`.
- **Active (runtime-override) per-instance cache:** `ConditionalWeakTable<IThemeObject, InstanceCache>` — no strong references, so per-instance overrides never leak.

#### Methods

#### ThemeCache.IsTypeRegistered

**Signature:**
`public static bool IsTypeRegistered(Type type)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type to look up. |

**Returns:** `bool` — `true` if `type` already has theme properties in the static cache.

**Notes:**
- Takes the internal lock; safe to call from multiple threads. Consulted by the generated `InitializeTheme()` before registering a type.

#### ThemeCache.RegisterType

**Signature:**
`public static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type. |
| `properties` | `Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)>` | The type's theme property configuration, keyed by property name. |

**Returns:** `void`

**Notes:**
- Thread-safe; a duplicate registration for the same `type` is silently ignored (first registration wins).
- Called from generated `IThemeObject.InitializeTheme()` implementations; each value dictionary holds one converted value per theme type.

#### ThemeCache.GetStaticForType

**Signature:**
`public static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)`

| Parameter | Type | Description |
|---|---|---|
| `type` | `Type` | The declaring type. |

**Returns:** `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>>` — a newly built merged dictionary of all theme properties for `type` and its base types (walks the inheritance chain, base first, so derived properties of the same name replace base ones).

**Notes:**
- Backs the generated `GetStaticThemeCache()` method and is used at switch time to obtain per-theme default values. A new dictionary is allocated on every call; its value dictionaries are the cached instances.

#### ThemeCache.GetOrCreateActiveEntry

**Signature:**
`public static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `IThemeObject` | The theme-aware instance. |

**Returns:** `InstanceCache` — the per-instance runtime-override cache, creating a new entry if none exists.

**Notes:**
- Backed by `ConditionalWeakTable.GetValue`, so the entry is created once per instance and collected together with it. Backs the generated `GetActiveThemeCache()`.

#### ThemeCache.TryGetActiveEntry

**Signature:**
`public static InstanceCache? TryGetActiveEntry(IThemeObject instance)`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `IThemeObject` | The theme-aware instance. |

**Returns:** `InstanceCache?` — the active override cache, or `null` if the instance has no entry. This is the lookup the generated `RestoreThemeValue<T>` uses.

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
- Walks the inheritance chain (`type.BaseType`) when the type has no own entry. Used by the generated `UpdatePropertyToCurrentTheme()` to re-apply defaults.

---

## Nested Type: `ThemeCache.InstanceCache`

`public sealed class InstanceCache`

| Member | Signature | Description |
|---|---|---|
| `Overrides` | `public Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; }` | Runtime overrides: property name → property → theme → value. Initialized to an empty dictionary. |

**Notes:**
- Only properties actually overridden at runtime are stored here. During a theme switch, dynamic content takes precedence over the static defaults.
- It is the value type of `ThemeCache`'s private `ConditionalWeakTable<IThemeObject, InstanceCache>`. (`ThemeManager` keeps a separate weak table as its own registration guard.)
