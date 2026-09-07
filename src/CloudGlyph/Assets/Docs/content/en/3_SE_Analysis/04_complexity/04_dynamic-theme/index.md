# Complexity Analysis — Dynamic Theme

Let $N$ = number of registered theme-aware objects, $P$ = number of themed properties per object, $T$ = number of registered types, $K$ = number of themes, and $C$ = number of registered converters. Theme switching is continuous/Stopwatch-driven: there is no precomputed frame count, and the frame rate is bounded by a coarse `Task.Delay(1)` yield rather than by the effect's `FPS`.

## Core Operations

### Static registration & lookup (`ThemeCache`)

$$O(P) \ \text{per type registration}, \quad O(\text{depth}) \approx O(1) \ \text{per default lookup}$$

- Defaults are stored in a `Dictionary<Type, Dictionary<string, PropertyEntry>>`, where `PropertyEntry` pairs a `PropertyInfo` with a `Dictionary<Type, object?>` of theme values. `RegisterType` copies $P$ entries once per type and is guarded by `IsTypeRegistered` ($O(1)$) — duplicates are ignored.
- `TryGetDefaultValue` walks `type.BaseType` until `object`, doing hash lookups per level: $O(\text{depth})$.
- `GetStaticForType` (called by generated `GetStaticThemeCache`) rebuilds a merged dictionary on every call by walking the inheritance chain and copying entries: $O(P \cdot \text{depth})$ per call.

### Per-instance active cache (`ThemeCache`)

$$O(1) \ \text{amortized per lookup/override}$$

Backed by `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue` (hash-based, amortized $O(1)$). `PrepareSamplers` calls the generated `GetActiveThemeCache()` for every registered object, so on the first switch an empty `InstanceCache` is created for each of the $N$ objects; entries are weak-keyed and collected with their instance.

### Register / Unregister (`ThemeManager`)

$$O(1) \ \text{per call} \quad (O(N) \ \text{worst for RemoveAll})$$

`Register` guards with `_act_cache.TryGetValue`, then appends a `WeakReference<IThemeObject>` to a list — $O(1)$. `Unregister` removes the cache entry and scans the list with `RemoveAll` — $O(N)$ worst, $O(1)$ typical. `InitializeTheme` adds one-time type registration ($O(P)$ amortized) plus applying the current theme to the instance ($O(P)$ reflection writes).

### Switch preparation (`PrepareSamplers`)

$$O(N \cdot P)$$

For each of the $N$ objects and each of its $P$ properties: current/target values are resolved from the active cache then the static dict ($O(1)$ hash lookups), a sampler is resolved via `InterpolatorCore.TryGetInterpolator` ($O(1)$, `ConcurrentDictionary`), and the sampler's `NormalizeStart`/`NormalizeEnd` produce the endpoints ($O(1)$ for value samplers). Rebuilding each object's merged static cache is $O(P \cdot \text{depth})$, giving $O(N \cdot P)$ overall for shallow hierarchies. Temporary memory for the prepared entries is $O(N \cdot P)$.

### Animated switch (`Transition<T>`)

$$O(N \cdot P) \ \text{preparation} \ +\ O(N \cdot P) \ \text{per frame},\quad \text{frames} \approx \frac{\text{Duration}}{\text{yield period}}$$

`ExecuteTransition` awaits a static `SemaphoreSlim` (passes serialize, $O(1)$), then runs a Stopwatch loop. Each frame calls one `ISampler.InsertFrame` (or an end-value write) per property — $O(N \cdot P)$ — and yields with `await Task.Delay(1)`. Because `Task.Delay(1)` resolves at OS-timer granularity (~1-15 ms on Windows), the number of frames is roughly `Duration` divided by that period; no frame list is ever built. A new switch cancels the running pass via `CancellationTokenSource`.

### Instant switch (`Jump<T>`)

$$O(N \cdot P)$$

`Jump` reuses `PrepareSamplers` + `ExecuteTransition` with `durationMs = 0`, so the first frame has `rawT = 1` and every property is written directly to its target value — a single $O(N \cdot P)$ pass.

### Runtime override (`SetThemeValue<T>` / `RestoreThemeValue<T>`)

$$O(1) \ \text{amortized per property}$$

A generated call stores one override entry in the instance's `Overrides` dictionary (or removes it), then refreshes that single property via `UpdatePropertyToCurrentTheme` — dictionary lookups plus at most one inheritance-chain walk in `TryGetDefaultValue` ($O(\text{depth})$).

## Memory Usage

| Structure | Complexity | Notes |
|---|---|---|
| Static theme cache | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`, keyed by declaring type; one value reference per property per theme plus `PropertyInfo` metadata. |
| Active instance overrides | $O(N \cdot P)$ worst | `ConditionalWeakTable<IThemeObject, InstanceCache>` — weak-keyed, no leaks; entries are created lazily on the first switch even when empty. |
| `ThemeManager` membership | $O(N)$ | `_act_cache` (`ConditionalWeakTable`, empty dict per object) + `activeThemes` (`List<WeakReference<IThemeObject>>`); dead entries pruned per pass. |
| Prepared sampler entries | $O(N \cdot P)$ | Transient per switch; freed when `ExecuteTransition` returns. |
| Converter registry | $O(C)$ | `ThemeCache._converters`; currently unpopulated because the generator instantiates converters inline at registration. |

## Lookup Cost of Supporting Structures

| Operation | Complexity |
|---|---|
| Sampler registry lookup (`InterpolatorCore.NativeInterpolators`) | $O(1)$ — `ConcurrentDictionary<Type, ISampler>` |
| Converter lookup by key (`ThemeCache.GetConverter`) | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` start-value read | $O(1)$ — active cache first, then static dictionary |
| `StartModel.Reflect` start-value read | $O(1)$ per property via `PropertyInfo.GetValue` — $O(P)$ per object per switch |

## Notes

- `StartModel` defaults to `Cache`, avoiding per-property reflection at animation start; `Reflect` trades that for reading the live property value.
- The weak-reference design means a registered object that is otherwise unreachable is collected (and pruned at the next switch), so long-running editors do not accumulate theme registrations.
- The animated pass is CPU-light per frame because the sampler writes go through a compiled `TransitionProperty` setter rather than per-frame reflection (`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`, lines 60-68, 124-184).

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (`Transition`, `Jump`, `PrepareSamplers`, `ExecuteTransition`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`, `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.
