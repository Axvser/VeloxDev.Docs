# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是每个命令生命周期事件携带的负载。`VeloxCommand` 是唯一的产出者；它被交给 `CommandEventHandler` 订阅者，并存放在命令内部的等待 / 活动队列中。

## Class: `CommandEventArgs`

**Signature**

```csharp
public sealed class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;

    // internal — not part of the public surface
    internal CancellationTokenSource? Cts { get; set; }
    internal CancellationTokenSource? TakeCts();
    internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }
    internal bool TryMarkCancelReported();
    internal void Complete(CommandOutcome outcome, Exception? exception);

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null);
}
```

**密封：** 是。

##### Properties

| 名称 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Parameter` | `object?` | get | 传给 `Execute` / `ExecuteAsync` 的实参。同一次执行的每个阶段都携带相同的值。 |
| `Exception` | `Exception?` | get | 结束该次执行的失败，仅 `Failed` 上有值；其它阶段（含 `Exited`）均为 `null`。 |
| `EventType` | `CommandEventType` | get | 本实例上报的阶段。 |
| `Cts` | `CancellationTokenSource?` | **internal** get / set | 该次执行的取消源；当命令的方法体永远拿不到 token 时为 `null`。刻意不公开：命令会在该次执行结束时释放它，暴露出去只会让人从处理器里读到一个正在失效的对象。 |

##### Methods

###### `CommandEventArgs.With`

**Signature:**
`CommandEventArgs With(CommandEventType newType, Exception? ex = null)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `newType` | `CommandEventType` | 要上报的阶段。 |
| `ex` | `Exception?` | 新实例应携带的失败。省略时改为保留接收者自身的失败。可选。 |

**Returns:** `CommandEventArgs` —— 新实例，保留 `Parameter` 与 `Cts`，并采用给定的异常或回退到接收者的异常。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs, lines 36-46
var boom = new InvalidOperationException("boom");
var other = new InvalidOperationException("other");
var args = new CommandEventArgs(null, CommandEventType.Failed, ex: boom);

Assert.AreSame(boom, args.With(CommandEventType.Exited).Exception,
    "With projects the whole instance, so an omitted failure falls back to the receiver's");
Assert.AreSame(other, args.With(CommandEventType.Exited, other).Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs, lines 14-25
using var cts = new CancellationTokenSource();
var args = new CommandEventArgs("payload", CommandEventType.Created, cts: cts);

var next = args.With(CommandEventType.Started);

Assert.AreEqual("payload", next.Parameter, "every stage of one execution carries the same argument");
Assert.AreSame(cts, next.Cts, "and the same cancellation source");
```

**Notes:**

- `With` 从不改写接收者；它投影出一个新实例。
- 命令本身从不触发那条异常回退：它总是从该次执行的起始实例投影，而那个实例创建时没有异常且全程不被改写，所以只有 `Failed` 这一个阶段会带着异常出来。
- `With` 产生的副本**不**携带 internal 的 `Completion` 槽 —— 副本不该能收尾等待中的调用方。

##### Internal 成员

这些成员声明在类型上，但消费方代码无法使用：

| 成员 | 签名 | 用途 |
|---|---|---|
| `Cts` | `internal CancellationTokenSource? Cts { get; set; }` | 该次执行的取消源。 |
| `TakeCts` | `internal CancellationTokenSource? TakeCts()` | `Interlocked.Exchange(ref _cts, null)` —— 恰好一个调用者胜出，由它负责释放。 |
| `Completion` | `internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }` | 等待槽；只有 `ExecuteAndWaitAsync` 会挂上它。 |
| `TryMarkCancelReported` | `internal bool TryMarkCancelReported()` | 首个调用者胜出，使一次执行至多上报一条 `Canceled`。 |
| `Complete` | `internal void Complete(CommandOutcome outcome, Exception? exception)` | 恰好收尾一次；无人等待时为空操作。 |

## Notes

- 同一次物理执行在其生命周期中由多个 `CommandEventArgs` 实例描述，从 `Created` 到 `Exited`，每个都由 `With` 产生。
- 由于 `Cts` 是 internal，需要取消某次运行的消费方必须经 `Interrupt` / `Clear`，而不能去取这个 token 源。
