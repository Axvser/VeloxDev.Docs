# MVVM — `VeloxCommand` 构造

构造 `VeloxCommand` 的所有方式。选择只决定两件事：方法体是否接收每次执行的 `CancellationToken`，以及返回值是否被 `IVeloxCommandResult` 捕获。

不接收 token 的方法体被中断时仍会上报 `Canceled`，只是无法停止，会继续跑完。

###### `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

主构造函数。方法体同时接收实参与每次执行的 token。

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `command` | `Func<object?, CancellationToken, Task>` | 要调用的方法体。 |
| `canExecute` | `Predicate<object?>?` | 可执行性谓词；`null` 表示恒可执行。 |
| `semaphore` | `int` | 最大并发执行数，必须 ≥ 1。默认 `1`。 |

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentNullException` | `command` 为 `null`。 |
| `ArgumentOutOfRangeException` | `semaphore` 小于 1。 |

###### `VeloxCommand(Func<Task> command, …)` / `VeloxCommand(Action<object?> command, …)` / `VeloxCommand(Action command, …)`

不接收 token 的方法体。`canExecute` 与 `semaphore` 契约相同；容量小于 1 同样抛 `ArgumentOutOfRangeException`。`null` 方法体不会在构造时检查：传给基类的是非空包装 lambda，因此会在执行到达它时表现为 `NullReferenceException`。

###### `VeloxCommand.CreateTaskOnlyWithParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**返回：** 等待 `command(parameter)` 的命令；方法体永不接收 token。

**异常：** `semaphore < 1` 时抛 `ArgumentOutOfRangeException`。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
object? received = null;
var command = VeloxCommand.CreateTaskOnlyWithParameter(p =>
{
    received = p;
    return Task.CompletedTask;
});
var recorder = new CommandEventRecorder(command);

command.Execute("test");
await recorder.FirstExit;

Assert.AreEqual("test", received);
```

###### `VeloxCommand.CreateTaskOnlyWithCancellationToken`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**返回：** 等待 `command(ct)` 的命令；每次执行创建一个 token，因此方法体真正可取消。

###### `VeloxCommand.CreateTaskOnlyWithResult`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithResult(Func<object?, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**返回：** 方法体接收实参、返回值、且不接收 token 的命令。返回值由 `IVeloxCommandResult.ExecuteAsync(object?, CancellationToken)` 交回。

###### `VeloxCommand.CreateTaskWithResult`

**Signature:**
`static VeloxCommand CreateTaskWithResult(Func<object?, CancellationToken, Task<object?>> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**返回：** `CreateTaskOnlyWithResult` 的可取消版本。

###### `VeloxCommand.CreateTypedTaskOnlyWithParameter<T>`

**Signature:**
`static VeloxCommand<T, object?> CreateTypedTaskOnlyWithParameter<T>(Func<T, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)`

**返回：** 接收 `T`、无 token 的强类型命令。生成器为"单强类型形参 + 无返回值"使用它。

###### `VeloxCommand.CreateTypedWithParameter<T>`

**Signature:**
`static VeloxCommand<T, object?> CreateTypedWithParameter<T>(Func<T, CancellationToken, Task> command, Predicate<T>? canExecute = null, int semaphore = 1)`

**返回：** 接收 `T` 与执行 token 的强类型命令。

**异常：** `command` 为 `null` 时抛 `ArgumentNullException`（该工厂把方法体直接交给基类构造函数）。

###### `VeloxCommand.CreateTaskOnlyWithValueTaskParameter` / `CreateTaskOnlyWithValueTaskCancellationToken`

**Signatures:**
`static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, …)`
`static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, …)`

**返回：** `CreateTaskOnlyWithParameter` 与 `CreateTaskOnlyWithCancellationToken` 的 `ValueTask` 版本。

**说明：**

- **条件编译：** 只在 `#if !NETSTANDARD2_0 && !NETFRAMEWORK` 下存在。
- 它们是*命名*工厂而不是重载：把 `Func<object?, ValueTask>` 放在 `Func<object?, Task>` 旁边会让每个 `async` lambda 调用点产生歧义（`CS0121`）。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs
var gate = new CommandGate();
var command = VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken(
    ct => new ValueTask(gate.RunWithTokenAsync(ct)));
var recorder = new CommandEventRecorder(command);

_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();
await CommandTestKit.WaitUntilAsync(() => recorder.ExitCount >= 1);

Assert.HasCount(0, recorder.Of(CommandEventType.Failed));
```

## 生成的调用点

Command 生成器不使用 `ValueTask` 工厂：它发出 `.AsTask()` thunk，因此生成代码在所有目标框架上都能工作。强类型形参使用强类型工厂：

```csharp
// Source: generated — *_Commands.g.cs（形状由 CommandSignatureDiagnosticsTests 钉住）
_buffer_SaveCommand ??= global::VeloxDev.MVVM.VeloxCommand<string, global::System.Object?>
    .CreateTypedTaskOnlyWithParameter<global::System.String>(
        command: Save,
        canExecute: _ => true,
        semaphore: 1);
```

**说明：**

- 特性的 `semaphore` 经 `Math.Max(1, semaphore)` 传递，因此生成的命令永远不会走 `ArgumentOutOfRangeException` 路径。
- 无 token 的方法体不分配 `CancellationTokenSource`，因此内部 `Cts` 为 `null`，无需释放。
