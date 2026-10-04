# Complexity — Transition: Interpolation

## Building a transition (`.Property(...)` calls)

$$
O(P \cdot \bar{k}) \;\Rightarrow\; O(P^2 \cdot k) \text{ per transition when the conflict check is counted}
$$

Each `.Property(lambda, value, options)` parses the lambda into a `TransitionProperty` — $O(k)$ on the path segments, since `TransitionProperty.TryCreate` unwraps and walks the member chain once — stores the value (and optional options) in a `ConcurrentDictionary` ($O(1)$ amortized), then runs the parent/child conflict check, which compares the incoming path against **every** already-declared key with `IsDescendantOf` in both directions. Each comparison is $O(k)$ on the segment chains, so declaring all $P$ paths of one transition costs $O(P^2 \cdot k)$ in total — negligible for the handful of paths a transition carries, and the price of making "one object, one path" a build-time invariant rather than a runtime surprise.

The compiled getter/setter delegate is built **lazily on first read/write** ($O(k)$ compile, once) and reused. `FromProperty` (the reflection-driven entry point) is memoized per `PropertyInfo`, so the parse and the compile are paid once per property for the process, not once per switch.

## Sampler resolution

$$
O(1)\ \text{on a hit} \quad\Rightarrow\quad O(B + I)\ \text{on a miss}
$$

`InterpolatorCore.TryGetInterpolator(Type, out _)` tries the exact type in the registry (one hash lookup). On a miss it walks the base-class chain nearest-first ($B$ ancestors) and then the type's interfaces, keeping the match whose full name is ordinally smallest ($I$ interfaces). Interfaces are ordered explicitly because reflection does not promise an order, so the tie-break has to be named.

The walk costs $O(B + I)$ **once per property per animation** and never per frame: `Prepare` resolves each declared path once, and the frame path only reads the `ISampler` the `SamplerSet` already holds. Per-property overrides add one constant-time check ahead of both legs, and `RegisterInterpolator` / `UnregisterInterpolator` are atomic `AddOrUpdate` / `TryRemove`, $O(1)$.

## Preparation (`InterpolatorCore.Prepare`)

$$
O(P) + O\!\left(\sum_{j} m_j\right)
$$

`Prepare` runs once per segment. For each of the $P$ recorded paths it binds the path to the target (`BindTo` — identity when the path carries no frozen index argument, otherwise $O(k)$), reads the current value through the compiled getter **on the target's thread** ($O(1)$), resolves an `ISampler` (the three legs above), calls `NormalizeStart` / `NormalizeEnd` once, and stores one entry. A value-type `ISampleable` property adds $O(m_j)$, the number of declared members, each getting one registry lookup and one value read. **No per-property frame list is built.**

## One frame

The pass position is the distance from the pass anchor into the source:

$$
\text{rawT} = \frac{\text{ms}(\text{Timeline.Ticks} - \text{Run.PassAnchor})}{D}, \qquad D = \text{effect.Duration.TotalMilliseconds}
$$

$$
\text{easedT} = \begin{cases} 1 & \text{forward pass, } \text{rawT} \ge 1 \\[2pt] 0 & \text{reverse pass, } \text{rawT} \ge 1 \\[2pt] \text{Ease}(\text{rawT}) & \text{otherwise (forward)} \\[2pt] \text{Ease}(1 - \text{rawT}) & \text{otherwise (reverse)} \end{cases}
$$

and the value written is the sampler's own business, but every numeric sampler is a lerp:

$$
\text{value}(t) = s + (e - s) \cdot t
$$

Note that `easedT` is **not clamped**: `Back` peaks at about $1.10$ and `Elastic` at about $1.37$, and clamping would flatten both curves. Each sampler decides what an out-of-range $t$ means.

Per sample the cost is $O(P)$ — one `InsertFrame` per prepared entry, each $O(1)$ (one lerp, one component-wise lerp, or one `Slerp`) — plus $O(1)$ for the easing evaluation itself.

## What an overshoot costs

An eased time outside $[0, 1]$ is legal, and what happens to it is decided per value class:

