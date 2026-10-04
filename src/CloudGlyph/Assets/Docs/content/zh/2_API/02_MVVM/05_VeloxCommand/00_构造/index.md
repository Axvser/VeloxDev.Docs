# MVVM — `VeloxCommand` 的构造

构造 `VeloxCommand` 的全部方式。选哪一种只决定方法体是否拿到“每次执行的 `CancellationToken`” —— 其它一切（排队、生命周期事件、中断上报）完全相同。

拿不到 token 的方法体在被中断时仍会上报 `Canceled`，只是无法真正停止，于是会继续跑到返回。该区别由内部的 `_isCtsNeeded` 记录。

###### `VeloxCommand(Func<object?, CancellationToken, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

主构造函数。创建一个方法体同时接收参数与每次执行取消令牌的命令。

| 参数 | 类型 | 说明 |
|---|---|---|
| `command` | `Func<object?, CancellationToken, Task>` | 要调用的方法体。 |
| `canExecute` | `Predicate<object?>?` | 可执行性谓词；为 `null` 时命令始终可执行。可选。 |
| `semaphore` | `int` | 最大并发执行数。必须 ≥ 1。可选，默认 `1`。 |

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `command` 为 `null`。 |
| `ArgumentOutOfRangeException` | `semaphore` 小于 1。 |

###### `VeloxCommand(Func<Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

从无参方法体创建命令。方法体永远拿不到 token，因此被中断时会报 `Canceled` 而方法体并不会真正停止。

**Exceptions:** 同主构造函数。

###### `VeloxCommand(Action<object?> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

从接收参数的同步方法体创建命令。方法体永远拿不到 token。

**Exceptions:** 同主构造函数。

###### `VeloxCommand(Action command, Predicate<object?>? canExecute = null, int semaphore = 1)`

从无参同步方法体创建命令。

**Exceptions:** 同主构造函数。

###### `VeloxCommand.CreateTaskOnlyWithParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithParameter(Func<object?, Task> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `command` | `Func<object?, Task>` | 只接收参数的方法体。 |
| `canExecute` | `Predicate<object?>?` | 可执行性谓词。可选。 |
| `semaphore` | `int` | 并发容量，≥ 1。可选，默认 `1`。 |

**Returns:** `VeloxCommand` —— 一个 await `command(parameter)` 的命令；方法体永远拿不到 token。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；`semaphore < 1` 时抛 `ArgumentOutOfRangeException`。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 86-100
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

**Returns:** `VeloxCommand` —— 一个 await `command(ct)` 的命令；每次执行都会创建 token，因此方法体确实可被取消。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；`semaphore < 1` 时抛 `ArgumentOutOfRangeException`。

###### `VeloxCommand.CreateTaskOnlyWithValueTaskParameter`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithValueTaskParameter(Func<object?, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** `VeloxCommand` —— 与 `CreateTaskOnlyWithParameter` 相同，但面向返回 `ValueTask` 的方法体。方法体永远拿不到 token。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；`semaphore < 1` 时抛 `ArgumentOutOfRangeException`。

**Notes:**

- **条件编译：** 只在 `#if !NETSTANDARD2_0 && !NETFRAMEWORK` 下存在，因此在 `netstandard2.0` 与 `netframework4.6.1` 目标上不存在。
- 它是**具名**工厂而不是 `CreateTaskOnlyWithParameter` 的重载。若让 `Func<object?, ValueTask>` 与 `Func<object?, Task>` 并存，会让每个 `async` lambda 调用点产生歧义（`CS0121`），而 `async p => { … }` 正是调用方写命令的方式。

###### `VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken`

**Signature:**
`static VeloxCommand CreateTaskOnlyWithValueTaskCancellationToken(Func<CancellationToken, ValueTask> command, Predicate<object?>? canExecute = null, int semaphore = 1)`

**Returns:** `VeloxCommand` —— 与 `CreateTaskOnlyWithCancellationToken` 相同，但面向返回 `ValueTask` 的方法体。每次执行都会创建 token。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；`semaphore < 1` 时抛 `ArgumentOutOfRangeException`。

**Notes:** 与 `CreateTaskOnlyWithValueTaskParameter` 相同的 `#if !NETSTANDARD2_0 && !NETFRAMEWORK` 守卫。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs, lines 119-135
var gate = new CommandGate();
var command = VeloxCommand.CreateTaskOnlyWithValueTaskCancellationToken(
    ct => new ValueTask(gate.RunWithTokenAsync(ct)));
var recorder = new CommandEventRecorder(command);

_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

await command.InterruptAsync();
await CommandTestKit.WaitUntilAsync(() => recorder.ExitCount >= 1);

Assert.HasCount(0, recorder.Of(CommandEventType.Failed),
    "a ValueTask body that honours the token is cancelled, not failed");
```

## 生成的调用点

Command 生成器完全不用 `ValueTask` 那两个工厂 —— 它改为生成 `.AsTask()` 转换 thunk，这样生成的代码在所有目标框架上都可用：

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs
_buffer_SumToCommand ??= global::VeloxDev.MVVM.VeloxCommand.CreateTaskOnlyWithParameter(
    command: parameter => SumToAsync((int)parameter!).AsTask(),
    canExecute: _ => true,
    semaphore: 1);
```

**Notes:**

- 特性上的 `semaphore` 经 writer 的 `Math.Max(1, semaphore)` 传入，所以生成的命令绝不会走 `ArgumentOutOfRangeException` 分支；只有手写构造才可能。
- 由“拿不到 token 的方法体”构建的命令不会分发 `CancellationTokenSource`，因此对它而言 `CommandEventArgs.Cts`（internal）为 `null` —— 也就没有东西需要释放。
