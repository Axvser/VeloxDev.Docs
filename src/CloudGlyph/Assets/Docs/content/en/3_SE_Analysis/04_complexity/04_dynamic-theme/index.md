# Complexity Analysis — Dynamic Theme

Let $N$ = number of registered theme-aware objects, $P$ = number of themed properties per object, $T$ = number of registered types, and $K$ = number of themes. (Sampling is continuous/Stopwatch-driven, so there is no pre-computed frame count $S$.)

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

$$O(N \cdot P) \text{ preparation} \quad + \quad O(N \cdot P) \text{ per sample}$$

For each of the $N$ objects, for each of its $P$ properties, `PrepareSamplers` resolves an `ISampleable` (`InterpolatorCore.TryGetInterpolator` → self-`ISampleable` → null), calls `Normalize`, and captures current/target values — $O(1)$ per property, **no frame list is built**. `ExecuteTransition` then runs a Stopwatch-driven sampling loop:

- Per-sample work: $O(N \cdot P)$ — one `ISampler.Update` (or a held current value) per property.
- The sample count is **not** `FPS`-derived: it is `elapsed / duration`, throttled by a coarse yield interval capped at `1000 / FPS` ms (a yield, not a timing source), so a pass issues at most ~`FPS` samples per second — **wall-clock** bounded by `Duration`. `FPS` is the maximum sample-rate cap.
- Temporary memory for the prepared entries: $O(N \cdot P)$ (each holds target / property / sampler / current / targetValue).

### Instant switch (`Jump<T>`)

$$O(N \cdot P)$$

No sampling beyond the endpoint; `ExecuteTransition` runs with `durationMs = 0`, so the first sample has `rawT = 1` and each property is written directly to its target value.

### Runtime override (`SetThemeValue<T>`)

$$O(P)$$

Writes one override entry into the instance's active cache (`InstanceCache.Overrides`) and updates the property to the current theme.

## Memory Usage

| Structure | Complexity | Notes |
|---|---|---|
| Static theme cache (per registered type) | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`, keyed by declaring type; holds one value per property per theme. |
| Active instance overrides | $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` — weak-keyed, no leaks. |
| `ThemeManager` live-instance list | $O(N)$ | `List<WeakReference<IThemeObject>>`; dead entries pruned on each transition ($O(N)$). |
| Prepared sampler entries | $O(N \cdot P)$ | Temporary during a transition; freed after `ExecuteTransition` completes. |
| Converter registry | $O(C)$ | `Dictionary<string, IThemeValueConverter>`, $C$ = registered converters. |

## Lookup Cost of Supporting Structures

| Operation | Complexity |
|---|---|
| Interpolator registry lookup (`InterpolatorCore.NativeInterpolators`) | $O(1)$ — `ConcurrentDictionary<Type, ISampleable>` |
| Converter lookup by key (`ThemeCache.GetConverter`) | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` start-value read | $O(1)$ — active cache then static dictionary |
| `StartModel.Reflect` start-value read | $O(1)$ per property via `PropertyInfo.GetValue` — $O(P)$ per object per transition |

## Notes

- `StartModel.Cache` avoids reflection during animation start; `StartModel.Reflect` reads the live property value via `PropertyInfo.GetValue` — negligible per property, but $O(P)$ per object per transition.
- The weak-reference design means a registered object that is otherwise unreachable is collected (and pruned at the next transition), so long-running editors do not accumulate theme registrations.

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (`Transition`, `Jump`, `PrepareSamplers`, `ExecuteTransition`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.
