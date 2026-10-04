# MVVM — `VeloxCommand` execution

The five members that dispatch work and ask whether it may run.

###### `VeloxCommand.CanExecute`

**Signature:**
`bool CanExecute(object? parameter)`

| Parameter | Type | Description |
|---|---|---|
| `parameter` | `object?` | Forwarded to the `canExecute` predicate. |

**Returns:** `bool` — `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked`. With no predicate registered it is `true` unless the command is force-locked.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 69-77
var command = new VeloxCommand(() => { }, canExecute: p => p is string s && s == "yes");

Assert.IsTrue(command.CanExecute("yes"));
Assert.IsFalse(command.CanExecute("no"));
Assert.IsFalse(command.CanExecute(null));
```

**Notes:** this is the `ICommand` member bound by XAML. It never reflects the queue — see `IVeloxCommandStatus` for that.

###### `VeloxCommand.Execute`

**Signature:**
`void Execute(object? parameter)`

**Returns:** `void` — fire-and-forget; implemented as `_ = ExecuteAsync(parameter)`.

**Notes:** the `ICommand` entry point. The returned task of the underlying call is discarded, so nothing observes a body failure — subscribe to `Failed` or use `ExecuteAndWaitAsync`.

###### `VeloxCommand.ExecuteAsync`

**Signature:**
`Task ExecuteAsync(object? parameter)`

| Parameter | Type | Description |
|---|---|---|
| `parameter` | `object?` | The argument passed to the command body. |

**Returns:** `Task` — completes when the execution has been **accepted**: it starts immediately when below the concurrency cap, otherwise it is enqueued. It does **not** complete when the body finishes.

**Exceptions:** none thrown by the method itself; a body failure surfaces through the `Failed` event, and through `CommandCompletion` if `ExecuteAndWaitAsync` was used.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 30-42
var gate = new CommandGate();
var command = new VeloxCommand(gate.RunAsync, semaphore: 1);

_ = command.ExecuteAsync(null);                       // takes the only slot
await gate.WaitForStartedAsync();

var waiting = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.IsBusy() && command.PendingCount() == 1);
```

**Notes:** the sequence is `Created` → (`Started` immediately, or `Enqueued` and later `Dequeued` → `Started`) → terminal stage → `Exited`.

###### `VeloxCommand.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| Parameter | Type | Description |
|---|---|---|
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons the wait only; it does not cancel the execution. Optional. |

**Returns:** `Task<CommandCompletion>` — completes when *this* execution has ended, including the calls that never run.

**Exceptions:**

| Exception | Condition |
|---|---|
| `OperationCanceledException` | `cancellationToken` fired first. |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 72-82
var command = new VeloxCommand(() => Task.CompletedTask);
await command.LockAsync();

var completion = await command.ExecuteAndWaitAsync(null).WaitAsync(CommandTestKit.Timeout);

Assert.AreEqual(CommandOutcome.Refused, completion.Outcome,
    "a refused call never raises Exited, so this is the only way to observe it");
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 44-56
var boom = new InvalidOperationException("boom");
var command = new VeloxCommand((_, _) => Task.FromException(boom));

// deliberately no Failed subscriber: the result must not depend on someone having subscribed
var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.AreSame(boom, completion.Exception);
```

**Notes:**

- This member is one of the two reasons `VeloxCommand` also implements `IVeloxCommandCompletion`; the same operation is available on an `IVeloxCommand` reference through `VeloxCommandExtensions`.
- The result is computed from the execution's own outcome, not read back from the events, so it does not depend on a `Failed` subscriber existing.
- A queued call that the command stays locked on has not ended, so the returned task waits until a slot frees or the queue is cleared.

###### `VeloxCommand.Notify`

**Signature:**
`void Notify()`

**Returns:** `void` — raises `CanExecuteChanged`.

**Example:**

```csharp
// Source: Demo — Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs, lines 218-222
private void RefreshCollectionCommands()
{
    RemoveSelectedItemCommand.Notify();
    MoveLastToFirstCommand.Notify();
}
```

**Notes:** a `CanExecuteChanged` subscriber that throws is swallowed and reported through `HandlerException`.
