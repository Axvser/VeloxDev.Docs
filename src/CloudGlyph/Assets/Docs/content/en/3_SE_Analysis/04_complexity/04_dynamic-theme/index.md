# Complexity Analysis — Dynamic Theme

Let $N$ = number of registered theme-aware objects, $P$ = number of themed properties per object, $T$ = number of registered types, $K$ = number of themes, and $C$ = number of registered converters. An animated switch is now executed by the platform's `TransitionSchedulerCore`, so its frame count and frame pace belong to the Effect (`FPS`) and its wall time is bounded by the effect's `Duration`, not by the element count: every target of one switch is anchored to a single `TransitionTimeline`.

## Core Operations

### Static registration & lookup (`ThemeCache`)

$$
O(P) \ \text{per type registration}, \quad O(\text{depth}) \approx O(1) \ \text{per default lookup}
$$

- Defaults are stored in a `Dictionary<Type, Dictionary<string, PropertyEntry>>`, where `PropertyEntry` pairs a `PropertyInfo` with a `Dictionary<Type, object?>` of theme values. `RegisterType` copies $P$ entries once per type and is guarded by `IsTypeRegistered` ($O(1)$) — duplicates are ignored.
- `TryGetDefaultValue` walks `type.BaseType` until `object`, doing hash lookups per level: $O(\text{depth})$.
- `GetStaticForType` (called by generated `GetStaticThemeCache`) rebuilds a merged dictionary on every call by walking the inheritance chain and copying entries: $O(P \cdot \text{depth})$ per call.

### Per-instance active cache (`ThemeCache`)

$$
O(1) \ \text{amortized per lookup/override}
$$

Backed by `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue` (hash-based, amortized $O(1)$). `PrepareSamplers` calls the generated `GetActiveThemeCache()` for every registered object, so on the first switch an empty `InstanceCache` is created for each of the $N$ objects; entries are weak-keyed and collected with their instance.

### Register / Unregister (`ThemeManager`)

$$
O(1) \ \text{per call} \quad (O(N) \ \text{worst for RemoveAll})
$$

`Register` guards with `_act_cache.TryGetValue`, then appends a `WeakReference<IThemeObject>` to a list — $O(1)$. `Unregister` removes the cache entry and scans the list with `RemoveAll` — $O(N)$ worst, $O(1)$ typical. `InitializeTheme` adds one-time type registration ($O(P)$ amortized) plus applying the current theme to the instance ($O(P)$ reflection writes).

### Switch preparation (`PrepareSamplers`)

$$
O(N \cdot P \cdot \text{depth}) \ \text{worst}, \quad O(N \cdot P) \ \text{for shallow hierarchies}
$$

For each of the $N$ objects and each of its $P$ properties: current/target values are resolved from the active cache then the static dict ($O(1)$ hash lookups each), and the property's `PropertyInfo` is wrapped in a `TransitionProperty` path. Rebuilding each object's merged static cache is $O(P \cdot \text{depth})$. No sampler is resolved and no endpoint is normalized here — the only registry touch is one `InterpolatorCore.TryGetInterpolator(propertyType, out _)` probe per property. That probe is exact-match first ($O(1)$) and otherwise walks the base-type chain from the type upward and then the interfaces ordered by name, so it is $O(\text{depth} + \text{interfaces})$ on a miss.

`TransitionProperty.FromProperty` is memoized in a static `ConcurrentDictionary<PropertyInfo, TransitionProperty>`, so the path construction — and the expression compilation it triggers on first use — is paid once per distinct `PropertyInfo`, not once per switch: $O(1)$ amortized afterwards. Temporary memory for the groups and entries is $O(N \cdot P)$.

### Scheduler resolution

$$
O(N)
$$

One `InterpolatorCore.CreateScheduler(target, effect)` call per target group, taken **before** anything is scheduled, so the answer is the same for the whole switch. The first failure — no platform interpolator, an empty group list, or one `null` scheduler — short-circuits the entire switch to an immediate apply, which is why the animated path never runs for a subset of the targets.

### Animated switch (`Transition<T>`)

$$
O(N \cdot P) \ \text{preparation} \ + \ O\!\left(\frac{\text{Duration}}{\text{FPS}^{-1}}\right) \ \text{frames} \ \times \ O(P) \ \text{per target per frame}
$$