- **Extrapolating classes** (`double`, `float`, `int`, `long`, `Point`, `PointF`, `Vector*`, `Rectangle`-positions, `Thickness`) just carry the lerp past the endpoint and back. That is why a transition's `Duration` and its overshoot are independent: a $\pm 3.8\%$ overshoot of a 200 px travel is about 7.6 px, a constant cost.
- **Bounded-channel classes** (`Color`, `Size`, `SizeF`, `Rectangle`, `RectangleF`) route through `BoundedProgress`, which finds the largest progress that keeps every added channel inside its range. With channels $\{(s_j, e_j)\}$ and bounds $[m, M]$:

$$
\text{progress} = \max\!\Big(t \; \text{clamped iteratively:} \; \forall j,\; \frac{\min(M - s_j,\; m - s_j)}{e_j - s_j} \le \text{progress} \le \frac{\max(M - s_j,\; m - s_j)}{e_j - s_j}\Big)
$$

which `Add` implements as two comparisons per channel, so the whole group is $O(C)$ for $C$ channels — constant, and the order channels are added in does not matter because `Add` only ever tightens. The remaining overshoot is dropped for the group. For an eased time in $[0, 1]$ the result is exactly that time, so an in-range animation pays the comparison and nothing else.
- **Fixed-range classes** (`Quaternion`) cannot overshoot at all: `Quaternion.Slerp` is defined on $[0, 1]$, and the sampler returns the caller's own instance at exactly $t = 0$ / $t = 1$.

The `ColorSampler` case is the instructive one. $R$, $G$, $B$ share one $[0, 255]$ progress so an overshoot cannot shift the hue; alpha keeps the full eased time because it is its own single-channel range and letting it into the group would let an already-opaque opacity truncate the colour's overshoot. Channels **saturate** rather than wrap, because a bare `(byte)` cast turns $300$ into $44$:

$$
\text{Channel}(v) = \begin{cases} 0 & v \le 0 \\ 255 & v \ge 255 \\ \lfloor v \rfloor & \text{otherwise} \end{cases}
$$

## Wall-clock time of a finite run

The number of samples is **not** dictated by `FPS`; it is the timeline-derived $\text{elapsed} / D$, throttled by the $1000 / \text{FPS}$ ms yield. A duration-$D$ pass therefore issues up to $D \cdot \text{FPS} / 1000$ samples, each $O(P)$. Auto-reverse doubles the pass count; `LoopTime` adds repeats; `Repeat` multiplies the chain.

$$
T_{\text{wall}} \approx \frac{D \times (\text{LoopTime} + 1) \times (1 + [\text{IsAutoReverse}])}{\text{rate}} \times R
$$

where $R$ is the number of `Repeat` iterations of the outermost loop (note $R = 1$ for a chain with no `Repeat`, and $R = \text{count} + 1$ for a `Repeat(count)`), and $\text{rate} = 1$ unless `Transition.SetRate` changed it — the rate scales elapsed time, so it divides the wall clock without touching the sample count per pass.

## Per-frame allocation

| Path | Per-sample allocation |
|---|---|
| The eased time into `Apply` | $0$ — one cached closure per target, the time passed via an `Interlocked` field |
| A numeric / value-type sampler | $0$ — computes and assigns |
| A reference-type sampler with a `working` scratch | $0$ after the first middle frame — the scratch is created once and reused |
| The wait | $0$ after the first frame — one `Timer` per loop, not per frame |

The two exceptions are the ones `AUTO TEST` exists to catch: an adapter sampler that must allocate a framework object per frame (blending a non-solid `WPF` `Brush` is the documented one), and a sampler that produces a value the framework rejects — which is why the conformance suite checks the **junction** (a real transition run) as well as the arithmetic.

> Sources: `Src/Core/VeloxDev.Core/TransitionSystem/Sampling/Interpolator.cs`, `TransitionInterpreter.cs`, `TransitionProperty.cs`, `BoundedProgress.cs`, `Eases.cs`, `NativeSamplers/{ColorSampler,SizeSampler,QuaternionSampler}.cs`, `Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,SamplerConformanceTests,EaseOvershootTests}.cs`, `Examples/Transition/AUTO TEST/Conformance/ClosedForm.cs`.
