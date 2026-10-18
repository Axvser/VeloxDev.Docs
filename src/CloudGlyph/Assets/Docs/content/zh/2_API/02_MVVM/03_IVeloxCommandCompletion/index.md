# MVVM — `IVeloxCommandCompletion`

`VeloxDev.MVVM.IVeloxCommandCompletion`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandCompletion.cs`）是能报告某一次执行何时结束的命令。它由 `VeloxCommand`（经 `CommandPipeline<TParam, TResult>`）实现，并从 `IVeloxCommand` 通过 `VeloxCommandExtensions` 到达。

## Interface: `IVeloxCommandCompletion`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandCompletion
{
    Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default);
}
```

它只声明一个成员，不继承任何接口。

**为什么独立：** `IVeloxCommand.ExecuteAsync` 在调用被受理后立即返回，需要真实结果的调用方只能手动配对 `Exited` 与 `Failed`。而被拒绝或被丢弃的调用永远不会触发 `Exited`，这种配对永远无法完成。独立接口意味着新增能力不会破坏已有实现者。

##### Methods

###### `IVeloxCommandCompletion.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃**等待** —— 不取消执行。要停止已经在进行的工作请用 `Interrupt` 或 `Clear`。可选。 |

**返回：** `Task<CommandCompletion>` —— **这一次**执行如何结束。被取消的执行是正常返回，`Outcome == CommandOutcome.Canceled`。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `OperationCanceledException` | `cancellationToken` 先触发。 |

**Example:**

```csharp
// Source: Demo/test usage — recorded semantics in Quick Start
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var running = command.ExecuteAndWaitAsync(null, cts.Token);
await gate.WaitForStartedAsync();

cts.Cancel();

await Assert.ThrowsAsync<OperationCanceledException>(() => running);

Assert.AreEqual(1, command.ActiveCount(), "cancelling the wait must not touch the execution");
```

**说明：**

- 命令保持锁定期间仍在排队的调用尚未结束，因此返回的任务要等到有槽位释放或队列被清空才完成。
- `CommandCompletion` 报告四种结局，包括 `Refused`，并在 `Result` 中携带方法体的值。未强类型的结果 API 见 `15_命令结果接口`；强类型见 `16_强类型命令`。
- 在 `IVeloxCommand` 引用上使用 `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, …)`；手写实现若缺少该接口，扩展方法会抛 `NotSupportedException`。
