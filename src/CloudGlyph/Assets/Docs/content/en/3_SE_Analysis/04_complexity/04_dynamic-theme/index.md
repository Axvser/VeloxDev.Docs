# Complexity Analysis — Dynamic Theme

Let $N$ = number of registered theme-aware objects, $P$ = number of themed properties per object, $S$ = number of interpolation frames for a transition, $T$ = number of registered types, and $K$ = number of themes.

## Core Operations

### Theme value lookup (`ThemeCache`)

$$O(P) \quad \text{per type (property scan)}, \quad O(1) \quad \text{per property lookup}$$

- Static defaults are stored in a `Dictionary<Type, Dictionary<string, PropertyEntry>>`; `TryGetDefaultValue` walks the inheritance chain (`type.BaseType`), so a lookup is $O(\text{depth}) \approx O(1)$ for shallow hierarchies.
- `GetStaticForType` rebuilds a merged dictionary each call by walking the inheritance chain and copying entries — $O(P \cdot \text{depth})$ worst case per call.

### Per-instance active cache (`GetOrCreateActiveEntry`)

$$O(1) \quad \text{amortized}$$

- Backed by `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue`, which is a hash-based lookup — amortized $O(1)$. The entry is created once per instance and collected with the instance.

### Register / Unregister (`ThemeManager`)

$$O(1) \quad \text{per call}$$

- `Register` does a `ConditionalWeakTable.TryGetValue` (guarding duplicates) then adds one `WeakReference<IThemeObject>` to a list. `Unregister` removes the cache entry and removes the matching weak reference via `RemoveAll` — $O(N)$ worst case for `RemoveAll`, $O(1)$ amortized per typical call.
- `InitializeTheme()` additionally registers the type once in `ThemeCache` ($O(P)$ amortized) and applies the current theme to the instance ($O(P)$).

### Animated switch (`Transition<T>`)

$$O(N \cdot P \cdot S)$$

For each of the $N$ objects, for each of its $P$ properties, `CalculateFrames` produces $S$ frames:

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

- Frame pre-computation per property: $O(S)$ (one interpolate + one eased evaluation per frame).
- Frame application: $S$ sequential `Task.Delay(deltaTime)` steps, each invoking one queued action that applies `PropertyInfo.SetValue` once per property — **wall-clock** $O(S \cdot \Delta t)$, i.e. bounded by `Duration`.
- Temporary memory for the pre-computed frame queue and per-property frame arrays: $O(N \cdot P \cdot S)$.

Example with `TransitionEffects.Theme` ($FPS = 60$, $Duration = 0.46s$):

$$S = \left\lfloor \frac{460 \times 60}{1000} \right\rfloor = 27 \quad \text{frames per property}$$

### Instant switch (`Jump<T>`)

$$O(N \cdot P)$$

No interpolation; `steps = 1`, `deltaTime = 0`. Each property is set directly to its target value.

### Runtime override (`SetThemeValue<T>`)

$$O(P)$$

Writes one override entry into the instance's active cache (`InstanceCache.Overrides`) and updates the property to the current theme.

## Memory Usage

| Structure | Complexity | Notes |
|---|---|---|
| Static theme cache (per registered type) | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`, keyed by declaring type; holds one value per property per theme. |
| Active instance overrides | $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` — weak-keyed, no leaks. |
| `ThemeManager` live-instance list | $O(N)$ | `List<WeakReference<IThemeObject>>`; dead entries pruned on each transition ($O(N)$). |
| Transition frame buffers | $O(N \cdot P \cdot S)$ | Temporary during a transition; freed after `ExecuteTransition` completes. |
| Converter registry | $O(C)$ | `Dictionary<string, IThemeValueConverter>`, $C$ = registered converters. |

## Lookup Cost of Supporting Structures

| Operation | Complexity |
|---|---|
| Interpolator registry lookup (`InterpolatorCore.NativeInterpolators`) | $O(1)$ — `ConcurrentDictionary<Type, IValueInterpolator>` |
| Converter lookup by key (`ThemeCache.GetConverter`) | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` start-value read | $O(1)$ — active cache then static dictionary |
| `StartModel.Reflect` start-value read | $O(1)$ per property via `PropertyInfo.GetValue` — $O(P)$ per object per transition |

## Notes

- `StartModel.Cache` avoids reflection during animation start; `StartModel.Reflect` reads the live property value via `PropertyInfo.GetValue` — negligible per property, but $O(P)$ per object per transition.
- The weak-reference design means a registered object that is otherwise unreachable is collected (and pruned at the next transition), so long-running editors do not accumulate theme registrations.

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (lines 83–106 `Transition`, 121–143 `Jump`, 153–407 `CalculateFrames`, 414–452 `ExecuteTransition`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.
