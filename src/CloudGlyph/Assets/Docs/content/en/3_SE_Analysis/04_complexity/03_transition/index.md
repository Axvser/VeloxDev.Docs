# Complexity Analysis — Transition

## Core Operations

Let $P$ = number of properties recorded in a snapshot, and $S$ = number of frames for the active effect:

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

### Building a snapshot (`.Property(...)` calls)

$$O(P)$$

Each `.Property(lambda, value)` parses the expression into a `TransitionProperty` (constant-time per call; `TryCreate` walks the lambda body once) and inserts into the state's `ConcurrentDictionary` ($O(1)$ amortized). The compiled getter/setter delegate is built lazily on first read/write and then reused.

### Interpolator resolution

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` is a `ConcurrentDictionary` lookup. Per-property custom interpolators and `IInterpolable` fallback add a constant check. `RegisterInterpolator` is an atomic `AddOrUpdate`, also $O(1)$.

### Frame computation (`InterpolatorCore.Interpolate`)

$$O(P \cdot S)$$

For each of the $P$ properties, the interpolator produces a $S$-element frame list:

| Interpolator | Cost per property | Notes |
|---|---|---|
| Numeric (`Double`/`Float`/`Int`/`Long`) | $O(S)$ | linear walk, constant ops per frame |
| `ColorInterpolator` (ARGB channels) | $O(4S) = O(S)$ | 4 channel lerps per frame |
| `Point`/`PointF`/`Size`/`SizeF`/`Rectangle`/`RectangleF`/`Vector2/3/4` | $O(S)$ | component-wise lerp |
| `QuaternionInterpolator` (`Slerp`) | $O(S)$ | constant per-frame trig (dot + possibly negate + `Slerp`) |
| `DoubleInterpolator` with `RotationDirection` | $O(S)$ | one mod-360 delta precomputed, then linear walk |

**Critical note:** the frame **lists** are materialized up-front (eager). Easing does not re-run the interpolator — the interpreter re-indexes the same array, so easing adds $O(1)$ per frame.

### Scheduler lookup (`FindOrCreate`)

$$O(1)$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` performs a `ConditionalWeakTable` lookup (`MutualSchedulers`) or allocates a fresh non-mutual scheduler. A `SemaphoreSlim.WaitAsync()` gate serializes executions on a mutual scheduler.

### Frame pump (`TransitionInterpreterCore.Execute`)

$$O(S) \text{ passes over } P \text{ properties} \quad \Rightarrow \quad O(P \cdot S) \text{ total work}$$

Each of the $S$ iterations applies $P$ `SetValue` writes through `InterpolatorOutputBase.SetValues` (compiled delegates, no per-frame reflection). UI-thread marshalling (when started off-thread) adds $O(1)$ dispatch per frame. Auto-reverse doubles the frame walk ($2S$); `LoopTime` multiplies it. The wall-clock time is bounded by:

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime} \quad (\text{or forever when } \text{LoopTime} = \text{int.MaxValue})$$

The interpreter precomputes the eased index list once: $O(S)$ space and time. `WaitForFrameAsync` is $O(1)$ per frame.

### State capture (`TransitionSnapshotHelper`)

Discovery (`DiscoverAnimatableProperties`) is a depth-limited DFS over the object graph:

$$O(V \cdot d)$$

where $V$ = number of reachable public instance properties (read/write, non-indexed) and $d \le \text{maxDepth} = 4$ (default). The search refuses to descend into primitives, enums, value types, `string`, `object`, `IEnumerable`, and `Delegate`. `CaptureAll` uses `Interpolator.TryGetInterpolator(type, out _)` as the "can animate" predicate. Each captured property is then read once via the compiled getter: $O(P)$ read cost.

### Memory usage

| Structure | Complexity |
|---|---|
| State (`IFrameState`) | $O(P)$ dictionaries (values + interpolators + options) |
| Frame sequence (`InterpolatorOutputBase.Frames`) | $O(P \cdot S)$ intermediate values, freed after the transition |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` (collected with targets, no leaks) |
| NoMutual scheduler table | $O(N \cdot M)$ per target, where $M$ = concurrent non-mutual animations |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` / `UnregisterInterpolator` | $O(1)$ |
| `.Property(...)` (expression parse + dict insert) | $O(1)$ per property |
| Interpolate one property | $O(S)$ |
| Interpolate all properties | $O(P \cdot S)$ |
| Eased index list precompute | $O(S)$ |
| Frame write (per frame) | $O(P)$ |
| Easing index lookup | $O(1)$ per frame |
| Scheduler `FindOrCreate` (CWT lookup) | $O(1)$ |
| `SnapshotAll` discovery (`DiscoverAnimatableProperties`) | $O(V \cdot d)$ DFS over the object graph |

## Notes

- Frames are **pre-computed once** and **re-indexed** for easing — the expensive per-property work happens once, before the first frame, not per frame.
- Long-running loops (`LoopTime = int.MaxValue`) hold $O(P \cdot S)$ memory for the frame sequence but constant extra memory per iteration.
- A property whose path is invalid for the current target returns the `UnreadablePath` sentinel in $O(1)$ (compiled getter), and the interpolator skips it rather than interpolating from a bogus `null`.
- `TransitionProperty` getter/setter delegates are compiled lazily once per property and shared across frames, so the frame pump avoids reflection entirely.

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `TransitionInterpreter.cs`, `TransitionSnapshotHelper.cs`, `InterpolatorOutputCore.cs`, `TransitionScheduler.cs`, `TransitionProperty.cs`.
