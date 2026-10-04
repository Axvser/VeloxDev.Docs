# MVVM — `VeloxCommand` 的执行

负责派发工作、以及询问“能否运行”的五个成员。

###### `VeloxCommand.CanExecute`

**Signature:**
`bool CanExecute(object? parameter)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameter` | `object?` | 转发给 `canExecute` 谓词。 |

**Returns:** `bool` —— `(_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked`。未注册谓词时，只要命令未被强制锁定就返回 `true`。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 69-77
var command = new VeloxCommand(() => { }, canExecute: p => p is string s && s == "yes");

Assert.IsTrue(command.CanExecute("yes"));
Assert.IsFalse(command.CanExecute("no"));
Assert.IsFalse(command.CanExecute(null));
```

**Notes:** 这是 XAML 绑定的 `ICommand` 成员。它从不反映队列 —— 那请看 `IVeloxCommandStatus`。

###### `VeloxCommand.Execute`

**Signature:**
`void Execute(object? parameter)`

**Returns:** `void` —— 即发即忘；实现为 `_ = ExecuteAsync(parameter)`。

**Notes:** `ICommand` 的入口。底层调用的返回任务被丢弃，因此没有人观察方法体失败 —— 请订阅 `Failed` 或使用 `ExecuteAndWaitAsync`。

###### `VeloxCommand.ExecuteAsync`

**Signature:**
`Task ExecuteAsync(object? parameter)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameter` | `object?` | 传给命令方法体的实参。 |

**Returns:** `Task` —— 执行被**受理**时完成：低于并发容量时立即开始，否则入队。方法体结束时它**不**完成。

**Exceptions:** 方法本身不抛异常；方法体失败经 `Failed` 事件呈现，若用了 `ExecuteAndWaitAsync` 则经 `CommandCompletion` 呈现。

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

**Notes:** 时序为 `Created` →（立即 `Started`，或先 `Enqueued` 再 `Dequeued` → `Started`）→ 终点阶段 → `Exited`。

###### `VeloxCommand.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃等待；不取消执行。可选。 |

**Returns:** `Task<CommandCompletion>` —— **这一次**执行结束时完成，包括那些根本没运行的调用。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `OperationCanceledException` | `cancellationToken` 先触发。 |

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

- 该成员是 `VeloxCommand` 同时实现 `IVeloxCommandCompletion` 的两个原因之一；在 `IVeloxCommand` 引用上经 `VeloxCommandExtensions` 可做同一件事。
- 结果由执行自身的结局算出，而不是从事件里读回来，因此不依赖是否存在 `Failed` 订阅者。
- 命令保持锁定期间仍在排队的调用尚未结束，返回的任务会等到槽位释放或队列被清空。

###### `VeloxCommand.Notify`

**Signature:**
`void Notify()`

**Returns:** `void` —— 触发 `CanExecuteChanged`。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs, lines 218-222
private void RefreshCollectionCommands()
{
    RemoveSelectedItemCommand.Notify();
    MoveLastToFirstCommand.Notify();
}
```

**Notes:** 抛异常的 `CanExecuteChanged` 订阅者会被吞掉并通过 `HandlerException` 上报。