The synchronous part of the call is the preparation: if it animates, `Transition<T>`'s first await is the `Task.WhenAll` over the per-target execution tasks, so everything before it — pruning, batching, `PrepareSamplers`, `WriteStartValues`, `Track`, `StateCore` construction, scheduling — happens inline. Then each target's scheduler runs its own sampling loop against the **shared** timeline, paced by the effect's `FPS` and eased by `effect.Ease`. Per frame per target, one `ISampler.InsertFrame` runs per sampled property; properties with no sampler are skipped by the loop entirely and written once at the end.

Because the timeline is shared, the number of frames a target sees is the same for one target and for a thousand, and the switch's wall time is the effect's own duration regardless of $N$ — the property the scale demo's `bench` mode measures (`Examples/Theme/WPF/Demo/BenchRunner.cs`).

Superseding a switch is $O(1)$ plus the cancellation callbacks: `CancelActiveSwitch` exchanges the run list out and, per run, cancels the token and wakes the timeline.

### Held values and landing (`RunSwitch` tail)

$$
O(N \cdot P)
$$

After `Task.WhenAll`, a target's runs are untracked, and `ApplyHeldValues` writes the end value of every entry that has no sampler — one pass over $O(N \cdot P)$ entries. `Current` advances only here, and only when no run was cancelled and nothing faulted.

### Instant switch (`Jump<T>`)

$$
O(N \cdot P)
$$

`Jump` reuses `PrepareSamplers`, then calls `ApplyImmediately`: one `TransitionProperty.SetValue` per entry whose end value is not null, then `Current`. It builds no timeline, asks for no scheduler and consults no sampler, and it contains no await point at all — so it is fully synchronous, and a `Jump` in flight cannot be cancelled (though a `Jump` cancels an animated switch in flight first).

### Runtime override (`SetThemeValue<T>` / `RestoreThemeValue<T>`)

$$
O(1) \ \text{amortized per property}
$$

A generated call stores one override entry in the instance's `Overrides` dictionary (or removes it), then refreshes that single property via `UpdatePropertyToCurrentTheme` — dictionary lookups plus at most one inheritance-chain walk in `TryGetDefaultValue` ($O(\text{depth})$).

## Memory Usage

| Structure | Complexity | Notes |
|---|---|---|
| Static theme cache | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`, keyed by declaring type; one value reference per property per theme plus `PropertyInfo` metadata. |
| Active instance overrides | $O(N \cdot P)$ worst | `ConditionalWeakTable<IThemeObject, InstanceCache>` — weak-keyed, no leaks; entries are created lazily on the first switch even when empty. |
| `ThemeManager` membership | $O(N)$ | `_act_cache` (`ConditionalWeakTable`, empty dict per object) + `activeThemes` (`List<WeakReference<IThemeObject>>`); dead entries pruned per switch. |
| Switch in flight | $O(N)$ | `_activeSwitch` holds one `SwitchTarget` (scheduler + run + frame state) per target; cleared in the `finally` around `Task.WhenAll`. |
| Prepared groups and entries | $O(N \cdot P)$ | Transient per switch; one `TransitionEntry` per property, one `TargetEntries` per target. |
| Memoized property paths | $O(\text{distinct themed } PropertyInfo)$ | `TransitionProperty.FromPropertyCache` — process-wide and never evicted. Bounded by the number of distinct property declarations, not by $N$. |
| Converter registry | $O(C)$ | `ThemeCache._converters`; currently unpopulated because the generator instantiates converters inline at registration. |

## Lookup Cost of Supporting Structures

| Operation | Complexity |
|---|---|
| Sampler registry lookup (`InterpolatorCore.TryGetInterpolator`) | $O(1)$ exact match; $O(\text{depth} + \text{interfaces})$ walking base classes and interfaces |
| Property-path factory (`TransitionProperty.FromProperty`) | $O(1)$ amortized — static `ConcurrentDictionary<PropertyInfo, TransitionProperty>` |
| Converter lookup by key (`ThemeCache.GetConverter`) | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` start-value read | $O(1)$ — active cache first, then static dictionary |
| `StartModel.Reflect` start-value read | $O(1)$ per property via `PropertyInfo.GetValue` — $O(P)$ per object per switch |
| Scheduler lookup for control (`Transition.Pause` / `Seek` / `Exit`) | $O(1)$ — `ConditionalWeakTable` keyed by target |

