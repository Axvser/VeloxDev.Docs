# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`）是 `IVeloxCommand` 上每个生命周期事件的委托类型。

## Delegate: `CommandEventHandler`

**Signature**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `e` | `CommandEventArgs` | 某次执行的某一个阶段。 |

**Returns:** `void`。

**Exceptions:** 未声明任何异常。处理器抛出的异常最多只会传到 `VeloxCommand` 的吞异常点，那里会经 `HandlerException` 上报并让生命周期继续。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandTestKit.cs, lines 65-83
internal CommandEventRecorder(IVeloxCommand command)
{
    command.Created += Record;
    command.Enqueued += Record;
    command.Dequeued += Record;
    command.Started += Record;
    command.Completed += Record;
    command.Failed += Record;
    command.Canceled += Record;
    command.Exited += e =>
    {
        Record(e);
        if (Interlocked.Increment(ref _exitCount) == 1)
        {
            _firstExit.TrySetResult(true);
        }
    };
}

private void Record(CommandEventArgs e) => _events.Enqueue(e);
```

## Notes

- 负载是单个 `CommandEventArgs`，而不是惯例的 `(object? sender, CommandEventArgs e)` 二元组 —— 因此处理器没有 `sender`，若需要命令本身请用闭包捕获。
- `IVeloxCommand` 为每个生命周期阶段声明一个此类型的事件：`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`。对订阅者而言，事件名才是阶段的标识；负载自身的 `EventType` 只是重复它。
- 抛异常的订阅者不会干扰命令：异常被捕获，若有订阅者则经静态 `VeloxCommand.HandlerException` 事件上报，然后被丢弃。这对 `CanExecuteChanged` 处理器同样成立。
- 由于该委托与特性声明在同一命名空间，一个 `using VeloxDev.MVVM;` 就足以用 lambda 写处理器：`cmd.Completed += e => { ... };`。
