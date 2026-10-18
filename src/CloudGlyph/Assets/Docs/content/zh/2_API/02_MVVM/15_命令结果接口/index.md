# MVVM — 命令结果接口

`VeloxDev.MVVM.IVeloxCommandResult`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandResult.cs`）是能把方法体返回值交回调用方的命令。它由 `CommandPipeline<TParam, TResult>` 实现，因此 `VeloxCommand` 与强类型族都具备它。

## Interface: `IVeloxCommandResult`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandResult
{
    Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken);
    void Execute(object? parameter, out object? result);
}
```

它不声明事件，也不继承任何接口。它与 `IVeloxCommand` 分离，这样新增能力不会破坏手写实现者（旧目标框架没有默认接口成员）。

## 为什么存在

`IVeloxCommand.ExecuteAsync(object?)` 在调用被受理后立即返回，`IVeloxCommandCompletion.ExecuteAndWaitAsync` 只报告执行如何结束。两者都不暴露 `Task<T>` / `ValueTask<T>` 方法体的值。该接口就是这条通道。

值属于某一次执行，而不属于命令：两个重叠的调用各得各的。

##### Methods

###### `IVeloxCommandResult.ExecuteAsync`

**Signature:**
`Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃等待 —— 不取消执行。要停止正在进行的工作请用 `Interrupt` 或 `Clear`。 |

**返回：** `Task<object?>` —— 方法体的值（装箱）；方法体无返回值时为 `null`。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `Exception` | 方法体抛出；原始实例被重新抛出 |
| `OperationCanceledException` | 执行被取消 |
| `InvalidOperationException` | 命令被锁定，调用被拒绝 |

**说明：** `cancellationToken` 刻意没有默认值：默认值会让单实参调用与 `ExecuteAsync(object?)` 产生歧义。

###### `IVeloxCommandResult.Execute`

**Signature:**
`void Execute(object? parameter, out object? result)`

**返回：** `void`；`result` 接收方法体的值。

**异常：** 与 `ExecuteAsync` 相同的结局；任一情况下都会抛出并把 `result` 置为 `null`。

**说明：**

- 它同时阻塞在队列与方法体上：命令达到并发上限或被锁定时，调用线程会等待槽位。管线全程使用 `ConfigureAwait(false)`，因此不会在同步上下文上死锁，但会占用一个线程直到执行结束。
- 在同一条命令的方法体内调用会因命令自身的锁而死锁。除非调用方确实是同步的，否则优先使用可等待重载。

## Example

```csharp
// Source: 根据声明与结果通道生成路径推断
var command = VeloxCommand.CreateTaskWithResult(
    async (parameter, ct) =>
    {
        await Task.Delay(10, ct);
        return (object?)$"loaded:{parameter}";
    });

object? value = await command.ExecuteAsync("orders", CancellationToken.None);
command.Execute("orders", out object? again);
```

对于生成的命令，`IVeloxCommand<TParam, TResult>` 的强类型重载是免装箱的替代方案；见 `16_强类型命令`。
