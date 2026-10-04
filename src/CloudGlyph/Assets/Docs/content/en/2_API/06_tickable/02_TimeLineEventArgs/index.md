# `TimeLineEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public abstract class TimeLineEventArgs
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`.

The base of every payload the time-line system hands to user code. It exists for exactly one reason: to carry `Handled` to both argument types without duplicating it. It is `abstract`, so it has no public constructor and cannot be instantiated.

Base type of `FrameEventArgs` and of `TransitionEventArgs`.

#### Property: `TimeLineEventArgs.Handled`

**Signature:**
`public virtual bool Handled { get; set; }`

**Returns:** `bool` — `false` by default.

**Exceptions:** none.

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs (lines 13-22)
var args = new TransitionEventArgs();
Assert.IsFalse(args.Handled);          // default is false

args = new TransitionEventArgs { Handled = true };
Assert.IsTrue(args.Handled);
```

**Notes:**
- The type is `virtual`, not abstract — a derived payload can override the accessors, and both `FrameEventArgs` and `TransitionEventArgs` inherit it unchanged. Nothing in the framework overrides it today, so `Handled` behaves as a plain field on every argument a hook receives.
- The documented meaning, from the source comment: *"False : default | True : kill the time line."* In the frame loop that "kill" is scoped to the current frame phase, not to the whole channel — see `05_frame-events-and-thread-safety` in the Quick Start.
- It is the only writable member of a `FrameEventArgs`; the four timing properties have `internal` setters.
