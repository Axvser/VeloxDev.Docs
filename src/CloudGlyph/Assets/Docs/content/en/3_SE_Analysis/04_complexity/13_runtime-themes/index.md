# Runtime themes

A theme switch is a fan-out over registered theme objects. The manager prunes dead weak references, snapshots the live targets, calls the changing hook on each, and then either writes end values immediately (`Jump`) or runs one transition per target (`Transition`). Everything is linear in targets times properties; the per-instance generated members add a reflection-based fallback per property.

Notation: $n$ registered targets, $T$ live targets, $P_t$ themed properties of target $t$, $K_t$ properties actually animated, $m$ members on the declaring type, $D$ inheritance depth, $R$ registered samplers.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `Register` | $O(1)$ amortized | $O(1)$ per instance | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:75` |
| `Unregister` | $O(n)$ | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:89` |
| `SetCurrent<T>` | $O(1)$ | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:69` |
| Dispatch (`Transition` / `Jump`) | $O(n)$ prune + snapshot + hook | $O(T)$ | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:112` |
| Prepare samplers | $O(\sum_t P_t D)$ | $O(\sum_t P_t)$ | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:439` |
| Animated per frame | $O(\sum_t K_t)$ writes + $O(T)$ dispatches | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:245` |
| `Jump` end values | $O(\sum_t P_t)$ writes | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:164` |
| `SetThemeValue` / `RestoreThemeValue` | $O(m + D)$ | $O(\text{overridden properties})$ | `Src/Generators/VeloxDev.Core.Generator/Theme.cs:303` |
| `InitializeTheme` | $O(P) + O(D)$ locks | $O(P)$ | `Src/Generators/VeloxDev.Core.Generator/Theme.cs:389` |

## Dispatch prunes, snapshots, then fans out

The target list is scanned twice — once to drop dead weak references, once to build the live array that the hook loop walks:

```csharp
CancelActiveSwitch();
activeThemes.RemoveAll(x => !x.TryGetTarget(out _));
var actives = activeThemes.Select(x => x.TryGetTarget(out var obj) ? obj : null).Where(x => x != null).ToArray();
foreach (var themeObject in actives)
{
    themeObject?.ExecuteThemeChanging(current, themeType);
}
```

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:120-126`

`Unregister` is $O(n)$ for the same reason: it removes by scanning the weak-reference list. There is no constant-time reverse index from instance to slot.

## Animated switches reuse the transition engine

The switch creates one shared timeline, then schedules one transition per target and awaits them together:

```csharp
var timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
foreach (var (scheduler, group) in planned)
{
    WriteStartValues(group);
    var run = new TransitionRun(timeline);
    scheduler.Track(run);
    runs.Add(new SwitchTarget(scheduler, run, BuildState(group)));
}
Interlocked.Exchange(ref _activeSwitch, runs);
foreach (var item in runs) tasks.Add(item.Scheduler.Execute(interpolator, item.State, effect, item.Run.Cts));
await Task.WhenAll(tasks);
```

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:239-268`

Fresh start values are reflection-level writes, $O(\sum_t P_t)$, before the loops start. Per frame the cost is the same as a transition with $k = K_t$ properties, summed over targets:

$$
T_{\text{switch}}(T) = O\!\left(\sum_t K_t\right) + O(T)\ \text{dispatches}
$$

```plot
{
  "title": "Theme switch cost vs live targets",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "10*x", "color": "#4a9eff", "title": "P = 10 properties per target" },
    { "fn": "40*x", "color": "#f472b6", "title": "P = 40 properties per target" }
  ]
}
```

`Jump` skips the animation and writes every end value synchronously, same order, no timer. `SetCurrent` only changes the type field and is constant-time.

## Per-instance overrides and the static cache

`SetThemeValue` creates nested dictionaries on demand and resolves the property by reflection; restoring removes the override and updates the property. The generated update path falls back to a default-value lookup that walks base types, taking the cache lock once per level:

```csharp
while (current != null && current != typeof(object))
{
    lock (_lock) { if (_staticCache.TryGetValue(current, out var props) && props.TryGetValue(propertyName, out var entry) && entry.Values.TryGetValue(themeType, out value)) return true; }
    current = current.BaseType;
}
```

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs:127-141`

That makes an override or a fallback lookup $O(m + D)$: $m$ for the reflection member lookup and $D$ for the inheritance walk. `InitializeTheme` pays one type registration plus, per instance, a fresh static-cache dictionary and one reflective set per themed property.

## Memory

The static cache holds one entry per declaring type and property, with a value dictionary sized by the theme count: $O(\text{types} \times \text{properties} \times \text{themes})$. Overrides are stored per instance in a weak table, $O(\text{instances} \times \text{overridden properties} \times \text{themes})$. A switch transiently allocates one entry per target and property, plus one shared timeline and one transition run per target; `_activeSwitch` retains all of it until the switch completes or a newer switch cancels it.
