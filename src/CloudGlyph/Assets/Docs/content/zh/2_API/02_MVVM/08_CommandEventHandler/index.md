# MVVM — `CommandEventHandler`

`VeloxDev.MVVM.CommandEventHandler`（`Src/Core/VeloxDev.Core/MVVM/CommandEventArgs.cs`）是 `IVeloxCommand` 上所有生命周期事件的委托类型。它的泛型孪生携带强类型载荷。

## Delegates

**Signatures**

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);

public delegate void CommandEventHandler<TParam, TResult>(CommandEventArgs<TParam, TResult> e);
```

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `e` | `CommandEventArgs` / `CommandEventArgs<TParam, TResult>` | 一次执行的一个阶段。 |

**返回：** `void`。

**异常：** 未声明。抛异常的处理器会被管线捕获，通过静态 `HandlerException` 事件上报，不会干扰命令。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandTestKit.cs
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

## 说明

- 载荷是单个 `CommandEventArgs`，而不是传统的 `(object? sender, EventArgs e)` 对；处理器没有 `sender`，需要命令本身时必须闭包捕获。
- `IVeloxCommand` 为每个生命周期阶段声明一个该类型的非泛型事件。
- `IVeloxCommandEvents<TParam, TResult>` 声明强类型对应物。由于一个类不能声明两个同名的公开事件，强类型事件是显式实现的；请通过 `IVeloxCommandEvents<TParam, TResult>` 类型的引用订阅。
- 抛异常的订阅者不会干扰命令。异常被捕获；若有人订阅 `VeloxCommand.HandlerException` 则上报，否则丢弃。`CanExecuteChanged` 处理器同理。
- 一个 `using VeloxDev.MVVM;` 就足以把处理器写成 lambda：`cmd.Completed += e => { ... };`。
