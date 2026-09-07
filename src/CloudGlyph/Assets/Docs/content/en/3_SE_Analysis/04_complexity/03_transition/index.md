# Complexity Analysis — Transition

Let $P$ = the number of properties recorded in a snapshot and $k$ = the depth of a property path (number of expression segments). Sampling is continuous (Stopwatch-driven), so there is no pre-computed frame array: `ITransitionEffectCore.FPS` caps the maximum sample rate (yield interval = `1000 / FPS` ms), and no per-property frame list is ever materialized.

## Building a snapshot (`.Property(...)` calls)

$$
O(P \cdot \bar{k})
$$

Each `.Property(lambda, value, options)` parses the lambda into a `TransitionProperty` ($O(k)$ on the path segments — `TransitionProperty.TryCreate` unwraps and walks the member chain once), stores the value (and optional interpolation options) in a `ConcurrentDictionary` (amortized $O(1)$), and, if options were given, stores the options entry. The compiled getter/setter delegate is built lazily on first read/write ($O(k)$ compile, once) and reused. For the usual single-segment property this is effectively $O(1)$ per call, i.e. $O(P)$ for a whole snapshot.

## Sampler resolution

$$
O(1)
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` is a `ConcurrentDictionary` lookup over `NativeInterpolators` (`ConcurrentDictionary<Type, ISampler>`). Per-property overrides (`state.Interpolators`) add one constant-time check. `RegisterInterpolator`/`UnregisterInterpolator` are atomic `AddOrUpdate`/`TryRemove`, also $O(1)$.

## Updater preparation (`InterpolatorCore.Prepare`)

$$
O(P) + O\!\left(\sum m_j\right)
$$

`Prepare` runs once per segment/animation. For each of the $P$ recorded properties it: reads the current value through the compiled getter (marshalled by `ProtectedGetValue`, $O(1)$), resolves an `ISampler` ($O(1)$; per-property override → registry → value-type `ISampleable`), calls `NormalizeStart`/`NormalizeEnd` once to fix the exact endpoint values, and stores a per-property `(property, sampler, start, end, options)` entry in the `SamplerSet`. A value-type `ISampleable` property adds $O(m_j)$ for the `StructAssembler`, where $m_j$ = the number of declared members (each member gets one registry lookup and one current-value read). **No per-property frame list is built.**

## Sampling loop (`TransitionInterpreterCore.Execute`)

$$
O(P)\ \text{per sample}
$$

Each sample iteration evaluates one eased/clamped time and applies it through `SamplerSet.Apply`, which walks the $P$ prepared entries (per property $O(1)$):

| Sampler | Cost per sample | Notes |
|---|---|---|
| Numeric (`Double`/`Float`/`Int`/`Long`) | $O(1)$ | one lerp |
| `ColorSampler` (ARGB channels) | $O(1)$ | 4 channel lerps |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF` | $O(1)$ | component-wise lerp |
| `Vector2`/`Vector3`/`Vector4` | $O(1)$ | component-wise lerp |
| `QuaternionSampler` (`Slerp`, optional directional negate) | $O(1)$ | constant trig |
| `DoubleSampler` with `RotationDirection` | $O(1)$ | one mod-360 delta per call, then one lerp |

**Endpoints are $O(1)$ replacements:** `t <= 0` writes the exact normalized start, `t >= 1` the exact normalized end (no sampling). Middle frames call `InsertFrame`, which for reference types mutates a per-animation `working` scratch (lazily created on the first middle-frame call and reused) — the shared `start`/`end` captured in the snapshot are never mutated. Value types compute-and-assign. Complex adapter fallbacks (e.g. WPF blending a non-solid `Brush`) allocate per frame, but the common solid/transform paths are zero-allocation.

The number of samples is **not** dictated by `FPS` — it is the Stopwatch-derived `elapsed / duration`, paced by the `1000 / FPS` ms yield (a throttle, not a timing source). A duration-$D$ pass therefore issues up to $D \cdot \text{FPS}/1000$ samples, each $O(P)$. Auto-reverse doubles the pass count; `LoopTime` adds repeats (`cycle ≤ LoopTime`). The wall-clock time for a finite run is

$$
T_{\text{wall}} \approx D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])
$$

