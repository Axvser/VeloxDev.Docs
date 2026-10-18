# MVVM — `VeloxCommand` 状态、事件与释放

##### Properties

| 名称 | 类型 | 访问 | 说明 |
| --- | --- | --- | --- |
| `EventContext` | `SynchronizationContext?` | get / set | 生命周期事件的触发上下文；`null`（默认）表示管线所在线程。 |
| `IsBusy` | `bool` | get | 有执行正在运行或在等待空闲槽位。 |
| `ActiveCount` | `int` | get | 当前正在运行的执行数。 |
| `PendingCount` | `int` | get | 正在等待空闲槽位的调用数。 |

三个状态属性满足 `IVeloxCommandStatus`。读取时不取命令内部锁，因此并发更新可能让值落后一步 —— 这是刻意的，属性 getter 不应阻塞。

###### `VeloxCommand.EventContext`

**Signature:**
`SynchronizationContext? EventContext { get; set; }`

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandEventContextTests.cs
var command = new VeloxCommand(() => Task.CompletedTask) { EventContext = context };
```

**说明：**

- 设为 UI 框架的上下文，订阅者就不必手动编组。默认关闭，因为内联触发是历史行为，而且已经自行编组的订阅者会付两次代价。
- 通过上下文触发是异步的：事件按顺序投递，但可能在触发调用返回后才到达处理器。命令已经位于该上下文时，事件内联触发，不投递。
- 处理器必须在事件触发的那一刻观察命令时，保持 `null`。

##### Events

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `Created` | `CommandEventHandler?` | 执行请求被受理。 |
| `Enqueued` | `CommandEventHandler?` | 并发已满；请求加入待处理队列。 |
| `Dequeued` | `CommandEventHandler?` | 排队请求离开队列，即将运行。 |
| `Started` | `CommandEventHandler?` | 被包装的方法开始。 |
| `Completed` | `CommandEventHandler?` | 方法正常返回。 |
| `Failed` | `CommandEventHandler?` | 方法抛出异常；`e.Exception` 携带它。 |
| `Canceled` | `CommandEventHandler?` | 执行被取消或被拒绝。每次执行最多一次。 |
| `Exited` | `CommandEventHandler?` | 执行离开活动集合。 |
| `CanExecuteChanged` | `EventHandler?` | 标准 `ICommand` 事件。 |
| `HandlerException` | `Action<Exception>?`（静态） | 命令事件或 `CanExecuteChanged` 的某个订阅者抛出异常。 |

强类型事件（`CommandEventHandler<TParam, TResult>`）从 `IVeloxCommandEvents<TParam, TResult>` **显式**实现；通过该接口类型的引用来订阅，可获得未装箱的实参与结果。见 `16_强类型命令`。

###### `VeloxCommand.HandlerException`（静态）

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

**说明：**

- 抛异常的订阅者不会干扰命令：生命周期照常继续，异常不会重新抛出。没有这个钩子时失败将不可见。
- 无人订阅时命令的行为与没有该事件完全相同；钩子自身抛异常也会被忽略。
- 它是进程级的：底层存储是非泛型 `CommandDiagnostics` 类型，因此所有命令形态都向同一批订阅者上报。

###### `VeloxCommand.Dispose`

**Signature:**
`void Dispose()`

**返回：** `void` —— 释放命令内部 `SemaphoreSlim`。

**说明：**

- 仅用于拆除，且必须没有执行在途 —— 在调用排队或运行时释放会让该调用下一次取锁抛异常。
- 仅被丢弃的命令无需拆除：锁不持有非托管资源。
- 释放是最终操作。
