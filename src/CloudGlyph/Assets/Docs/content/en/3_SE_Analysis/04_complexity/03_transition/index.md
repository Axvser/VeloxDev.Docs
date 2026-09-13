# Complexity Analysis — Transition

Let $P$ = the number of properties declared in a transition and $k$ = the depth of a property path (number of expression segments). Sampling is continuous, paced by the run's `ITimeSourceControl` (whose only time source is a `Stopwatch`), so there is no pre-computed frame array: `ITransitionEffectCore.FPS` caps the maximum sample rate (yield interval = `1000 / FPS` ms), and no per-property frame list is ever materialized.

## Building a transition (`.Property(...)` calls)

$$
O(P \cdot \bar{k})
$$

Each `.Property(lambda, value, options)` parses the lambda into a `TransitionProperty` ($O(k)$ on the path segments — `TransitionProperty.TryCreate` unwraps and walks the member chain once), stores the value (and optional interpolation options) in a `ConcurrentDictionary` (amortized $O(1)$), and, if options were given, stores the options entry. A value path additionally runs the parent/child conflict check, which compares the incoming path against every already-declared key — $O(P)$ per call, i.e. $O(P^2)$ for a whole transition (negligible in practice, $P$ being a handful of paths). The compiled getter/setter delegate is built lazily on first read/write ($O(k)$ compile, once) and reused. For the usual single-segment property this is effectively $O(1)$ per call, i.e. $O(P)$ for a whole transition.

## Sampler resolution

$$
O(1)\ \text{on a hit} \quad\Rightarrow\quad O(B + I)\ \text{on a miss}
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` first tries the exact type in `NativeInterpolators` (`ConcurrentDictionary<Type, ISampler>`) — one hash lookup. On a miss it walks the base-class chain nearest-first ($B$ = the number of ancestors) and then the type's interfaces, keeping the match whose full name is ordinally smallest ($I$ = the interface count). Interfaces are ordered explicitly because reflection does not promise an order, so the tie-break has to be named. Per-property overrides (`state.Interpolators`) add one constant-time check ahead of both, and `RegisterInterpolator`/`UnregisterInterpolator` are atomic `AddOrUpdate`/`TryRemove`, $O(1)$.

The walk costs $O(B + I)$ **once per property per animation** and never per frame: `Prepare` resolves each declared path once, and the frame path only reads the `ISampler` the `SamplerSet` already holds. `InterpolatorCoreTests` pins the order (exact → nearest base class → interface, base class over interface, ordinal name between two interfaces).

## Updater preparation (`InterpolatorCore.Prepare`)

$$
O(P) + O\!\left(\sum m_j\right)
$$

`Prepare` runs once per segment/animation. For each of the $P$ recorded properties it: binds the path to the target (`TransitionProperty.BindTo` — identity when the path carries no frozen index argument, otherwise $O(k)$), reads the current value through the compiled getter (marshalled by `ProtectedGetValue`, $O(1)$), resolves an `ISampler` ($O(1)$ on a registry hit, $O(B + I)$ on the base-class/interface walk; per-property override → registry → value-type `ISampleable`), calls `NormalizeStart`/`NormalizeEnd` once to fix the exact endpoint values, and stores a per-property `(property, sampler, start, end, options)` entry in the `SamplerSet`. A value-type `ISampleable` property adds $O(m_j)$ for the `StructAssembler`, where $m_j$ = the number of declared members (each member gets one registry lookup and one current-value read). **No per-property frame list is built.**

## Sampling loop (`TransitionInterpreterCore.Execute`)

$$
O(P)\ \text{per sample}
$$

Each sample iteration evaluates one eased time and applies it through `SamplerSet.Apply`, which walks the $P$ prepared entries (per property $O(1)$):

| Sampler | Cost per sample | Notes |
|---|---|---|
| Numeric (`Double`/`Float`/`Int`/`Long`) | $O(1)$ | one lerp |
| `ColorSampler` (ARGB channels) | $O(1)$ | 4 channel lerps |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF` | $O(1)$ | component-wise lerp |
| `Vector2`/`Vector3`/`Vector4` | $O(1)$ | component-wise lerp |
| `QuaternionSampler` (`Slerp`, optional directional negate) | $O(1)$ | constant trig |
| `DoubleSampler` with `RotationDirection` | $O(1)$ | one mod-360 delta per call, then one lerp |

**Endpoints are $O(1)$ replacements:** `t <= 0` writes the exact normalized start, `t >= 1` the exact normalized end (no sampling). Middle frames call `InsertFrame`, which for reference types mutates a per-animation `working` scratch (lazily created on the first middle-frame call and reused) — the shared `start`/`end` taken from the transition declaration are never mutated. Value types compute-and-assign. Complex adapter fallbacks (e.g. WPF blending a non-solid `Brush`) allocate per frame, but the common solid/transform paths are zero-allocation.

Middle frames are also **not clamped**: the eased value is handed to the sampler as it comes, so `Back` and `Elastic` may leave $[0,1]$ — the numeric samplers extrapolate, and a sampler that cannot pins to its endpoint. Clamping here would flatten both curves.

