# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the delegate type for the command lifecycle events.

**Signature**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

**Notes:**

- The payload is a single `CommandEventArgs`, not the standard .NET `(object? sender, CommandEventArgs e)` pair.
- `IVeloxCommand` exposes one event of this type per lifecycle state (`Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`) — see [IVeloxCommand](../02_IVeloxCommand/index.md).
- Subscriber exceptions are swallowed by `VeloxCommand` (`RaiseCommandEvent`), so one faulty handler does not break the command pipeline.
