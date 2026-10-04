# Complexity — Transition: Pacer & Scheduler

## One wait per frame

The yield interval is a cap, not a grid:

$$
\Delta_{\text{yield}} = \frac{1000}{\max(1, \text{FPS})} \ \text{ms}
$$

and it is re-read every frame, so tightening `FPS` on a running animation takes effect immediately. Because the timeline — not the wait — is the timing authority, waking late draws a frame further along rather than a wrong one; the wait only decides how often the loop *looks*.

$$
O(1)\ \text{time}, \qquad 0\ \text{bytes per wait after the first frame}
$$

`ArmNextFrame` routes through the host's `FramePacerCore` when there is one and through one reused `ReusableTimerWait` otherwise. The alternative it replaces is `await Task.Delay(interval, token)`, which builds a fresh `DelayPromise` and registers a fresh cancellation callback on every wait; commit `8dca3893` measured that at **184 bytes per wait** (100 waits: 0 bytes against 18 400). `ReusableTimerWait` is the same `Timer` queue `Task.Delay` ends up in, so it changes what a wait costs and not when it lands.

The trade is one `Timer` per *animation* (~200 bytes) — and only for an animation that actually waits: `RunPassAsync` draws its frame **before** it waits and returns when that frame ended the pass, so a single-frame or zero-duration pass never constructs one. Past about 1.1 frames the reused timer is already ahead.

## Reading the clock

The pass position is one subtraction and one conversion:

$$
\text{elapsedTicks} = \text{Timeline.Ticks} - \text{Run.PassAnchor}, \qquad \text{elapsedMs} = \frac{\text{elapsedTicks} \cdot 1000}{\text{TicksPerSecond}}
$$

Reading `Timeline.Ticks` is **lock-free**: the coherent fields are published under a sequence counter, and because the only writers are control calls a reader effectively never retries. The spin loop is $O(1)$ expected with at most a `SpinWait` on the rare torn read.

The position arithmetic itself is worth quoting because its ordering is the whole point:

$$
\text{Advance}(p, \Delta, \sigma) = p + \left\lfloor \frac{\Delta}{S} \right\rfloor \sigma + \frac{(\Delta \bmod S)\,\sigma}{S}, \qquad S = 10^4
$$

The whole part is taken out **before** anything is multiplied. The obvious $\Delta \cdot \sigma / S$ overflows at `long.MaxValue / σ`: with a speed of $10^4$ that is about 2.9 years of real time on Windows, but **10.7 days** on Linux, where a `Stopwatch` tick is a nanosecond. C# arithmetic is unchecked, so the failure is not an exception but a silent wrap to a negative position, leaving a consumer that was never paused and never seeked jammed for good. Measured (BenchmarkDotNet, commit `f5485adf`): $0.23$ ns for the multiply-first form against $0.61$ ns for this one — $0.38$ ns per frame per animation, or $2.3\ \mu s$ per second for a hundred animations at 60 FPS.

## Sampling modes

An `IUncompensatedTimeSampler` is $O(1)$ over two `long` fields with no accumulator. A `CompensatingTimeSampler` keeps integer ticks and delivers exactly

$$
\text{delivered} = \left\lfloor \frac{\text{elapsed}}{\text{Step}} \right\rfloor = \sum_{\text{calls}} \min\big(\text{pending},\ \text{MaxStepsPerCall}\big)
$$

with the sub-step remainder carried ($\text{acc} \bmod \text{Step}$) and the over-cap debt deferred rather than discarded, so the identity holds across calls. Forgiven debt is bounded:

$$
\text{dropped} = \max(0,\ \text{pending} - \text{MaxPendingSteps}), \qquad \text{pending} \le \text{MaxPendingSteps}
$$

with the default `MaxPendingSteps = 64` representing about one second at a 16 ms step. A rebase (`Epoch` change) discards the debt instead of repaying it, which is what keeps a backward seek from producing negative pushes.

## The park signal

$$
\text{cost of a paused animation} = O(1)\ \text{wake-ups per change}, \quad \text{not} \quad O\!\left(\frac{1}{\Delta_{\text{yield}}}\right)
$$

`WaitWhileStalledAsync` parks the loop on a gate installed exactly while `IsAdvancing` is false. A control call that has to be seen while stalled **replaces** the gate and completes the old one, so a parked consumer wakes once per change and re-reads the state rather than polling. Without the pairing, `while (!IsAdvancing) await WaitWhileStalledAsync()` would return immediately and spin a core hot — which is why the predicate and the signal are maintained in one place.

## Scheduler lookup

$$
O(1)
$$

`TransitionSchedulerCore.FindOrCreate(target, CanMutualTask)` is a `ConditionalWeakTable.GetValue` (mutual) or one allocation (non-mutual). `Execute` is serialized by a `SemaphoreSlim` gate; entering and leaving a run is $O(1)$ amortized — `Track` / `Untrack` are one dictionary add/remove keyed by the run's token source, and `DrainActive` (called by `Exit`) is $O(K)$ for $K$ active runs on that scheduler.

