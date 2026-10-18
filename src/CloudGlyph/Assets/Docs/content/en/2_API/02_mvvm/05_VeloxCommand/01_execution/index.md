# MVVM — `VeloxCommand` execution

The members that dispatch work and ask whether it may run.

###### `VeloxCommand.CanExecute`

**Signature:**
`bool CanExecute(object? parameter)`

| Parameter | Type | Description |
| --- | --- | --- |
| `parameter` | `object?` | Forwarded to the `canExecute` predicate. |

**Returns:** `bool` — the predicate's answer combined with the force-lock flag. With no predicate the command is executable unless locked.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var command = new VeloxCommand(() => { }, canExecute: p => p is string s && s == "yes");

Assert.IsTrue(command.CanExecute("yes"));
Assert.IsFalse(command.CanExecute("no"));
Assert.IsFalse(command.CanExecute(null));
```

**Notes:** this is the `ICommand` member bound by XAML. It never reflects the queue — see `IVeloxCommandStatus` for that. A `null` argument is executable only when the parameter type can hold `null`; otherwise the answer is `false` rather than an exception.

###### `VeloxCommand.Execute`

**Signature:**
`void Execute(object? parameter)`

**Returns:** `void` — fire-and-forget; implemented as `_ = ExecuteAsync(parameter)`.

**Notes:** the `ICommand` entry point. Nothing observes a body failure; subscribe to `Failed` or use `ExecuteAndWaitAsync`.

###### `VeloxCommand.ExecuteAsync(object?)`

**Signature:**
`Task ExecuteAsync(object? parameter)`

**Returns:** `Task` — completes when the execution has been **accepted**: it starts immediately when below the concurrency cap, otherwise it is enqueued. It does **not** complete when the body finishes.

**Exceptions:** none thrown by the method itself. A body failure surfaces through the `Failed` event and through `CommandCompletion` if `ExecuteAndWaitAsync` was used.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var gate = new CommandGate();
var command = new VeloxCommand(gate.RunAsync, semaphore: 1);

_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

var waiting = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.IsBusy() && command.PendingCount() == 1);
```

**Notes:** the sequence is `Created` → (`Started` immediately, or `Enqueued` and later `Dequeued` → `Started`) → terminal stage → `Exited`.

###### `VeloxCommand.ExecuteAsync(object?, CancellationToken)`

**Signature:**
`Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)`

**Returns:** the body's value, boxed — or `null` when it returned none.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `Exception` | the body threw; the original instance is rethrown |
| `OperationCanceledException` | the execution was cancelled |
| `InvalidOperationException` | the call was refused because the command was locked |

**Notes:** the token abandons the wait only. This overload has no default for `cancellationToken` deliberately: a default would make a one-argument call ambiguous with `ExecuteAsync(object?)`.

###### `VeloxCommand.Execute(object?, out object?)`

**Signature:**
`void Execute(object? parameter, out object? result)`

**Returns:** `void`; `result` receives the body's value.

**Exceptions:** same outcomes as the awaitable twin; on any of them it throws and assigns `result = null`. It blocks on the queue as well as on the body and must not be called from inside the same command's body.

###### `VeloxCommand.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| Parameter | Type | Description |
| --- | --- | --- |
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons the wait only; it does not cancel the execution. Optional. |

**Returns:** `Task<CommandCompletion>` — completes when *this* execution has ended, including calls that never run.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `OperationCanceledException` | `cancellationToken` fired first. |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);
await command.LockAsync();

var completion = await command.ExecuteAndWaitAsync(null).WaitAsync(CommandTestKit.Timeout);

Assert.AreEqual(CommandOutcome.Refused, completion.Outcome);
```

**Notes:** the outcome is computed from the execution itself, not read back from events. A queued call that stays queued has not ended, so the task waits until a slot frees or the queue is cleared.

###### `VeloxCommand.Notify`

**Signature:**
`void Notify()`

**Returns:** `void` — raises `CanExecuteChanged`.

**Example:**

```csharp
// Source: Demo — Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs
private void RefreshCollectionCommands()
{
    RemoveSelectedItemCommand.Notify();
    MoveLastToFirstCommand.Notify();
}
```

**Notes:** a throwing `CanExecuteChanged` subscriber is swallowed and reported through `HandlerException`.
