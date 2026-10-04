# `TimeLineEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
    public TimeSpan DeltaTime { get; internal set; } = TimeSpan.Zero;
    public TimeSpan TotalTime { get; internal set; } = TimeSpan.Zero;
}
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`.

The base of every payload the time-line system hands to user code. It carries two things: the `Handled` kill switch, and the two clock readings every subscriber of a frame shares (`DeltaTime` / `TotalTime` — moved up here from `FrameEventArgs` so the transition system's arguments inherit them too). It is `abstract`, so it has no public constructor and cannot be instantiated.

Base type of `FrameEventArgs` and of `TransitionEventArgs`; the latter now lives in `VeloxDev.TransitionSystem` (see the transition feature's [event arguments](../../03_transition/00_transitionsystem/04_transition-event-args/index.md)).

#### Property: `TimeLineEventArgs.Handled`

**Signature:**
`public virtual bool Handled { get; set; }`

**Returns:** `bool` — `false` by default.

**Exceptions:** none.

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs (lines 28-36)
var args = new FrameEventArgs();
Assert.IsFalse(args.Handled);          // default is false

args = new FrameEventArgs { Handled = true };
Assert.IsTrue(args.Handled);
```

**Notes:**
- The type is `virtual`, not abstract — a derived payload can override the accessors, and both `FrameEventArgs` and `TransitionEventArgs` inherit it unchanged. Nothing in the framework overrides it today, so `Handled` behaves as a plain field on every argument a hook receives.
- The documented meaning, from the source comment: *"False : default | True : kill the time line."* In the frame loop that "kill" is scoped to the current frame phase, not to the whole channel — see `05_frame-events-and-thread-safety` in the Quick Start.
- It is the only **writable** member of the whole family: user code sets `Handled` and reads everything else.

#### Property: `TimeLineEventArgs.DeltaTime`

**Signature:**
`public TimeSpan DeltaTime { get; internal set; }`

**Returns:** `TimeSpan` — time elapsed since the previous frame. Defaults to `TimeSpan.Zero`.

**Notes:**
- `internal` setter: the frame pump writes it (`TickManager`'s `CreateFrameEventArgs`) and the transition interpreter writes it once per sample. User code only reads it.
- For the tickable feature it is the frame interval of the same pump, with the channel's time scale applied. For the transition system it is this frame's advance (see [transition event arguments](../../03_transition/00_transitionsystem/04_transition-event-args/index.md)).

#### Property: `TimeLineEventArgs.TotalTime`

**Signature:**
`public TimeSpan TotalTime { get; internal set; }`

**Returns:** `TimeSpan` — time since this line's clock started, published from the clock rather than accumulated. Defaults to `TimeSpan.Zero`.

**Notes:**
- `internal` setter, like `DeltaTime`.
- For the tickable feature it is virtual time since the channel started (reset to zero by `StopAsync`). For the transition system it is the time accumulated since the current segment began — it does **not** reset per pass; the pass is `TransitionEventArgs.Loop`.
- Neither reading is monotonic across a rebase: a step-size change or a restart re-anchors the clock.
