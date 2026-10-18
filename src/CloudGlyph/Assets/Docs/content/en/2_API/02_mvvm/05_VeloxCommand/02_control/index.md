# MVVM — `VeloxCommand` lifecycle control

The lock / interrupt / clear / continue family, each available synchronously (fire-and-forget) and as an awaitable `Async` twin. All are also declared on `IVeloxCommand`, so generated command properties expose them too.

###### `VeloxCommand.Lock` / `VeloxCommand.LockAsync`

**Signature:**
`void Lock()` — `Task LockAsync()`

**Returns:** `Task` (async form) — completes once the force-lock is set and `CanExecuteChanged` has been raised.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandControlTests.cs
await command.LockAsync();
Assert.IsFalse(command.CanExecute(null));

await command.ExecuteAsync(null);

Assert.HasCount(1, recorder.Of(CommandEventType.Canceled));
Assert.HasCount(0, recorder.Of(CommandEventType.Started));
```

**Notes:** entering the lock refuses new calls (`Created` → `Canceled`) but does not interrupt running ones. `Interrupt` and `Clear` borrow the lock and hand it back, so a command that was already locked stays locked afterwards.

###### `VeloxCommand.Unlock` / `VeloxCommand.UnlockAsync`

**Signature:**
`void Unlock()` — `Task UnlockAsync()`

**Returns:** `Task` (async form) — completes once the lock is cleared and the queue drained as far as capacity allows.

**Notes:** the spelling is `Unlock`, not `UnLock`. Only that spelling exists on `IVeloxCommand` and on every command type.

###### `VeloxCommand.Interrupt` / `VeloxCommand.InterruptAsync`

**Signature:**
`void Interrupt()` — `Task InterruptAsync()`

**Returns:** `Task` (async form) — completes once the active executions have been cancelled.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var running = command.ExecuteAndWaitAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await running.WaitAsync(CommandTestKit.Timeout)).Outcome);
```

**Notes:** cancels each active item's cancellation source and raises `Canceled` once per execution. Queued items stay queued — use `Clear` to drop them. A body that already finished and disposed its source is skipped (`ObjectDisposedException` is caught), and a throwing cancellation callback is swallowed so the command can never end up permanently locked.

###### `VeloxCommand.Clear` / `VeloxCommand.ClearAsync`

**Signature:**
`void Clear()` — `Task ClearAsync()`

**Returns:** `Task` (async form) — completes once the queue is empty and the active executions have been cancelled.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

var queued = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.PendingCount() == 1);

await command.ClearAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await queued.WaitAsync(CommandTestKit.Timeout)).Outcome);
```

**Notes:** pending items are reported in queue order — `Dequeued` for each first, then `Canceled`. A dropped pending item never runs, never raises `Started` / `Exited`, and its per-execution cancellation source is disposed by `ClearAsync` itself.

###### `VeloxCommand.Continue` / `VeloxCommand.ContinueAsync`

**Signature:**
`void Continue()` — `Task ContinueAsync()`

**Returns:** `Task` (async form).

**Notes:** starts queued work when the command is not force-locked; otherwise a no-op.

###### `VeloxCommand.ChangeSemaphore` / `VeloxCommand.ChangeSemaphoreAsync`

**Signature:**
`void ChangeSemaphore(int s)` — `Task ChangeSemaphoreAsync(int semaphore)`

| Parameter | Type | Description |
| --- | --- | --- |
| `s` / `semaphore` | `int` | The new maximum number of concurrent executions. |

**Returns:** `Task` (async form).

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `ArgumentOutOfRangeException` | the value is less than 1. The synchronous overload validates before dispatching, because an exception thrown only inside the async method would become an unobserved exception. |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandConcurrencyTests.cs
await command.ChangeSemaphoreAsync(3);
await gate.WaitForStartedAsync(3);
Assert.AreEqual(3, gate.StartedCount);
```

**Notes:** raising the cap drains the queue immediately; lowering it never cancels anything already running.