The number of samples is **not** dictated by `FPS` — it is the timeline-derived `elapsed / duration`, paced by the `1000 / FPS` ms yield (a throttle, not a timing source, and read per frame so a rate cap can be tightened on a running animation). A duration-$D$ pass therefore issues up to $D \cdot \text{FPS}/1000$ samples, each $O(P)$. Auto-reverse doubles the pass count; `LoopTime` adds repeats (`run.Cycle ≤ effect.LoopTime`). The wall-clock time for a finite run is

$$
T_{\text{wall}} \approx \frac{D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])}{\text{rate}}
$$

(or forever when $\text{LoopTime} = \text{int.MaxValue}$), where $\text{rate} = 1$ unless `Transition.SetRate` changed it — the rate scales elapsed time, so it divides the wall clock without touching the sample count per pass. No eased-index list is precomputed ($O(1)$ extra space).

## One wait per frame (`ReusableTimerWait`)

$$
O(1)\ \text{time}, \quad 0\ \text{bytes per wait}
$$

`ArmNextFrame` is what the loop actually waits through. Its default reuses one `Timer` for the whole loop — re-armed per frame, with **one** cancellation registration for the animation instead of one per frame. The alternative it replaces is `await Task.Delay(interval, token)`, which builds a fresh `DelayPromise` and registers a fresh cancellation callback every wait; `8dca3893` measured that at 184 bytes per wait (100 waits: 0 bytes against 18400). `ReusableTimerWaitTests` measures the same difference.

The trade is one `Timer` per animation (~200 bytes) — but only for an animation that actually waits: `RunPassAsync` draws its frame *before* it waits and returns when that frame ended the pass, so a single-frame or zero-duration pass never constructs one. Past about 1.1 frames the reused timer is already ahead. The waiting is all that changes: same wake-up count, same thread behavior, and the same `TimerQueue` `Task.Delay` itself uses — a frame that wakes late is drawn further along, not wrong.

## Scheduler lookup (`FindOrCreate`)

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` performs a `ConditionalWeakTable` lookup (`MutualSchedulers`) or allocates a fresh non-mutual scheduler. A `SemaphoreSlim.WaitAsync()` gate serializes executions on a scheduler; the per-target `NoMutualSchedulers` value is a concurrent **set** (`ConcurrentDictionary<ITransitionSchedulerCore, byte>`), so a run registers and unregisters in $O(1)$ and only enumerating it — for an `Exit`, a `Pause` or any other control call — costs $O(M)$ where $M$ = concurrent non-mutual animations on that target.

## Scheduler composition (`CreateScheduler`)

$$
O(1)
$$

`InterpolatorCore.CreateScheduler(target, effect)` is one type test against the platform's effect type plus the same `ConditionalWeakTable` lookup as any other acquisition, so it is $O(1)$ and allocates nothing to decline: the base implementation returns `null`, and only a platform that recognises the effect goes on to `FindOrCreate`. That matters because it is the entry point a caller holding only an `object` has — the theme system runs one switch across targets of many runtime types — so this is the cost of starting *any* animation in that flow, not an extra one.

## Reflected paths (`TransitionProperty.FromProperty`)

$$
O(1)\ \text{amortized per } PropertyInfo
$$

`FromProperty` goes through a static `ConcurrentDictionary<PropertyInfo, TransitionProperty>` and returns a **shared** path per `PropertyInfo`, so the $O(k)$ expression parse and the lazy getter/setter compile are paid once per property for the process, not once per switch. Sharing is safe because a path is immutable, `BindTo` returns the instance itself when there is no frozen index argument, and the lazy compile is idempotent (a concurrent first use can only compile twice and discard one).

The commit that introduced it (`58ae23b3`) measured the previous behaviour: for a thousand two-property elements, preparing the paths cost ~1.6 s of UI-thread stall and 29 MB allocated before the first frame, against ~10 ms and 6 MB after — which brings a switch's wall time to the effect's own duration regardless of how many elements it covers. The cache retains one entry per distinct `PropertyInfo` ever reflected, for the life of the process.

## Path validation

There is no capture / discovery walk to cost: animated state is declared path by path, and the only per-path overhead beyond the dictionary insert is the conflict check.

$$
O(P)\ \text{per declared value path} \;\Rightarrow\; O(P^2)\ \text{per transition}
$$

`StateCore.SetValue` compares the incoming `TransitionProperty` against every key already in `Values`, asking `IsDescendantOf` in both directions (a parent/child pair on one transition is `TransitionPathConflictException`). Each comparison is $O(k)$ on the segment chains, so declaring all $P$ paths of one transition costs $O(P^2 \cdot k)$ in total — negligible for the handful of paths a transition carries. `TransitionCore.RejectUnsampleablePaths` (called once by `Execute`/`CoreValidate`) walks the same $P$ keys and asks the registry once per path — $P$ lookups, each $O(1)$ to $O(B + I)$: $O(P \cdot (B + I))$ worst case, once per run.

## Execution scale

The scheduler work around a run is $O(1)$ per segment plus $O(M)$ for the per-target non-mutual scheduler set ($M$ = concurrent non-mutual animations on that target): `FindOrCreate` is a `ConditionalWeakTable` lookup, entering/leaving a run drains and tracks the token set under the target lock, and `Exit` cancels every tracked token of the run.

## Memory usage

| Structure | Complexity |
|---|---|
| State (`IFrameState`) | $O(P)$ dictionaries (values + interpolators + options) |
| Prepared sampler set (`SamplerSet`) | $O(P)$ — one `(property, sampler, start, end, options)` entry per property; no frame list |
| `SamplerSet` per-property `Working` scratch | $O(P)$ — lazily allocated once per animation, reused across frames |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` (collected with targets, no leaks) |
| Non-mutual scheduler table | $O(N + M)$ per target, where $M$ = concurrent non-mutual animations |
| `TransitionProperty` memo cache (`FromPropertyCache`) | $O(R)$ — one shared path per distinct `PropertyInfo` ever reflected, held for the process lifetime |
| One `ReusableTimerWait` per running loop | $O(1)$ — ~200 bytes, and nothing at all for a pass that ends on its first frame |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` — exact hit | $O(1)$ |
| `TryGetInterpolator` — miss (base-class walk, then name-ordered interfaces) | $O(B + I)$, once per property per animation |
| `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `CreateScheduler` (effect type test + CWT lookup) | $O(1)$; nothing allocated when the platform declines |
| `TransitionProperty.FromProperty` | $O(1)$ amortized; the first call per `PropertyInfo` pays the parse and the getter/setter compile |
| `.Property(...)` (expression parse + dictionary insert) | $O(k)$ per property ($O(1)$ for single-segment paths) |
| `Prepare` one property (bind path + read current + resolve sampler + normalize endpoints) | $O(1)$ (plus $O(B + I)$ on a registry miss and $O(m_j)$ for a value-type `ISampleable` member assembly) |
| `Prepare` all properties (`InterpolatorCore.Prepare`) | $O(P) + O(\sum m_j)$ |
| Sample one property (`ISampler.InsertFrame` / scratch mutation) | $O(1)$ |
| Apply one sample to all properties (`SamplerSet.Apply`) | $O(P)$ |
| Easing + clamping one sample | $O(1)$ |
| One frame's wait (`ArmNextFrame` → `ReusableTimerWait`) | $O(1)$ time, 0 bytes (one `Timer` per animation, not per frame) |
| Endpoint write (`t <= 0` / `t >= 1`) | $O(1)$ replacement, no sampling |
| Scheduler `FindOrCreate` (CWT lookup) | $O(1)$ |
| Path conflict check (`StateCore.SetValue` → `RejectPathConflict`) | $O(k)$ per already-declared path ($O(P \cdot k)$ per declared value) |
| Unsampleable-path scan (`RejectUnsampleablePaths`, once per run) | $O(P)$ registry lookups |
| Scheduler enter/leave (`Track`/`Untrack`/`DrainActive`) | $O(1)$ amortized per run (plus $O(M)$ for non-mutual registration) |

