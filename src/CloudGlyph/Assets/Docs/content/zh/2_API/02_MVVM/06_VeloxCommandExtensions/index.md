# MVVM — `VeloxCommandExtensions`

`VeloxDev.MVVM.VeloxCommandExtensions`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandExtensions.cs`）是一个 `static` 类，用来从“生成命令属性所声明的接口类型”上取到 `VeloxCommand` 超出 `IVeloxCommand` 的那些能力。

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

**为什么存在：** Command 生成器产出 `public IVeloxCommand FooCommand`，所以消费方持有的是接口，尽管其背后的实例永远是 `VeloxCommand`。这些扩展就是这些调用点取到额外成员的方式，而不必让 `IVeloxCommand` 自身增加成员 —— 那会破坏所有手写实现者。

##### Methods

###### `VeloxCommandExtensions.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `command` | `IVeloxCommand` | 要运行的命令。 |
| `parameter` | `object?` | 传给方法体的实参。 |
| `cancellationToken` | `CancellationToken` | 只放弃等待 —— 不取消执行。可选。 |

**Returns:** `Task<CommandCompletion>` —— 执行如何结束。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `command` 为 `null`。 |
| `NotSupportedException` | `command` 是未实现 `IVeloxCommandCompletion` 的手写实现。 |

**Example:**

```csharp
// Source: Demo — the recorded run of the Quick Start complete-code program
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

**Notes:** 命令保持锁定期间仍在排队的调用尚未结束，因此返回的任务要等到槽位释放或队列被清空才完成。

###### `VeloxCommandExtensions.IsBusy`

**Signature:**
`bool IsBusy(this IVeloxCommand command)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `command` | `IVeloxCommand` | 要检查的命令。 |

**Returns:** `bool` —— 有执行正在运行或正在等待空闲槽位。

**Exceptions:**

| 异常 | 条件 |
|---|---|
| `ArgumentNullException` | `command` 为 `null`。 |
| `NotSupportedException` | `command` 未实现 `IVeloxCommandStatus`。 |

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandStatusTests.cs, lines 20-23
var command = new VeloxCommand(() => Task.CompletedTask);

Assert.IsFalse(command.IsBusy());
Assert.AreEqual(0, command.ActiveCount());
Assert.AreEqual(0, command.PendingCount());
```

###### `VeloxCommandExtensions.ActiveCount`

**Signature:**
`int ActiveCount(this IVeloxCommand command)`

**Returns:** `int` —— 此刻正在运行的执行数。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；未实现 `IVeloxCommandStatus` 时抛 `NotSupportedException`。

###### `VeloxCommandExtensions.PendingCount`

**Signature:**
`int PendingCount(this IVeloxCommand command)`

**Returns:** `int` —— 正在等待空闲槽位的调用数。

**Exceptions:** `command` 为 `null` 时抛 `ArgumentNullException`；未实现 `IVeloxCommandStatus` 时抛 `NotSupportedException`。

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandStatusTests.cs, lines 79-87
// StubCommand implements only IVeloxCommand, so it is unaffected by this round of changes.
var plain = new StubCommand();

Assert.Throws<NotSupportedException>(() => plain.IsBusy());
Assert.Throws<NotSupportedException>(() => plain.ActiveCount());
Assert.Throws<NotSupportedException>(() => plain.ExecuteAndWaitAsync(null));
```

**Notes:**

- `NotSupportedException` 的消息由私有辅助方法 `Unsupported` 生成：*“This command does not implement {interfaceName}. Every command built by VeloxCommand does; a hand-written IVeloxCommand implementation has to opt in.”*
- 由 `VeloxCommand` 构建的所有命令都实现了 `IVeloxCommandCompletion` 与 `IVeloxCommandStatus`，因此对生成的命令属性而言这些扩展永远不会抛异常。
