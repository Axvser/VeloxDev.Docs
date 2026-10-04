# Complexity Analysis — Transition

Let $P$ = the number of properties declared in a transition, $k$ = the depth of a property path (number of expression segments), $B$ = the number of base classes above a value's type, and $I$ = the number of interfaces that type implements. Sampling is continuous and paced by the run's `ITimeSourceControl`, so there is no pre-computed frame array: `ITransitionEffectCore.FPS` caps the maximum sample rate, and no per-property frame list is ever materialized.

## Sub-pages

- [interpolation](00_interpolation/index.md) — building a transition, resolving a sampler, `Prepare`, and the per-sample cost (including what an overshoot costs and why only the five bounded-channel samplers clamp — `Color`, `Size`, `SizeF`, `Rectangle`, `RectangleF` — while `Quaternion` pins its endpoints and the rest extrapolate).
- [pacer-and-scheduler](01_pacer-and-scheduler/index.md) — the per-frame wait, the timeline read, scheduler lookup and the registry tables, and the memory footprint.

## Headline numbers

| Operation | Complexity | Once per |
|---|---|---|
| `.Property(...)` (parse + insert + conflict check) | $O(k) + O(P \cdot k)$ | declaration |
| `TryGetInterpolator` — exact hit | $O(1)$ | property per animation |
| `TryGetInterpolator` — miss | $O(B + I)$ | property per animation |
| `Prepare` all properties | $O(P) + O(\sum m_j)$ | segment per animation |
| Apply one sample to all properties | $O(P)$ | frame |
| Scheduling the next frame | $O(1)$ time, 0 bytes after the first frame | frame |
| `FindOrCreate` (scheduler lookup) | $O(1)$ | segment per animation |
| Path conflict check | $O(P \cdot k)$ per declared value | declaration |

The one structural claim worth repeating: **every per-frame cost is a constant plus $O(P)$**, because the sampler, the endpoints and the compiled accessor were all resolved once, in `Prepare`. Nothing on the frame path parses, resolves, reflects or allocates a closure.

Related analysis: [Design patterns — Transition](../../02_design-patterns/03_transition/index.md) · [Data flow — Transition](../../03_data-flow/03_transition/index.md)
