# Data Flow — Transition

The engine runs the same core pipeline on every platform adapter. A run is **three-phase** inside each segment: the builder resolves a scheduler for the target, the scheduler *prepares* a normalized `SamplerSet` (reads current values, resolves samplers, fixes endpoints), then the interpreter drives a *continuous* sampling loop, anchored to the run's timeline and marshaling each frame write to the host's thread. This section draws the run lifecycle, the pacing and UI-thread hop, and the error path — all as PlantUML sequence diagrams.

## Sub-pages

- [run-lifecycle](00_run-lifecycle/index.md) — `Execute` → scheduler → `Awake` → `Prepare` → interpreter, and what a **prepared state** (one `SamplerSet` entry per declared path) contains.
- [pacing-and-marshal](01_pacing-and-marshal/index.md) — how the loop decides *when* to sample (timeline + `FramePacerCore` / `ReusableTimerWait`) and how each frame is marshaled to the owning thread.
- [error-path](02_error-path/index.md) — what happens when a callback, sampler, host dispatch or `Prepare` throws: the `Warn` / `Error` channel, and why the run still unwinds through `Canceled` + `Finally`.

## Flow summary

| Scenario | Behavior |
|---|---|
| Normal run | `CoreExecute` queues every chained segment, then per segment: `await delay` → scheduler `Execute` (gate) → `Awake` on the host's thread → `Prepare` builds one `SamplerSet` entry per property → interpreter samples continuously and applies each frame through the host → `Completed` + `Finally`. |
| `IsAutoReverse` | After the forward pass the interpreter runs a backward pass (same samplers; pass end `easedT = 0`). |
| `LoopTime` / `Repeat` | `LoopTime` repeats one segment's passes; `Repeat(count)` repeats a segment's *loop*, wrapping the chain from the first segment through that one, and replays the frame set the first iteration prepared. |
| Sampling cadence | The timeline decides *when* a frame is; `1000 / max(1, FPS)` ms only caps how often the loop looks. A stalled timeline parks the loop, which then costs no wake-ups at all. |
| `Pause` / `Resume` / `SetRate` / `Seek` | `Transition.*` act on the run's `ITimeSourceControl`, **not** on the scheduler: a pause freezes the clock (so the paused time is excluded, not skipped), a rate change rebases first (so it does not jump the position), and a seek replaces `run.PassAnchor` (and, for the `cycle` overload, the pass counter). |
| Shared timeline | Two runs given the same `ITimeSourceControl` share a transport but keep their own pass and place in it, so one `Pause` freezes both while one `Exit` stops only one. |
| Index arguments | Re-evaluated every frame by default, so the path follows them while the end value stays where it was read. `PathIndex.Frozen(i)` pins the slot for the whole animation and is part of the path's identity. |
| Reflected paths | `TransitionProperty.FromProperty` returns a memoized shared path per `PropertyInfo`, so a theme switch stops recompiling getters and setters for every target on every switch. |
| New mutual run on the same target | `CoreExecute` drains and cancels the previous run's tokens first (bumping the generation); the previous run gives up at its next check, so queued frames are skipped. |
| `TransitionEventArgs.Handled = true` | An event handler makes the interpreter throw `OperationCanceledException` → `Canceled` + `Finally`; the timeline stops. |
| A throwing callback / sampler / host | Reported once through `Error`, then the run unwinds down its **normal** cancellation path, so `Canceled` and `Finally` still fire and the loop's resources are still released. |
| Property without a sampler / invalid path | A path that does not match the target's runtime type is skipped in `Prepare` (`UnreadablePath`) and reported through `Warn`; a declared **reference-type** path with no sampler is rejected by `Execute` (`TransitionPathUnsampleableException`) instead of animating nothing. Other properties keep animating. |
| App shutting down | `SamplerSet.CanSetValue()` returns `host.IsAlive == false` → `Apply` skips the write and fires no further events. |

Related analysis: [Design patterns — Transition](../../02_design-patterns/03_transition/index.md) · [Complexity — Transition](../../04_complexity/03_transition/index.md)
