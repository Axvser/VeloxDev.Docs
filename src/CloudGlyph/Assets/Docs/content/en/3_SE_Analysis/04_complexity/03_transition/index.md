# Complexity Analysis — Transition

## Core Operations

Let $P$ = number of properties recorded in a snapshot. Sampling is continuous (Stopwatch-driven), so there is no pre-computed frame count: `ITransitionEffectCore.FPS` caps the maximum sample rate (yield interval = `1000 / FPS` ms), and no $S$-element per-property frame list is ever materialized.

### Building a snapshot (`.Property(...)` calls)

$$O(P)$$

Each `.Property(lambda, value)` parses the expression into a `TransitionProperty` (constant-time per call; `TryCreate` walks the lambda body once) and inserts into the state's `ConcurrentDictionary` ($O(1)$ amortized). The compiled getter/setter delegate is built lazily on first read/write and then reused.

### Sampler resolution

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` is a `ConcurrentDictionary` lookup over `NativeInterpolators` (`ConcurrentDictionary<Type, ISampleable>`). Per-property custom samplers (`state.Interpolators`) and the `ISampleable` self-fallback on the current/new value add a constant check. `RegisterInterpolator` is an atomic `AddOrUpdate`, also $O(1)$.

### Updater preparation (`InterpolatorCore.Prepare`)

$$O(P)$$

`Prepare` runs once per animation. For each of the $P$ properties it: reads the current value via the compiled getter (`ProtectedGetValue`, $O(1)$), resolves a sampler ($O(1)$), calls `Normalize` once, and stores a per-property `(property, sampler, start, end, options)` entry. **No per-property frame list is built** — the per-sample value is computed lazily at sampling time.

### Sampling loop (`TransitionInterpreterCore.Execute`)

$$O(P) \text{ per sample}$$

Each sample iteration evaluates one eased/clamped time `t ∈ [0,1]` and applies it through `SamplerSet.Apply`, which walks the $P$ prepared sampler entries. Per property the work is $O(1)$:

| Sampler | Cost per sample | Notes |
|---|---|---|
| Numeric (`Double`/`Float`/`Int`/`Long`) | $O(1)$ | one lerp |
| `ColorSampler` (ARGB channels) | $O(1)$ | 4 channel lerps |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF`/`Vector2/3/4` | $O(1)$ | component-wise lerp |
| `QuaternionSampler` (`Slerp`) | $O(1)$ | constant trig (dot + possibly negate + `Slerp`) |
| `DoubleSampler` with `RotationDirection` | $O(1)$ | one mod-360 delta per call, then a single lerp |

**Endpoints are $O(1)$ replacements:** `t <= 0` writes the exact start value, `t >= 1` the exact end value (no sampling). Reference types are mutated **in place** inside `ISampler.Update` (the live `start` instance), so middle samples allocate nothing; value types compute-and-assign.

The number of samples is **not** dictated by `FPS` — it is the Stopwatch-derived `elapsed / duration`, throttled only by a coarse 1 ms `Task.Delay` yield (not a timing source). A pass therefore issues roughly `Duration / 1ms` samples at most, each $O(P)$. Auto-reverse doubles the pass count; `LoopTime` multiplies it. The wall-clock time is bounded by:

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime} \quad (\text{or forever when } \text{LoopTime} = \text{int.MaxValue})$$

No eased-index list is precomputed ($O(1)$ extra space), and there is no per-frame `Task.Delay` calibration.

### Scheduler lookup (`FindOrCreate`)

$$O(1)$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` performs a `ConditionalWeakTable` lookup (`MutualSchedulers`) or allocates a fresh non-mutual scheduler. A `SemaphoreSlim.WaitAsync()` gate serializes executions on a mutual scheduler.

### State capture (`TransitionSnapshotHelper`)

Discovery (`DiscoverAnimatableProperties`) is a depth-limited DFS over the object graph:

$$O(V \cdot d)$$

where $V$ = number of reachable public instance properties (read/write, non-indexed) and $d \le \text{maxDepth} = 4$ (default). The search refuses to descend into primitives, enums, value types, `string`, `object`, `IEnumerable`, and `Delegate`. `CaptureAll` uses `Interpolator.TryGetInterpolator(type, out _)` as the "can animate" predicate. Each captured property is then read once via the compiled getter: $O(P)$ read cost.

### Memory usage

| Structure | Complexity |
|---|---|
| State (`IFrameState`) | $O(P)$ dictionaries (values + interpolators + options) |
| Prepared sampler set (`SamplerSet`) | $O(P)$ — one `(property, sampler, start, end, options)` entry per property; no frame list |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` (collected with targets, no leaks) |
| NoMutual scheduler table | $O(N \cdot M)$ per target, where $M$ = concurrent non-mutual animations |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)` (expression parse + dict insert) | $O(1)$ per property |
| `Prepare` one property (read current + resolve sampler + create updater) | $O(1)$ |
| `Prepare` all properties (`InterpolatorCore.Prepare`) | $O(P)$ |
| Sample one property (`ISampler.Update` / in-place mutation) | $O(1)$ |
| Apply one sample to all properties (`SamplerSet.Apply`) | $O(P)$ |
| Easing + clamping one sample | $O(1)$ |
| Endpoint write (t <= 0 / t >= 1) | $O(1)$ replacement, no sampling |
| Scheduler `FindOrCreate` (CWT lookup) | $O(1)$ |
| `SnapshotAll` discovery (`DiscoverAnimatableProperties`) | $O(V \cdot d)$ DFS over the object graph |

## Notes

- Updaters are **prepared once** in `O(P)`; each sample re-evaluates only the eased time against the captured start/end/options — there is no frame list to build, store, or re-index, and no eager `count` boxed objects.
- Reference types are mutated **in place** inside `ISampler.Update`, so middle samples allocate nothing per sample (constant extra memory per iteration even for `LoopTime = int.MaxValue`).
- A property whose path is invalid for the current target returns the `UnreadablePath` sentinel in $O(1)$ (compiled getter), and `Prepare` skips it rather than sampling from a bogus `null`.
- `TransitionProperty` getter/setter delegates are compiled lazily once per property and shared across samples, so the sampling loop avoids reflection entirely.

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `TransitionInterpreter.cs`, `TransitionSnapshotHelper.cs`, `SamplerSet.cs`, `TransitionScheduler.cs`, `TransitionProperty.cs`.
