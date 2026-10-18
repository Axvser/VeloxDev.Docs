# MVVM — `VeloxCommandExtensions`

`VeloxDev.MVVM.VeloxCommandExtensions`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandExtensions.cs`）是一个 `static` 类，用于从生成命令属性所声明的接口类型到达 `IVeloxCommand` 之外的能力。

## Class: `VeloxCommandExtensions`

**Signature**

```csharp
public static class VeloxCommandExtensions
{
    public static Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default);
    public static bool IsBusy(this IVeloxCommand command);
    public static int ActiveCount(this IVeloxCommand command);
    public static int PendingCount(this IVeloxCommand command);
}
```

**为什么存在：** Command 生成器为未强类型命令发出 `public IVeloxCommand FooCommand`，因此消费方持有接口，尽管背后的实例总是 `VeloxCommand`。这些扩展方法让调用点到达额外成员，而不必让 `IVeloxCommand` 增长 —— 那会破坏所有手写实现者。

##### Methods

###### `VeloxCommandExtensions.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `command` | `IVeloxCommand` | 要运行的命令。 |
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃等待 —— 不取消执行。可选。 |

**返回：** `Task<CommandCompletion>` —— 执行如何结束。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentNullException` | `command` 为 `null`。 |
| `NotSupportedException` | `command` 是未实现 `IVeloxCommandCompletion` 的手写实现。 |

**Example:**

```csharp
// Source: Quick Start 完整代码程序（静态核对）
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

**说明：** 命令保持锁定期间仍在排队的调用尚未结束，因此返回的任务要等到槽位释放或队列清空才完成。

###### `VeloxCommandExtensions.IsBusy`

**Signature:**
`bool IsBusy(this IVeloxCommand command)`

**返回：** `bool` —— 是否有执行正在运行或在等待空闲槽位。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentNullException` | `command` 为 `null`。 |
| `NotSupportedException` | `command` 未实现 `IVeloxCommandStatus`。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandStatusTests.cs
var command = new VeloxCommand(() => Task.CompletedTask);

Assert.IsFalse(command.IsBusy());
Assert.AreEqual(0, command.ActiveCount());
Assert.AreEqual(0, command.PendingCount());
```

###### `VeloxCommandExtensions.ActiveCount`

**Signature:**
`int ActiveCount(this IVeloxCommand command)`

**返回：** `int` —— 当前正在运行的执行数。

**异常：** `command` 为 `null` 时 `ArgumentNullException`；未实现 `IVeloxCommandStatus` 时 `NotSupportedException`。

###### `VeloxCommandExtensions.PendingCount`

**Signature:**
`int PendingCount(this IVeloxCommand command)`

**返回：** `int` —— 正在等待空闲槽位的调用数。

**异常：** `command` 为 `null` 时 `ArgumentNullException`；未实现 `IVeloxCommandStatus` 时 `NotSupportedException`。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandStatusTests.cs
var plain = new StubCommand();

Assert.Throws<NotSupportedException>(() => plain.IsBusy());
Assert.Throws<NotSupportedException>(() => plain.ActiveCount());
Assert.Throws<NotSupportedException>(() => plain.ExecuteAndWaitAsync(null));
```

**说明：**

- `NotSupportedException` 消息由私有 `Unsupported` 辅助方法生成：*"This command does not implement {interfaceName}. Every command built by VeloxCommand does; a hand-written IVeloxCommand implementation has to opt in."*
- `CommandPipeline<TParam, TResult>` 构造的每条命令都实现 `IVeloxCommandCompletion`、`IVeloxCommandResult` 与 `IVeloxCommandStatus`，因此生成的命令不会让这些扩展方法抛出。
