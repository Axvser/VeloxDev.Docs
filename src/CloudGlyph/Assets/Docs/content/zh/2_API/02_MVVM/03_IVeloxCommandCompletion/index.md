# MVVM — `IVeloxCommandCompletion`

`VeloxDev.MVVM.IVeloxCommandCompletion`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandCompletion.cs`）是能够报告某一次具体执行何时结束的命令。它由 `VeloxCommand` 实现，并经 `VeloxCommandExtensions` 从 `IVeloxCommand` 取到。

## Interface: `IVeloxCommandCompletion`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandCompletion
{
    Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default);
}
```

它只声明一个成员，且没有继承。

**为什么是独立接口：** `IVeloxCommand.ExecuteAsync` 在调用被受理（入队或开始）时就返回，这对即发即忘型调用方是正确的，但让需要真实结果的调用方只能手工把 `Exited` 与 `Failed` 配对。而对被拒绝或被丢弃的调用，这种配对永远不会完成，因为它们从不触发 `Exited`。把它做成独立接口而不是 `IVeloxCommand` 的成员，意味着新增它不会破坏任何既有实现者。

##### Methods

###### `IVeloxCommandCompletion.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | **只放弃等待** —— 不取消执行。要停止已在途的工作请用 `Interrupt` 或 `Clear`。可选。 |

**Returns:** `Task<CommandCompletion>` —— **这一次**执行如何结束。被取消的执行是正常返回，`Outcome == CommandOutcome.Canceled`。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `OperationCanceledException` | `cancellationToken` 先触发。 |

**Example:**

```csharp
// Source: Demo — the recorded run of the Quick Start complete-code program
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 102-119
var running = command.ExecuteAndWaitAsync(null, cts.Token);
await gate.WaitForStartedAsync();

cts.Cancel();

await Assert.ThrowsAsync<OperationCanceledException>(() => running);

// abandoning the wait is not cancelling the execution: the body is still running, the slot still taken
Assert.AreEqual(1, command.ActiveCount(), "cancelling the wait must not touch the execution");
```

**Notes:**

- 如果调用在命令保持锁定期间仍在排队，它就还没有结束，因此返回的任务要等到槽位释放或队列被清空才完成。若这种等待需要逃生通道，请传入 `cancellationToken`。
- 结果能区分四种结局，其中 `CommandOutcome.Refused` 是事件流无法表达的。详见 `10_CommandOutcome` 与 `11_CommandCompletion`。
- 在 `IVeloxCommand` 引用上请使用 `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, …)`；未实现本接口的手写实现会让该扩展抛 `NotSupportedException`。