The per-target **non-mutual** table is a concurrent set, so registering and unregistering are $O(1)$ and only *enumerating* it — for an `Exit`, a `Pause`, or any other control call — costs $O(M)$, where $M$ is the number of concurrent non-mutual animations on that target. That is the one operation whose cost grows with how many animations are running, and it is why the *query* helpers (`Position`, `Cycle`, `Rate`, `IsPaused`) go through `TryGetFirstRun`, which returns the first entry without building the list — asking a target with nothing running, which is what a per-frame `Transition.Position(target)` does most of the time, allocates nothing.

`InterpolatorCore.CreateScheduler(target, effect)` is one type test against the platform's effect type plus the same lookup, so it is $O(1)$ and allocates nothing to decline: the base returns `null`, and only a platform that recognises the effect goes on to `FindOrCreate`.

## Memory footprint

| Structure | Complexity |
|---|---|
| Declared state (`IFrameState`) | $O(P)$ — three dictionaries (values + interpolators + options) |
| Prepared set (`SamplerSet`) | $O(P)$ — one `(property, sampler, start, end, options)` entry per path; **no frame list** |
| `SamplerSet` per-entry `Working` scratch | $O(P)$, lazily allocated once per animation and reused |
| Mutual scheduler table | $O(N)$ targets via `ConditionalWeakTable` — collected with the targets, no leaks |
| Non-mutual scheduler table | $O(N + M)$ per target |
| `TransitionProperty` memo cache (`FromPropertyCache`) | $O(R)$ — one shared path per distinct `PropertyInfo` ever reflected, held for the process (weakly keyed, so a collectible `AssemblyLoadContext` can still unload) |
| One `ReusableTimerWait` per running loop | $O(1)$ — ~200 bytes, and nothing at all for a pass that ends on its first frame |
| Effect events (`WeakDelegate`) | $O(H)$ handlers, $H$ = live handler targets |
| Per-animation state that survives a frame | $O(1)$ — one `TransitionRun` (timeline, anchor, cycle, token, thread) |

Two notes on that table. The `SamplerSet` replacement policy is what makes `Repeat` cheap *and* correct: a repeated segment replays the set its first iteration prepared, so the $O(P)$ preparation cost is paid once per segment however many iterations there are. And the `TransitionProperty` cache is the reason a theme switch's cost is per-*process* rather than per-*switch*: commit `58ae23b3` measured the previous behaviour at roughly **1.6 s of UI-thread stall and 29 MB allocated** for a thousand two-property elements (before the first frame), against **~10 ms and 6 MB** afterwards.

## Per-operation summary

| Operation | Complexity |
|---|---|
| `TryGetInterpolator` — exact hit | $O(1)$ |
| `TryGetInterpolator` — miss | $O(B + I)$, once per property per animation |
| `CreateScheduler` (type test + CWT lookup) | $O(1)$ |
| `TransitionProperty.FromProperty` | $O(1)$ amortized per `PropertyInfo` |
| `.Property(...)` | $O(k)$, plus $O(P \cdot k)$ for the conflict check |
| `Prepare` one property | $O(1)$, plus $O(B + I)$ on a registry miss and $O(m_j)$ for struct assembly |
| `Prepare` all properties | $O(P) + O(\sum m_j)$ |
| Sample one property (`InsertFrame`) | $O(1)$; $O(C)$ for a $C$-channel bounded group |
| Apply one sample to all properties | $O(P)$ |
| Easing + endpoint handling | $O(1)$ |
| One frame's wait | $O(1)$ time, 0 bytes after the first frame |
| `Timeline.Ticks` read | $O(1)$ expected, lock-free |
| `Advance` (position arithmetic) | $O(1)$, 0.61 ns measured |
| Scheduler `FindOrCreate` | $O(1)$ |
| Scheduler enter / leave (`Track` / `Untrack`) | $O(1)$ amortized |
| `Exit` / control sweep across runs | $O(M)$ for non-mutual runs on that target; the four queries are $O(1)$ via `TryGetFirstRun` |
| Unsampleable-path scan (`RejectUnsampleablePaths`, once per run) | $O(P)$ registry lookups |
| Diagnostic report | $O(1)$ per stage per run (a `HashSet` guard caps repeats) |

> Sources: `Src/Core/VeloxDev.Core/TransitionSystem/{TransitionInterpreter,FramePacerCore,ReusableTimerWait,TransitionScheduler,TransitionRun,TransitionProperty}.cs`, `Src/Core/VeloxDev.Core/Timing/{TimeSourceCore,CompensatingTimeSampler,UncompensatedTimeSampler}.cs`, `Src/Core/VeloxDev.Core.Test/TransitionSystem/{FramePathAllocationTests,ReusableTimerWaitTests,TimelineControlTests}.cs`, `Src/Core/VeloxDev.Core.Test/Timing/{CompensatingTimeSamplerTests,TimerCoreRegistryTests}.cs`.
