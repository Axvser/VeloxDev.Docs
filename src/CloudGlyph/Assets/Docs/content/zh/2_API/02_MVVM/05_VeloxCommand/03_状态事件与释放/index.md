# MVVM — `VeloxCommand` 的状态、事件与拆除

##### Properties

| 名称 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `EventContext` | `SynchronizationContext?` | get / set | 生命周期事件投递到的上下文；`null`（默认）表示在管线所在线程上就地触发。 |
| `IsBusy` | `bool` | get | 有执行正在运行或正在等待空闲槽位。 |
| `ActiveCount` | `int` | get | 此刻正在运行的执行数。 |
| `PendingCount` | `int` | get | 正在等待空闲槽位的调用数。 |

三个状态属性对应 `IVeloxCommandStatus` 的成员；它们读取时都不获取命令内部的锁，因此并发更新可能让它们滞后一步 —— 这是刻意的，属性 getter 不应阻塞。

###### `VeloxCommand.EventContext`

**Signature:**
`SynchronizationContext? EventContext { get; set; }`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs, lines 62-63
var command = new VeloxCommand(() => Task.CompletedTask) { EventContext = context };
```

**Notes:**

- 把它设为 UI 框架的上下文，订阅者就不必再手工编组。默认关闭是因为“在管线线程上触发”才是命令一直以来的行为，而已经自行编组的订阅者否则要付出两遍代价。
- 经由上下文触发是异步的：事件按键序投递，但某个事件可能在那次触发调用返回之后才到达其处理器。当命令已经处于该上下文时，事件就地触发，不投递任何东西。
- 若处理器必须在事件触发的确切时刻观察命令，请保持它为 `null`。

##### Events

| 名称 | 类型 | 说明 |
|---|---|---|
| `Created` | `CommandEventHandler?` | 执行请求被受理。 |
| `Enqueued` | `CommandEventHandler?` | 容量已满，请求进入等待队列。 |
| `Dequeued` | `CommandEventHandler?` | 排队请求离开队列，即将运行。 |
| `Started` | `CommandEventHandler?` | 被包装的方法真正开始执行。 |
| `Completed` | `CommandEventHandler?` | 方法正常返回。 |
| `Failed` | `CommandEventHandler?` | 方法抛异常；`e.Exception` 携带它。 |
| `Canceled` | `CommandEventHandler?` | 执行被取消或被拒绝。每次执行至多一次。 |
| `Exited` | `CommandEventHandler?` | 执行结束并离开活动集合。 |
| `CanExecuteChanged` | `EventHandler?` | 标准的 `ICommand` 事件。 |
| `HandlerException` | `Action<Exception>?`（静态） | 命令某个事件（或 `CanExecuteChanged`）的订阅者抛了异常。 |

###### `VeloxCommand.HandlerException`（静态）

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

- 抛异常的订阅者绝不会干扰命令：生命周期无论如何都会继续，异常也不会被重新抛出。这是刻意的 —— 坏掉的 `Exited` 处理器不该把队列困死 —— 但这也意味着该失败本来会完全不可见。
- 没有订阅者时，命令的行为与这个事件不存在时完全一致；钩子自身抛异常也会被忽略，因此订阅它绝不会破坏向你汇报命令。
- 静态事件即进程级：所有命令共享它。请在成对的范围内订阅与退订，并留意并行测试。

###### `VeloxCommand.Dispose`

**Signature:**
`void Dispose()`

**Returns:** `void` —— 释放命令内部的 `SemaphoreSlim`。

**Example:**

```csharp
// Source: Inferred from the disposal contract (Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs, line 832)
using var command = new VeloxCommand(token => RunAsync(token));
```

**Notes:**

- 用于拆除，且只能在没有任何在途调用时 —— 在有调用排队或运行时释放，会让该调用下一次取锁抛异常。
- 仅仅被丢弃的命令无需拆除：这把锁不持有任何非托管资源。
- 释放是终态；被释放的命令不能再使用。

## 源码引用

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs` —— `HandlerException` 223、`CanExecuteChanged` 225、八个生命周期事件 228-242、`EventContext` 260、`IsBusy` 269、`ActiveCount` 276、`PendingCount` 283、`Dispose` 832。
