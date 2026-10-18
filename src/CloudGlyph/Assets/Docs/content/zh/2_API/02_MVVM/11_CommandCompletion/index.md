# MVVM — `CommandCompletion`

`VeloxDev.MVVM.CommandCompletion`（`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`）是一次执行的结果，由 `ExecuteAndWaitAsync` 返回。

## Struct: `CommandCompletion`

**Signature**

```csharp
public readonly struct CommandCompletion(
    CommandOutcome outcome,
    Exception? exception = null,
    object? result = null)
{
    public CommandOutcome Outcome { get; } = outcome;
    public Exception? Exception { get; } = exception;
    public object? Result { get; } = result;

    public bool Succeeded => Outcome == CommandOutcome.Completed;

    public object? GetResultOrThrow();
    public TR GetResultOrThrow<TR>();
    public override string ToString() =>
        Exception is null ? Outcome.ToString() : $"{Outcome}: {Exception.Message}";
}
```

- **种类：** `readonly struct`（值类型，没有 `null` 状态）。
- **构造函数：** `(CommandOutcome outcome, Exception? exception = null, object? result = null)`。

与生命周期事件不同，它是**按调用**的：回答"**这一次**执行是怎么结束的"，包括从未运行的调用。

##### Properties

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `Outcome` | `CommandOutcome` | 执行如何结束。 |
| `Exception` | `Exception?` | 仅在 `CommandOutcome.Failed` 上携带失败；否则为 `null`。 |
| `Result` | `object?` | 方法体的值（装箱）—— 方法体无返回值或返回 `null` 时为 `null`。只有 `Completed` 携带值。 |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`。 |

##### Methods

###### `CommandCompletion.GetResultOrThrow`

**Signature:**
`object? GetResultOrThrow()`

**返回：** `Result`（装箱）；方法体无返回值时为 `null`。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `Exception` | 方法体抛出；原始实例经 `ExceptionDispatchInfo` 重新抛出，保留堆栈 |
| `OperationCanceledException` | 执行被取消 |
| `InvalidOperationException` | 命令已锁定，调用被拒绝 |

**说明：** 这是把完成结果变成值的地方。`ExecuteAndWaitAsync` 本身刻意只报告结局而不抛异常。

###### `CommandCompletion.GetResultOrThrow<TR>`

**Signature:**
`TR GetResultOrThrow<TR>()`

**返回：** `Result` 转换为 `TR`。

**异常：** 与非泛型重载相同的结局，外加 `Result` 不是 `TR` 时的 `InvalidCastException`。

###### `CommandCompletion.ToString`

**Signature:**
`override string ToString()`

**返回：** 结局名称；有失败时为 `"{Outcome}: {Exception.Message}"`。

**Example:**

```csharp
// Source: Inferred from the declaration
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.ToString());   // "Completed"，或例如 "Failed: boom"
```

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Completed, completion.Outcome);
Assert.IsTrue(completion.Succeeded);
Assert.IsNull(completion.Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs
var boom = new InvalidOperationException("boom");
var command = new VeloxCommand((_, _) => Task.FromException(boom));

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.AreSame(boom, completion.Exception);
Assert.IsFalse(completion.Succeeded);
```

## 说明

- 被取消的执行是**正常返回**，不是抛异常 —— `Outcome` 为 `CommandOutcome.Canceled`。只有调用方自己的 `CancellationToken` 会让等待抛异常。
- 它是结构体，自身不分配；这条路径上唯一的分配是等待调用创建的 `TaskCompletionSource`。
- `Outcome` 由执行自身计算，而不是从事件回读，因此 `Failed` 结果不依赖是否有人订阅 `Failed`。
