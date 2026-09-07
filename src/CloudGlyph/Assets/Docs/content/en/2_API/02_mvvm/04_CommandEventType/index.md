# MVVM — `CommandEventType`

`VeloxDev.MVVM.CommandEventType` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) enumerates the lifecycle state of one command execution.

**Signature**

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,
    Enqueued,
    Dequeued,
    Started,
    Completed,
    Failed,
    Canceled,
    Exited
}
```

| Value | Meaning |
|---|---|
| `None = 0` | Unset / default. |
| `Created` | A `CommandEventArgs` was allocated for the trigger. |
| `Enqueued` | Concurrency cap reached; the execution waits in the pending queue. |
| `Dequeued` | The queued execution was pulled out and is about to run. |
| `Started` | The command method actually started. |
| `Completed` | The command method returned successfully. |
| `Failed` | The command method threw a non-cancellation exception. |
| `Canceled` | The execution was canceled. |
| `Exited` | Lifecycle ended; the execution was removed from the active list. |

The `CommandEventType` is stamped on a `CommandEventArgs` (see [06_CommandEventArgs](../06_CommandEventArgs/index.md)), which is how the same execution is re-raised across its lifecycle by `VeloxCommand`. Which event the value is delivered through is defined by `IVeloxCommand` (see [02_IVeloxCommand](../02_IVeloxCommand/index.md)).
