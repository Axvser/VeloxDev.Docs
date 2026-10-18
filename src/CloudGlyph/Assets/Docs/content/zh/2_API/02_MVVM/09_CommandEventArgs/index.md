# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs`（`Src/Core/VeloxDev.Core/MVVM/CommandEventArgs.cs`）是每个非泛型命令生命周期事件携带的载荷。`CommandEventArgs<TParam, TResult>` 派生自它，并增加强类型实参与结果。

## Class: `CommandEventArgs`

**Signature**

```csharp
public class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public virtual object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;

    // internal —— 不属于公开面
    internal CancellationTokenSource? Cts { get; set; }
    internal CancellationTokenSource? TakeCts();
    internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }
    internal bool TryMarkCancelReported();
    internal void Complete(CommandOutcome outcome, Exception? exception, object? result = null);

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null);
}
```

**密封：** 否 —— `CommandEventArgs<TParam, TResult>` 派生自它。

##### Properties

| 名称 | 类型 | 访问 | 说明 |
| --- | --- | --- | --- |
| `Parameter` | `object?` | get（virtual） | 传给 `Execute` / `ExecuteAsync` 的实参。同一次执行的每个阶段携带相同的值。读取会让值类型装箱；强类型子类重写它。 |
| `Exception` | `Exception?` | get | 结束该执行的失败，仅在 `Failed` 上；其它阶段（包括 `Exited`）为 `null`。 |
| `EventType` | `CommandEventType` | get | 该实例报告的状态。 |
| `Cts` | `CancellationTokenSource?` | **internal** get / set | 该执行的取消源；方法体不接收 token 时为 `null`。不公开：命令在执行结束时释放它。 |

##### Methods

###### `CommandEventArgs.With`

**Signature:**
`CommandEventArgs With(CommandEventType newType, Exception? ex = null)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `newType` | `CommandEventType` | 要报告的状态。 |
| `ex` | `Exception?` | 新实例应携带的失败。省略时保留接收者自己的失败。 |

**返回：** `CommandEventArgs` —— 保留 `Parameter` 与 `Cts` 的新实例。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs
var boom = new InvalidOperationException("boom");
var other = new InvalidOperationException("other");
var args = new CommandEventArgs(null, CommandEventType.Failed, ex: boom);

Assert.AreSame(boom, args.With(CommandEventType.Exited).Exception);
Assert.AreSame(other, args.With(CommandEventType.Exited, other).Exception);
```

**说明：**

- `With` 不修改接收者，而是投影出新实例。
- 命令本身从不走异常回退：它从执行的原始实例投影，该实例创建时没有异常，因此只有 `Failed` 会带异常。
- `With` 产生的副本**不**携带内部 `Completion` 槽 —— 副本不能完成等待中的调用方。

##### 内部成员

| 成员 | 签名 | 用途 |
| --- | --- | --- |
| `Cts` | `internal CancellationTokenSource? Cts { get; set; }` | 该执行的取消源。 |
| `TakeCts` | `internal CancellationTokenSource? TakeCts()` | `Interlocked.Exchange(ref _cts, null)` —— 只有一个调用者胜出并负责释放。 |
| `Completion` | `internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }` | 等待槽；只有 `ExecuteAndWaitAsync` 会挂上它。 |
| `TryMarkCancelReported` | `internal bool TryMarkCancelReported()` | 先到者胜，使一次执行最多上报一条 `Canceled`。 |
| `Complete` | `internal void Complete(CommandOutcome outcome, Exception? exception, object? result = null)` | 恰好完成等待一次；无人等待时为空操作。 |

## 强类型子类

`CommandEventArgs<TParam, TResult>` 是 `sealed`。它增加：

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `TypedParameter` | `TParam` | 实参的自身类型；若 `object?` 入口携带了其它类型则抛 `InvalidCastException`。 |
| `TypedResult` | `TResult` | 执行结束后方法体返回的值。 |
| `Parameter` | `override object?` | 仅在真正读取时装箱。 |
| `With` | `new CommandEventArgs<TParam, TResult> With(...)` | 在强类型域内投影（旧目标框架不支持协变返回）。 |

见 `16_强类型命令`。

## 说明

- 同一次物理执行在整个生命周期中由多个 `CommandEventArgs` 实例描述，从 `Created` 到 `Exited`。
- 由于 `Cts` 是 internal，需要取消运行的消费方应使用 `Interrupt` / `Clear`。