## Notes

- Samplers are **prepared once**; each sample re-evaluates only the eased time against the normalized start/end/options — there is no frame list to build, store, or re-index.
- Reference types are interpolated through a per-animation `working` scratch, so the common fast paths allocate nothing per sample (even for `LoopTime = int.MaxValue`, per-iteration memory is constant).
- `SamplerSet.Apply` reuses one cached closure per target and passes the eased time via an `Interlocked`-read field, so per-sample marshaling does not allocate a closure.
- A property path that is invalid for the current target returns the `UnreadablePath` sentinel in $O(1)$ (compiled getter), and `Prepare` skips it rather than sampling from a bogus `null`.
- `TransitionProperty` getter/setter delegates are compiled lazily once per property and shared across samples, so the sampling loop avoids reflection entirely.
- A sampler is resolved per property per animation, never per frame, so the base-class/interface walk's $O(B + I)$ stays off the frame path even though it is no longer a single hash lookup.
- `FromProperty`'s memo cache moves the reflection-driven path cost from per-switch to per-process: the parse and the compile happen once for a given `PropertyInfo`, however many switches use it.
- The wait is per *frame* in time but per *animation* in allocation: after the first frame, waiting costs nothing.

> Sources: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `TransitionInterpreter.cs`, `Transition.cs`, `TransitionRun.cs`, `ReusableTimerWait.cs`, `Src/Core/VeloxDev.Core/Timing/TimeSourceCore.cs`, `PathIndex.cs`, `State.cs`, `SamplerSet.cs`, `TransitionScheduler.cs`, `TransitionProperty.cs`, `StructAssembler.cs`, `NonPriority.cs`, `NativeSamplers/*.cs`, `Src/Core/VeloxDev.Core.Test/TransitionSystem/{InterpolatorCoreTests,ReusableTimerWaitTests}.cs`.

Related analysis: [Design patterns — Transition](../../02_design-patterns/03_transition/index.md) · [Data flow — Transition](../../03_data-flow/03_transition/index.md)
