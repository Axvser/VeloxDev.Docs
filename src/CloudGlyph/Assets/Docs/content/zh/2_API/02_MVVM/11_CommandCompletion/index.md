# MVVM — `CommandCompletion`

`VeloxDev.MVVM.CommandCompletion`（`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`）是单次执行的结果，由 `ExecuteAndWaitAsync` 返回。

## Struct: `CommandCompletion`

**Signature**

```csharp
public readonly struct CommandCompletion(CommandOutcome outcome, Exception? exception = null)
{
    public CommandOutcome Outcome { get; } = outcome;
    public Exception? Exception { get; } = exception;

    public bool Succeeded => Outcome == CommandOutcome.Completed;

    public override string ToString() =>
        Exception is null ? Outcome.ToString() : $"{Outcome}: {Exception.Message}";
}
```

- **种类：** `readonly struct`（值类型，没有 `null` 状态）。
- **构造函数：** 公开的主构造函数 `(CommandOutcome outcome, Exception? exception = null)`。

与生命周期事件不同，它是**按调用**的：它回答“**这一次**执行如何结束”，包括那些根本没运行的调用。这正是它能作为 await 使用的原因。

##### Properties

| 名称 | 类型 | 说明 |
|---|---|---|
| `Outcome` | `CommandOutcome` | 执行如何结束。 |
| `Exception` | `Exception?` | 失败，仅在 `CommandOutcome.Failed` 上有值；否则为 `null`。 |
| `Succeeded` | `bool` | `Outcome == CommandOutcome.Completed`。 |

##### Methods

###### `CommandCompletion.ToString`

**Signature:**
`override string ToString()`

**Returns:** `string` —— 结局名，或存在失败时的 `"{Outcome}: {Exception.Message}"`。

**Example:**

```csharp
// Source: Inferred from the declaration (Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs, lines 57-58)
var completion = await command.ExecuteAndWaitAsync(null);
Console.WriteLine(completion.ToString());   // "Completed", or e.g. "Failed: boom"
```

**Notes:** 这让 `CommandCompletion` 可以安全地插值进日志行 —— 只有在存在异常时才追加异常消息。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 15-25
var command = new VeloxCommand(() => Task.CompletedTask);

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Completed, completion.Outcome);
Assert.IsTrue(completion.Succeeded);
Assert.IsNull(completion.Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 44-56
var boom = new InvalidOperationException("boom");
var command = new VeloxCommand((_, _) => Task.FromException(boom));

var completion = await command.ExecuteAndWaitAsync(null);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.AreSame(boom, completion.Exception);
Assert.IsFalse(completion.Succeeded);
```

## Notes

- 被取消的执行是**正常返回**，不是抛出的异常 —— `Outcome` 为 `CommandOutcome.Canceled`。只有调用方自己的 `CancellationToken` 会中止等待，而那确实会抛 `OperationCanceledException`。
- 该值本身是结构体，不额外产生分配；这条路径上唯一的分配是等待调用创建的 `TaskCompletionSource`。
- `Outcome` 由执行自身算出，而不是从事件读回来，因此 `Failed` 结果不依赖是否有人订阅了 `Failed`。