(or forever when $\text{LoopTime} = \text{int.MaxValue}$). No eased-index list is precomputed ($O(1)$ extra space), and no per-frame `Task.Delay` calibration is needed.

## Scheduler lookup (`FindOrCreate`)

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` performs a `ConditionalWeakTable` lookup (`MutualSchedulers`) or allocates a fresh non-mutual scheduler. A `SemaphoreSlim.WaitAsync()` gate serializes executions on a scheduler; per-target `NoMutualSchedulers` list operations are $O(M)$ where $M$ = concurrent non-mutual animations.

## State capture (`TransitionSnapshotHelper`)

Snapshot discovery (`DiscoverAnimatableProperties`) is a recursive DFS over the object graph guarded by an object-revisit set and an ancestor-**type** guard (no fixed depth cap):

$$
O(V \cdot d)
$$

where $V$ = number of reachable composite objects/properties enumerated and $d$ = the path depth (bounded in practice by the ancestor-type guard — a member whose type is already on the current path stops the recursion). The search refuses to descend into primitives, enums, value types, `string`, `object`, `IEnumerable`, and `Delegate`, and is `ISampleable`-aware: it expands a reference-type `ISampleable` into declared member paths and captures a value-type `ISampleable` as a whole path (later assembled by `StructAssembler`). `CaptureAll`/`CaptureAllExcept` use `Interpolator.TryGetInterpolator(type, out _)` (or `ISampler` implementors) as the "can animate" predicate. Each captured property is then read once through the compiled getter: $O(P)$ read cost.

## Memory usage

| Structure | Complexity |
|---|---|
| State (`IFrameState`) | $O(P)$ dictionaries (values + interpolators + options) |
| Prepared sampler set (`SamplerSet`) | $O(P)$ — one `(property, sampler, start, end, options)` entry per property; no frame list |
| `SamplerSet` per-property `Working` scratch | $O(P)$ — lazily allocated once per animation, reused across frames |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` (collected with targets, no leaks) |
| Non-mutual scheduler table | $O(N + M)$ per target, where $M$ = concurrent non-mutual animations |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)` (expression parse + dictionary insert) | $O(k)$ per property ($O(1)$ for single-segment paths) |
| `Prepare` one property (read current + resolve sampler + normalize endpoints) | $O(1)$ (plus $O(m_j)$ for a value-type `ISampleable` member assembly) |
| `Prepare` all properties (`InterpolatorCore.Prepare`) | $O(P) + O(\sum m_j)$ |
| Sample one property (`ISampler.InsertFrame` / scratch mutation) | $O(1)$ |
| Apply one sample to all properties (`SamplerSet.Apply`) | $O(P)$ |
| Easing + clamping one sample | $O(1)$ |
| Endpoint write (`t <= 0` / `t >= 1`) | $O(1)$ replacement, no sampling |
| Scheduler `FindOrCreate` (CWT lookup) | $O(1)$ |
| `SnapshotAll` discovery (`DiscoverAnimatableProperties`) | $O(V \cdot d)$ DFS over the object graph |

## Notes

- Samplers are **prepared once**; each sample re-evaluates only the eased time against the captured start/end/options — there is no frame list to build, store, or re-index.
- Reference types are interpolated through a per-animation `working` scratch, so the common fast paths allocate nothing per sample (even for `LoopTime = int.MaxValue`, per-iteration memory is constant).
- `SamplerSet.Apply` reuses one cached closure per target and passes the eased time via an `Interlocked`-read field, so per-sample marshaling does not allocate a closure.
- A property path that is invalid for the current target returns the `UnreadablePath` sentinel in $O(1)$ (compiled getter), and `Prepare` skips it rather than sampling from a bogus `null`.
- `TransitionProperty` getter/setter delegates are compiled lazily once per property and shared across samples, so the sampling loop avoids reflection entirely.

> Sources: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `TransitionInterpreter.cs`, `TransitionSnapshotHelper.cs`, `SamplerSet.cs`, `TransitionScheduler.cs`, `TransitionProperty.cs`, `StructAssembler.cs`, `NativeSamplers/*.cs`.

Related analysis: [Design patterns — Transition](../../02_design-patterns/03_transition/index.md) · [Data flow — Transition](../../03_data-flow/03_transition/index.md)
