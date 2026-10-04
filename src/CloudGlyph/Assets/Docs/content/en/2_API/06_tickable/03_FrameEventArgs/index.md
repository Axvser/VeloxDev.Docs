# `FrameEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public class FrameEventArgs : TimeLineEventArgs
{
    public int CurrentFPS { get; internal set; } = 0;
    public int TargetFPS { get; internal set; } = 0;
}
```

Source: `Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`.

What every `Update`, `LateUpdate` and `FixedUpdate` hook receives. It declares only the two frame-rate readings; `Handled`, `DeltaTime` and `TotalTime` are inherited from [TimeLineEventArgs](../02_TimeLineEventArgs/index.md) (the clock readings moved up to the base so the transition system's arguments share them).

**Every property in this family has an `internal` setter** — user code reads the measurements and writes only `Handled`. The setters are called from `LoopChannel.CreateFrameEventArgs` (`TickManager.cs` lines 824-833), which fills a pooled instance from a single `TimeSample`.

#### Property: `FrameEventArgs.CurrentFPS`

**Signature:**
`public int CurrentFPS { get; internal set; }`

**Returns:** `int` — measured frames per second, default `0`.

**Notes:**
- Measured against the **wall clock**, not the virtual one, so halving the time scale does not halve this number (`UpdatePerformanceStats` remarks, line 919).
- Republished at most once per wall-clock second; between publications a reader sees the previous value. A short run can therefore read `0` here while the loop is plainly running — the Quick Start program waits 1.1 s before printing it for that reason.

#### Property: `FrameEventArgs.TargetFPS`

**Signature:**
`public int TargetFPS { get; internal set; }`

**Returns:** `int` — the channel's configured target, default `0` until the first frame is built.

**Notes:**
- Reflects the channel setting at the moment the frame was built, so it lags `SetTargetFPS` by up to one frame — the request goes through the config queue and is applied at a frame boundary.
- `CurrentFPS` and `TargetFPS` are the two numbers to compare when a loop looks wrong; the demo shows both.

#### Inherited: `DeltaTime`, `TotalTime`, `Handled`

All three come from `TimeLineEventArgs` unchanged (source: `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`); this type does not override them.

- `DeltaTime` (`TimeSpan`, `internal` set) — time elapsed since the previous frame **of the same pump**, with the channel's time scale already applied. Taken from the clock's sample, not difference-computed by the loop, so a stalled channel contributes nothing here rather than a lump (`CreateFrameEventArgs` remarks, lines 818-822). Update and FixedUpdate each have their own measurement: `DeltaTime` inside `FixedUpdate` is the fixed step (`_fixedSampler.Step`, default 16 ms), not the frame interval. Because the sample is taken *before* the hooks run, a hook that blocks changes the **next** frame's `DeltaTime`, not its own.
- `TotalTime` (`TimeSpan`, `internal` set) — virtual time since the channel started, published from the clock rather than accumulated. It excludes everything spent stalled, applies the rate, and is reset to zero by `StopAsync`. A `FixedUpdate` push receives `sample.Step × stepTicks` — the step ordinal times the step size. It is **not** monotonic under a step-size change: rebasing the sampler discards the accumulator and keeps the delivered-step count, so `TotalTime` jumps while the step ordinal does not.
- `Handled` (`bool`, `get; set;`) — the only writable member. `false` when the frame is built; a hook sets it to stop the remaining behaviours of that frame phase.
