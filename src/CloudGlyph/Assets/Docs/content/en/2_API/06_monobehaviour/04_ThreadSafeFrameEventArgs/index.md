# MonoBehaviour — `ThreadSafeFrameEventArgs`

Namespace `VeloxDev.TimeLine`. A `FrameEventArgs` subclass whose `Handled` flag is safe to read and write concurrently from the Update and FixedUpdate threads.

```csharp
namespace VeloxDev.TimeLine;

public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }
}
```

### `ThreadSafeFrameEventArgs.Handled`

**Signature:**

`public new bool Handled { get; set; }`

**Returns:** `bool` — the `Handled` value, guarded by a `lock` so reads and writes are atomic across threads.

**Notes:**

- The `new` keyword hides the `virtual Handled` inherited from `TimeLineEventArgs`; the accessors lock a private object on every get and set.
- All other members (`DeltaTime`, `TotalTime`, `CurrentFPS`, `TargetFPS`) are inherited unchanged from `FrameEventArgs`.
- Thread safety verified by `TimeLineEventArgsTests.ThreadSafeFrameEventArgs_Handled_ThreadSafe` (100 concurrent tasks read/write without exception).

**Source:**

`Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`