## Measured Behaviour

The scale demo's headless `bench` mode (`Examples/Theme/WPF/Demo/BenchRunner.cs`, run as `dotnet run -- bench`) runs the same switch at 1 / 50 / 200 / 1000 registered elements, three repetitions each, and writes a table to `%TEMP%\veloxdev-theme-scale.tsv`. The figures below are that file's, produced on 2026-09-13 by a **Debug** build of `Examples/Theme/WPF/Demo` on .NET 9 (`net9.0-windows`) on Windows 11 (10.0.26200). They measure this engine against itself at different sizes — not against any other library. The 1000-element rows were additionally measured with the tiles outside the visual tree (`attached=False`). **Absolute figures vary between runs** — on this machine the allocation columns by roughly a third, and `prep_ms` by a few milliseconds — so read them for their shape and their scaling rather than as exact values.

| elements | `prep_ms` | `anim_ms` | `frames` | `frames_per_target` | `alloc_kb` | `jump_ms` |
|---|---|---|---|---|---|---|
| 1 | 0.2 – 0.6 | 307.3 – 315.9 | 20 | 20 | 121 – 140 | 0.2 – 0.9 |
| 50 | 0.6 – 0.8 | 311.2 – 317.8 | 1 000 | 20 | 804 – 812 | 0.2 |
| 200 | 1.6 – 2.0 | 309.8 – 314.4 | 4 000 | 20 | 2 837 – 2 870 | 0.4 – 0.8 |
| 1000 | 7.1 – 10.0 | 310.4 – 320.4 | 18 416 – 19 833 | 18 – 20 | 12 625 – 13 533 | 1.6 – 4.5 |

- **`anim_ms` is flat.** Roughly 310–320 ms at every size, against a declared 300 ms effect. A thousand-fold increase in targets costs no additional wall time — this is the shared `TransitionTimeline` claim, measured rather than asserted, and it is the empirical form of the claim above: wall time is bounded by `Duration`, not by the element count $N$.
- **`prep_ms` is the part that scales with $N$.** ~0.2–0.6 ms at one element, ~7–10 ms at a thousand — linear, matching the $O(N \cdot P)$ preparation bound above ($P = 2$ per tile, plus a fixed cost per target). This is the quantity the `58ae23b3` memoization of `TransitionProperty.FromProperty` took from ~1.6 s to ~10 ms at the 1000-element size, and these rows are that memoized state.
- **Allocation is paid per switch, not per frame.** Roughly 13–22 KB per element per switch at 1000 elements depending on the run, while `frames_per_target` stays fixed at 20 and `gen1` / `gen2` stay 0 all the way up (the 1000-element rows show a single gen-0 collection). The allocation tracks the element count, not the frame count, so it is the prepared entry set that costs, and the sampling loop is allocation-free per frame.
- **`jump_ms` stays in the low single milliseconds even at 1000 elements**, which is what the synchronous, await-free `ApplyImmediately` path predicts.

## Notes

- `StartModel` defaults to `Cache`, avoiding per-property reflection at switch start; `Reflect` trades that for reading the live property value. Whichever is chosen, the prepared start is written back onto the target by `WriteStartValues` before the scheduler runs, because `InterpolatorCore.Prepare` reads the start off the target rather than from the entry.
- `TransitionProperty.FromProperty` memoization is what makes the preparation scale. Measured in commit `58ae23b3 perf(theme): memoize TransitionProperty.FromProperty`: ~1.6 s of UI-thread stall and 29 MB allocated before the first frame for a thousand two-property elements before the change, against ~10 ms and 6 MB after it.
- The weak-reference design means a registered object that is otherwise unreachable is collected (and pruned at the next switch), so long-running editors do not accumulate theme registrations. The scale demo relies on this: it drops a batch of tiles and forces one collection to make the active set exactly the new batch (`Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, `Build`).
- Per-frame write cost is low because the writes go through a compiled `TransitionProperty` setter rather than per-frame reflection (`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`).

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (`Transition`, `Jump`, `RunSwitch`, `PrepareSamplers`, `CancelActiveSwitch`, `ApplyImmediately`, `ApplyHeldValues`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`, `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs` (`CreateScheduler`, `TryGetInterpolator`), `Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs` (`FromProperty`), `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.
