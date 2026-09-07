# MonoBehaviour — `TimeLineEventArgs`

Namespace `VeloxDev.TimeLine`. Abstract base class of every event-arguments type dispatched by the TimeLine system. It carries the `Handled` flag, which a handler can set to `true` to stop the remaining handlers of the current dispatch.

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

### `TimeLineEventArgs.Handled`

**Signature:**

`public virtual bool Handled { get; set; }`

**Returns:** `bool` — `false` is the default; `true` kills the current dispatch (the remaining behaviours of the frame phase are skipped).

**Notes:**

- Declared `virtual`: `FrameEventArgs` inherits it unchanged and `ThreadSafeFrameEventArgs` hides it behind a lock-protected `new` property.
- In the frame loop the manager reads `Handled` after each behaviour invocation and stops when it is `true` (see `MonoBehaviourManager`).
- Default `false` (verified by `TimeLineEventArgsTests.FrameEventArgs_DefaultValues` and the `TransitionEventArgs_Handled_*` tests).

**Source:**

`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`
