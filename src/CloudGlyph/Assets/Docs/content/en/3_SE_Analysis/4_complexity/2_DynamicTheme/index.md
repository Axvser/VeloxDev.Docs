# Complexity Analysis — Dynamic Theme

## Core Operations

Let $N$ = number of registered theme-aware objects, $P$ = number of themed properties per object, and $S$ = number of interpolation frames for a transition.

### Theme lookup

$$O(1)$$

Property values are stored in nested `Dictionary`s (`Type → PropertyName → ThemeType → value`), so reading a theme value is constant time.

### Register / Unregister

$$O(P) \quad \text{per object}$$

`InitializeTheme()` registers the type's properties once (amortized), then `ThemeManager.Register(this)` adds one `WeakReference`. Walking the properties to apply the current theme is $O(P)$.

### Animated switch (`Transition<T>`)

$$O(N \cdot P \cdot S)$$

For each of the $N$ objects, for each of its $P$ properties, `CalculateFrames` produces $S$ frames:

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

- Frame computation per property: $O(S)$ (one interpolate + one eased evaluation per frame).
- Frame application: $S$ sequential `Task.Delay(deltaTime)` steps, each applying one `PropertyInfo.SetValue` per frame — **wall-clock** $O(S \cdot \Delta t)$, i.e. bounded by `Duration`.
- Memory for pre-computed frames: $O(N \cdot P \cdot S)$ temporary during the transition.

Example with `TransitionEffects.Theme` ($FPS = 60$, $Duration = 0.46s$):

$$S = \left\lfloor \frac{460 \times 60}{1000} \right\rfloor = 27 \quad \text{frames per property}$$

### Instant switch (`Jump<T>`)

$$O(N \cdot P)$$

No frames; each property is set directly to its target value.

### Runtime override (`SetThemeValue<T>`)

$$O(P)$$

Writes one override entry into the instance's active cache and updates the property.

## Memory Usage

| Structure | Complexity |
|---|---|
| Static theme cache (per registered type) | $O(T \cdot P \cdot K)$, $T$ = types, $K$ = themes |
| Active instance overrides | $O(N \cdot P)$, released via `WeakReference` — no leaks |
| Transition frame buffers | $O(N \cdot P \cdot S)$ temporary |

## Notes

- `StartModel.Cache` avoids reflection during animation start (uses the cache); `StartModel.Reflect` reads the live property value via `PropertyInfo.GetValue` — negligible per property but $O(P)$ per object per transition.
- Interpolator registry lookup is $O(1)$ (`ConcurrentDictionary<Type, IValueInterpolator>`).
- Converter lookup by key is $O(1)$ (`Dictionary<string, IThemeValueConverter>`).

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (lines 83–106, 153–407), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.
