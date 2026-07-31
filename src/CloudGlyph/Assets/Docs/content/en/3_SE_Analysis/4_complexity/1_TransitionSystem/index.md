# Complexity Analysis — Transition System

## Core Operations

Let $P$ = number of properties recorded in a snapshot, and $S$ = number of frames for the active effect:

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

### Building a snapshot (`.Property(...)` calls)

$$O(P)$$

Each `.Property(lambda, value)` parses the expression into a `TransitionProperty` (constant-time per call, `TryCreate` walks the lambda body once) and inserts into the state's `ConcurrentDictionary` ($O(1)$ amortized).

### Interpolator resolution

$$O(1)$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` is a `ConcurrentDictionary` lookup. Custom per-property interpolators and `IInterpolable` fallback add a constant check.

### Frame computation (`Interpolator.Interpolate`)

$$O(P \cdot S)$$

For each of the $P$ properties, the interpolator produces a $S$-element frame list:

- Numeric interpolators: $O(S)$ per property.
- `ColorInterpolator` (ARGB channels): $O(4S) = O(S)$.
- `QuaternionInterpolator` (`Slerp`): $O(S)$ with constant per-frame trig.

### Frame application (the interpreter loop)

$$O(P \cdot S) \quad \text{compute}, \quad O(S) \quad \text{wall-clock}$$

Each of the $S$ iterations applies $P$ `SetValue` writes. UI-thread marshalling (when started off-thread) adds $O(1)$ dispatch per frame. The total wall-clock time is bounded by `Duration` (times `LoopTime` when looping):

$$T_{\text{wall}} = \text{Duration} \times \text{LoopTime}$$

### Memory usage

| Structure | Complexity |
|---|---|
| State (`IFrameState`) | $O(P)$ dictionaries |
| Frame sequence | $O(P \cdot S)$ intermediate values, freed after the transition |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` (collected with targets) |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` / `RegisterInterpolator` | $O(1)$ |
| `.Property(...)` (expression parse) | $O(1)$ per property |
| Interpolate a property | $O(S)$ |
| Interpolate all properties | $O(P \cdot S)$ |
| Frame write (per frame) | $O(P)$ |
| Easing index lookup | $O(1)$ per frame |
| `SnapshotAll` discovery (`DiscoverAnimatableProperties`) | $O(V \cdot d)$ BFS over $V$ reachable properties up to depth $d$ |

## Notes

- Easing is applied by **re-indexing** the pre-computed frame array, so it adds $O(1)$ per frame rather than re-evaluating values.
- Long running loops (`LoopTime = int.MaxValue`) hold $O(P \cdot S)$ memory for the frame sequence but constant extra memory per iteration.
- `TransitionSnapshotHelper.CaptureAll` uses `Interpolator.TryGetInterpolator(type, out _)` as the "can animate" predicate; discovery is $O(V \cdot d)$ over the object graph.

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`, `TransitionInterpreter.cs`, `TransitionSnapshotHelper.cs`, `InterpolatorOutputCore.cs`.
