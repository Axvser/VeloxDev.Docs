# MVVM — `VeloxCommand` 执行

负责派发工作与查询"能否运行"的成员。

###### `VeloxCommand.CanExecute`

**Signature:**
`bool CanExecute(object? parameter)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `parameter` | `object?` | 转发给 `canExecute` 谓词。 |

**返回：** `bool` —— 谓词结果与强制锁标志的组合。没有谓词时，命令在未锁定时可执行。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var command = new VeloxCommand(() => { }, canExecute: p => p is string s && s == "yes");

Assert.IsTrue(command.CanExecute("yes"));
Assert.IsFalse(command.CanExecute("no"));
Assert.IsFalse(command.CanExecute(null));
```

**说明：** 这是 XAML 绑定的 `ICommand` 成员。它从不反映队列 —— 队列问题见 `IVeloxCommandStatus`。只有形参类型能容纳 `null` 时，`null` 实参才可执行；否则回答 `false` 而不是抛异常。

###### `VeloxCommand.Execute`

**Signature:**
`void Execute(object? parameter)`

**返回：** `void` —— fire-and-forget；实现为 `_ = ExecuteAsync(parameter)`。

**说明：** `ICommand` 入口。方法体失败无人观察；订阅 `Failed` 或使用 `ExecuteAndWaitAsync`。

###### `VeloxCommand.ExecuteAsync(object?)`

**Signature:**
`Task ExecuteAsync(object? parameter)`

**返回：** `Task` —— 在调用被**受理**时完成：低于并发容量则立即启动，否则入队。它**不**等待方法体结束。

**异常：** 方法本身不抛。方法体失败通过 `Failed` 事件或 `ExecuteAndWaitAsync` 的 `CommandCompletion` 呈现。

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

**说明：** 序列是 `Created` →（立即 `Started`，或先 `Enqueued` 后 `Dequeued` → `Started`）→ 终止阶段 → `Exited`。

###### `VeloxCommand.ExecuteAsync(object?, CancellationToken)`

**Signature:**
`Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)`

**返回：** 方法体的值（装箱）；方法体无返回值时是 `null`。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `Exception` | 方法体抛出；原始实例被重新抛出 |
| `OperationCanceledException` | 执行被取消 |
| `InvalidOperationException` | 命令被锁定，调用被拒绝 |

**说明：** token 只放弃等待。该重载刻意不给 `cancellationToken` 默认值：否则单实参调用会与 `ExecuteAsync(object?)` 产生歧义。

###### `VeloxCommand.Execute(object?, out object?)`

**Signature:**
`void Execute(object? parameter, out object? result)`

**返回：** `void`；`result` 接收方法体的值。

**异常：** 与可等待版本相同的三种结局；任一情况下都会抛出并把 `result` 置为 `null`。它会同时阻塞在队列与方法体上，且不得在同一条命令的方法体内调用。

###### `VeloxCommand.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃等待；不取消执行。可选。 |

**返回：** `Task<CommandCompletion>` —— **这一次**执行结束时完成，包括从未运行的调用。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `OperationCanceledException` | `cancellationToken` 先触发。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);
await command.LockAsync();

var completion = await command.ExecuteAndWaitAsync(null).WaitAsync(CommandTestKit.Timeout);

Assert.AreEqual(CommandOutcome.Refused, completion.Outcome);
```

**说明：** 结局由执行自身计算，而不是从事件回读。仍在排队的调用尚未结束，因此任务会等到槽位释放或队列清空。

###### `VeloxCommand.Notify`

**Signature:**
`void Notify()`

**返回：** `void` —— 触发 `CanExecuteChanged`。

**Example:**

```csharp
// Source: Demo — Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs
private void RefreshCollectionCommands()
{
    RemoveSelectedItemCommand.Notify();
    MoveLastToFirstCommand.Notify();
}
```

**说明：** 抛异常的 `CanExecuteChanged` 订阅者会被吞掉并通过 `HandlerException` 上报。
