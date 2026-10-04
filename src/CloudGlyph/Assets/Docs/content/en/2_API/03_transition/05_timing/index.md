# Transition — Sub-module: `VeloxDev.Timing`

The clock the transition engine reads. It is a **sub-module of the transition feature** rather than a feature of its own: `VeloxDev.Timing` (`Src/Core/VeloxDev.Core/Timing/**` + `Interfaces/Timing/**`, first added 2026-09-14) is keyword-level infrastructure shared by transition / dynamic-theme / tickable, and the transition system is its first and heaviest consumer. The `dynamic-theme` feature reaches it through a theme switch, and the `tickable` feature through `TickManager`.

Every animation is anchored to an `ITimeSource` instead of to a framework clock: `TransitionRun.Timeline` is one, and every control call (`Pause`, `Resume`, `SetRate`, `Seek`) acts on it. That is what lets several animations share a transport, and what makes "cannot be driven that way" a property of the source rather than of each consumer.

## Why it exists

Three properties a framework's own clock does not give the engine, and that the previous design had to re-derive per platform:

- **A pause is excluded, not skipped.** `Stopwatch` keeps running while a flag says "don't count"; a source that simply does not advance while paused makes the exclusion constructive, and removes the post-resume delta spike the old design had.
- **A run can park.** A consumer waits on `WaitWhileStalledAsync` rather than polling, so a paused or frozen animation costs **no timer wake-ups at all**.
- **Time is shared.** Several consumers can be anchored to one source, so one pause stops a frame loop and the animations running over it.

## Sub-pages

- [contracts](00_contracts/index.md) — `TimeSample`, `ITimeSource`, `ITimeSourceControl`, `ITimeSampler`, `IUncompensatedTimeSampler`, `ICompensatingTimeSampler`.
- [implementation](01_implementation/index.md) — `TimeConversion`, `TimeSourceCore`, `UncompensatedTimeSampler`, `CompensatingTimeSampler`, and the `TimerCore` registry.

## Where the engine meets it

| Engine type | How it uses the timing layer |
|---|---|
| `Abstractions.TransitionRun` | Holds the `ITimeSourceControl` the run is anchored to, the `PassAnchor` (where the current pass started in that source) and the `Cycle` counter |
| `Abstractions.TransitionInterpreterCore` | Reads `timeline.Ticks` for the pass position, `timeline.IsAdvancing` to decide whether to draw-then-park, `TimeConversion.TicksToMilliseconds` to convert, and `timeline.TicksPerSecond` as the unit |
| `TransitionCore.Seek` / `Position` | Converts between a `TimeSpan` and the source's tick unit with `TimeConversion`, and writes `run.PassAnchor` |
| `TransitionCore.Pause` / `Resume` / `SetRate` | Forward the call to `run.Timeline` |
| `Abstractions.SamplerSet` (a test driving the interpreter directly) | Falls back to `TimerCore.CreateTimeSource<ITimeSourceControl>()` for its own private, uncontrollable run |
| `TransitionCore.ExecuteCoreAsync` | Creates the default source with `TimerCore.CreateTimeSource<ITimeSourceControl>()` when the caller supplied none |
