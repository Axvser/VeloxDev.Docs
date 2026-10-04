# MVVM — `IVeloxCommandStatus`

`VeloxDev.MVVM.IVeloxCommandStatus`（`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandStatus.cs`）是能够报告自己有多忙的命令。它由 `VeloxCommand` 实现，并经 `VeloxCommandExtensions` 从 `IVeloxCommand` 取到。

## Interface: `IVeloxCommandStatus`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandStatus
{
    bool IsBusy { get; }
    int ActiveCount { get; }
    int PendingCount { get; }
}
```

**为什么是独立接口：** `ICommand.CanExecute` 回答不了“这条命令忙不忙” —— 它只反映谓词与锁，从不反映队列。唯一槽位被占用的命令依然报告自己可执行，只绑定 `CanExecute` 的 UI 于是显示一个按下去毫无作用的按钮。把它做成独立接口而不是 `IVeloxCommand` 的成员，意味着新增它不会破坏任何既有实现者。

##### Properties

| 名称 | 类型 | 说明 |
|---|---|---|
| `IsBusy` | `bool` | 有执行正在运行**或**正在等待空闲槽位。 |
| `ActiveCount` | `int` | 此刻正在运行的执行数。 |
| `PendingCount` | `int` | 正在等待空闲槽位的调用数。 |

三者读取时都不获取命令内部的锁，因此并发更新可能让它们滞后一步。这是刻意的：它们是展示值，而属性 getter 不应阻塞。

## 用法

这些成员定义在本接口上，所以在 `IVeloxCommand` 上要经 `VeloxCommandExtensions.IsBusy` / `ActiveCount` / `PendingCount` 取到：

```csharp
// Source: Demo — the recorded run of the Quick Start complete-code program
Console.WriteLine($"status: IsBusy={vm.IncrementCommand.IsBusy()}, Active={vm.IncrementCommand.ActiveCount()}, Pending={vm.IncrementCommand.PendingCount()}");
// status: IsBusy=False, Active=0, Pending=0
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandStatusTests.cs, lines 61-76
_ = command.ExecuteAsync(null);
await gate.WaitForStartedAsync();

Assert.IsTrue(command.CanExecute(null),
    "CanExecute cannot see the queue, so it is the wrong thing to bind a button to");
Assert.IsTrue(command.IsBusy(), "IsBusy is the one that can");

gate.Release();
await CommandTestKit.WaitUntilAsync(() => !command.IsBusy());
```

**Example —— 把按钮绑定到队列而不是谓词：**

```csharp
// Source: Inferred from the interface documentation (Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandStatus.cs)
// A WPF/Avalonia view-model can expose the status of one command:
public bool CanStart
{
    get
    {
        StartCommand.CanExecuteChanged += (_, _) => OnPropertyChanged(nameof(CanStart));
        return StartCommand.CanExecute(null) && !StartCommand.IsBusy();
    }
}
```

**Notes:**

- `ActiveCount > 0` 或 `PendingCount > 0` 时 `IsBusy` 为 `true`。
- 未实现本接口的手写 `IVeloxCommand` 会让扩展抛 `NotSupportedException`（对 `null` 命令则抛 `ArgumentNullException`），而不是去猜一个答案。由 `VeloxCommand` 构建的所有命令都实现了它。
