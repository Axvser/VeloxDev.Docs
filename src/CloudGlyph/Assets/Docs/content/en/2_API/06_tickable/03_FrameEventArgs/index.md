# `FrameEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public class FrameEventArgs : TimeLineEventArgs
```

Source: `Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`.

What every `Update`, `LateUpdate` and `FixedUpdate` hook receives. Inherits `Handled` from `TimeLineEventArgs`.

**Every one of the four timing properties below has an `internal` setter.** That is the load-bearing fact about this type: user code reads the measurements and writes only `Handled`. The setters are called from `LoopChannel.CreateFrameEventArgs` (`TickManager.cs` lines 824-833), which fills a pooled instance from a single `TimeSample`.

#### Property: `FrameEventArgs.DeltaTime`

**Signature:**
`public TimeSpan DeltaTime { get; internal set; }`

**Returns:** `TimeSpan` — time elapsed since the previous frame **of the same pump**, with the channel's time scale already applied. Defaults to `TimeSpan.Zero`.

**Notes:**
- Taken from the clock's sample, not difference-computed by the loop, so a stalled channel contributes nothing here rather than a lump (`CreateFrameEventArgs` remarks, lines 818-822).
- Update and FixedUpdate each have their own measurement: `DeltaTime` inside `FixedUpdate` is the fixed step (`_fixedSampler.Step`, default 16 ms), not the frame interval.
- Because the sample is taken *before* the hooks run, a hook that blocks changes the **next** frame's `DeltaTime`, not its own.
- A rate of `0` parks the pumps, so no frame is delivered at all — there is no "zero delta" frame to observe.

#### Property: `FrameEventArgs.TotalTime`

**Signature:**
`public TimeSpan TotalTime { get; internal set; }`

**Returns:** `TimeSpan` — virtual time since the channel started, published from the clock rather than accumulated. Defaults to `TimeSpan.Zero`.

**Notes:**
- Excludes everything spent stalled, and applies the rate: this is the clock's position, not a sum of deltas (`UpdatePerformanceStats`, lines 906-916).
- Reset to zero by `StopAsync`. A `FixedUpdate` push receives `sample.Step × stepTicks` — the step ordinal times the step size — rather than the last reading repeated (`FixedUpdateLoop`, lines 480-487).
- **Not** monotonic under a step-size change: rebasing the sampler discards the accumulator and keeps the delivered-step count, so `TotalTime` jumps while the step ordinal does not. The WPF demo reads the step ordinal, not `TotalTime`, for that reason (`SimState.cs` comments).

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
