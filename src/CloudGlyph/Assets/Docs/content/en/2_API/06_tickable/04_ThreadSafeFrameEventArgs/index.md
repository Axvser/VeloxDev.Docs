# `ThreadSafeFrameEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
```

Source: `Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`.

A `FrameEventArgs` whose `Handled` property is guarded by a lock, for hosts that set the flag from a thread other than the one running the hooks.

#### Property: `ThreadSafeFrameEventArgs.Handled`

**Signature:**
`public new bool Handled { get; set; }`

**Returns:** `bool` — the lock-guarded flag, default `false`.

**Exceptions:** none.

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs (lines 48-63)
var args = new ThreadSafeFrameEventArgs();
var tasks = new List<Task>();
for (int i = 0; i < 100; i++)
{
    tasks.Add(Task.Run(() =>
    {
        args.Handled = true;
        _ = args.Handled;
        args.Handled = false;
    }));
}
Task.WaitAll(tasks.ToArray());
// No exception = thread-safe access works
```

**Notes:**
- Declared with **`new`**, not `override`. This is the important detail: `Handled` on the base is `virtual`, but this type hides it rather than overriding it. A `ThreadSafeFrameEventArgs` read through a `FrameEventArgs` reference therefore resolves to the **base, unsynchronised** property. Use the static type, or the lock buys nothing.

```csharp
FrameEventArgs baseRef = new ThreadSafeFrameEventArgs();
baseRef.Handled = true;      // writes FrameEventArgs.Handled — NOT synchronised

ThreadSafeFrameEventArgs own = new ThreadSafeFrameEventArgs();
own.Handled = true;          // writes the locked property
```

- **The frame loop never constructs this type.** `LoopChannel.CreateFrameEventArgs` draws a plain `FrameEventArgs` from `_frameEventArgsPool`, and that is what every hook is handed. There is no public option to make a channel use the thread-safe variant. It exists for hosts that build their own arguments and pass them to their own dispatch code.
- Because the framework does not use it, it has no interaction with pooling, with `Handled`'s per-frame-phase reset, or with the fixed pump's per-step arguments.
- `DeltaTime`, `TotalTime`, `CurrentFPS` and `TargetFPS` keep their `internal` setters from the base — the thread-safe type adds no writable timing property.
