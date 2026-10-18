# MVVM — `VeloxCommand` status, events and teardown

##### Properties

| Name | Type | Access | Description |
| --- | --- | --- | --- |
| `EventContext` | `SynchronizationContext?` | get / set | The context lifecycle events are raised on, or `null` (the default) for the pipeline's thread. |
| `IsBusy` | `bool` | get | An execution is running or waiting for a free slot. |
| `ActiveCount` | `int` | get | How many executions are running right now. |
| `PendingCount` | `int` | get | How many calls are waiting for a free slot. |

The three status properties satisfy `IVeloxCommandStatus`. Each is read without taking the command's own lock, so a concurrent update can leave it one step stale — deliberate, because a property getter must not block.

###### `VeloxCommand.EventContext`

**Signature:**
`SynchronizationContext? EventContext { get; set; }`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs
var command = new VeloxCommand(() => Task.CompletedTask) { EventContext = context };
```

**Notes:**

- Set this to the UI framework's context so subscribers stop marshalling by hand. It is off by default because inline raising is the historical behaviour, and a subscriber that already marshals would otherwise pay twice.
- Raising through a context is asynchronous: events are posted in order, but one can reach its handler after the raising call returned. When the command is already on that context, events are raised inline and nothing is posted.
- Leave it `null` where a handler must observe the command at the exact moment the event is raised.

##### Events

| Name | Type | Description |
| --- | --- | --- |
| `Created` | `CommandEventHandler?` | An execution request was accepted. |
| `Enqueued` | `CommandEventHandler?` | Capacity is full; the request joined the pending queue. |
| `Dequeued` | `CommandEventHandler?` | A queued request left the queue and is about to run. |
| `Started` | `CommandEventHandler?` | The wrapped method began. |
| `Completed` | `CommandEventHandler?` | The method returned normally. |
| `Failed` | `CommandEventHandler?` | The method threw; `e.Exception` carries it. |
| `Canceled` | `CommandEventHandler?` | The execution was cancelled or refused. At most once per execution. |
| `Exited` | `CommandEventHandler?` | The execution left the active set. |
| `CanExecuteChanged` | `EventHandler?` | The standard `ICommand` event. |
| `HandlerException` | `Action<Exception>?` (static) | A subscriber of one of the command's events or of `CanExecuteChanged` threw. |

The typed events (`CommandEventHandler<TParam, TResult>`) are implemented **explicitly** from `IVeloxCommandEvents<TParam, TResult>`; subscribe through a reference typed as that interface to receive the argument and result unboxed. See `16_typed-commands`.

###### `VeloxCommand.HandlerException` (static)

**Signature:**
`static event Action<Exception>? HandlerException`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandDiagnosticsTests.cs
void Hook(Exception ex) => reported.TrySetResult(ex);

VeloxCommand.HandlerException += Hook;
try
{
    var command = new VeloxCommand(() => Task.CompletedTask);
    var recorder = new CommandEventRecorder(command);
    command.Started += _ => throw boom;

    await command.ExecuteAsync(null);
    await recorder.FirstExit;

    Assert.AreSame(boom, await reported.Task.WaitAsync(CommandTestKit.Timeout));
}
finally
{
    VeloxCommand.HandlerException -= Hook;
}
```

**Notes:**

- A throwing subscriber never disturbs the command: the lifecycle carries on and the exception is not rethrown. Without this hook the failure would be invisible.
- With nothing subscribed the command behaves exactly as if the event did not exist, and a hook that itself throws is ignored.
- It is process-wide: the backing store is the non-generic `CommandDiagnostics` type, so every command shape reports to the same subscribers.

###### `VeloxCommand.Dispose`

**Signature:**
`void Dispose()`

**Returns:** `void` — releases the command's internal `SemaphoreSlim`.

**Notes:**

- For teardown, and only once nothing is in flight — disposing while a call is queued or running makes that call's next lock acquisition throw.
- A command that is merely dropped needs no teardown: the lock holds no unmanaged resource.
- Disposal is final.
