# MVVM — `VeloxCommand` status, events and teardown

##### Properties

| Name | Type | Access | Description |
|---|---|---|---|
| `EventContext` | `SynchronizationContext?` | get / set | The context lifecycle events are raised on, or `null` (the default) to raise them on whatever thread the pipeline is on. |
| `IsBusy` | `bool` | get | An execution is running or waiting for a free slot. |
| `ActiveCount` | `int` | get | How many executions are running right now. |
| `PendingCount` | `int` | get | How many calls are waiting for a free slot. |

The three status properties correspond to the members of `IVeloxCommandStatus`; each is read without taking the command's own lock, so a concurrent update can leave it one step stale — deliberate, since a property getter must not block.

###### `VeloxCommand.EventContext`

**Signature:**
`SynchronizationContext? EventContext { get; set; }`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs, lines 62-63
var command = new VeloxCommand(() => Task.CompletedTask) { EventContext = context };
```

**Notes:**

- Set this to the UI framework's context so subscribers stop marshalling by hand. It is off by default because raising on the pipeline's thread is what the command has always done, and a subscriber that already marshals would otherwise pay for it twice.
- Raising through a context is asynchronous: events are posted in order, but one can reach its handler after the call that raised it has already returned. When the command is already on that context, events are raised inline and nothing is posted.
- Leave it `null` where a handler must observe the command at the exact moment the event is raised.

##### Events

| Name | Type | Description |
|---|---|---|
| `Created` | `CommandEventHandler?` | An execution request was accepted. |
| `Enqueued` | `CommandEventHandler?` | Capacity is full; the request joined the pending queue. |
| `Dequeued` | `CommandEventHandler?` | A queued request left the queue and is about to run. |
| `Started` | `CommandEventHandler?` | The wrapped method actually began. |
| `Completed` | `CommandEventHandler?` | The method returned normally. |
| `Failed` | `CommandEventHandler?` | The method threw; `e.Exception` carries it. |
| `Canceled` | `CommandEventHandler?` | The execution was cancelled or refused. At most once per execution. |
| `Exited` | `CommandEventHandler?` | The execution finished and left the active set. |
| `CanExecuteChanged` | `EventHandler?` | The standard `ICommand` event. |
| `HandlerException` | `Action<Exception>?` (static) | A subscriber of one of the command's events, or of `CanExecuteChanged`, threw. |

###### `VeloxCommand.HandlerException` (static)

**Signature:**
`static event Action<Exception>? HandlerException`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandDiagnosticsTests.cs, lines 27-47
void Hook(Exception ex) => reported.TrySetResult(ex);

VeloxCommand.HandlerException += Hook;
try
{
    var command = new VeloxCommand(() => Task.CompletedTask);
    var recorder = new CommandEventRecorder(command);
    command.Started += _ => throw boom;

    await command.ExecuteAsync(null);
    await recorder.FirstExit;

    Assert.AreSame(boom, await reported.Task.WaitAsync(CommandTestKit.Timeout),
        "the handler's failure is reported instead of vanishing");
}
finally
{
    VeloxCommand.HandlerException -= Hook;
}
```

**Notes:**

- A throwing subscriber never disturbs the command: the lifecycle carries on either way and the exception is not rethrown. That is deliberate — a broken `Exited` handler must not strand the queue — but it also means the failure would otherwise be invisible.
- With nothing subscribed the command behaves exactly as if this event did not exist, and a hook that itself throws is ignored, so subscribing can never break the command that reported to you.
- Static, therefore process-wide: it is shared by every command. Subscribe and unsubscribe in matching scopes, and beware parallel tests.

###### `VeloxCommand.Dispose`

**Signature:**
`void Dispose()`

**Returns:** `void` — releases the command's internal `SemaphoreSlim`.

**Example:**

```csharp
// Source: Inferred from the disposal contract (Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs, line 832)
using var command = new VeloxCommand(token => RunAsync(token));
```

**Notes:**

- For teardown, and only once nothing is in flight — disposing while a call is queued or running makes that call's next lock acquisition throw.
- A command that is merely dropped needs no teardown: the lock holds no unmanaged resource.
- Disposal is final; a disposed command cannot be used again.

## Source references

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` — `HandlerException` 223, `CanExecuteChanged` 225, the eight lifecycle events 228-242, `EventContext` 260, `IsBusy` 269, `ActiveCount` 276, `PendingCount` 283, `Dispose` 832.
