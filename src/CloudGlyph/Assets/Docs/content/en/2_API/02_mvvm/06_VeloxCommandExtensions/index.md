# MVVM — `VeloxCommandExtensions`

`VeloxDev.MVVM.VeloxCommandExtensions` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandExtensions.cs`) is a `static` class that reaches the capabilities `VeloxCommand` has beyond `IVeloxCommand`, from the interface type that generated command properties are declared with.

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

**Why it exists:** the Command generator emits `public IVeloxCommand FooCommand`, so consumers hold the interface even though the instance behind it is always a `VeloxCommand`. These extensions are how those call sites reach the extra members without `IVeloxCommand` itself growing any — which would break every hand-written implementer.

##### Methods

###### `VeloxCommandExtensions.ExecuteAndWaitAsync`

**Signature:**
`Task<CommandCompletion> ExecuteAndWaitAsync(this IVeloxCommand command, object? parameter, CancellationToken cancellationToken = default)`

| Parameter | Type | Description |
|---|---|---|
| `command` | `IVeloxCommand` | The command to run. |
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons the wait only — it does not cancel the execution. Optional. |

**Returns:** `Task<CommandCompletion>` — how the execution ended.

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentNullException` | `command` is `null`. |
| `NotSupportedException` | `command` is a hand-written implementation that does not implement `IVeloxCommandCompletion`. |

**Example:**

```csharp
// Source: Demo — the recorded run of the Quick Start complete-code program
var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
Console.WriteLine($"while locked -> {refused.Outcome}");
// while locked -> Refused
```

**Notes:** a call that is still queued while the command stays locked has not ended, so the returned task does not complete until a slot frees or the queue is cleared.

###### `VeloxCommandExtensions.IsBusy`

**Signature:**
`bool IsBusy(this IVeloxCommand command)`

| Parameter | Type | Description |
|---|---|---|
| `command` | `IVeloxCommand` | The command to inspect. |

**Returns:** `bool` — whether an execution is running or waiting for a free slot.

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentNullException` | `command` is `null`. |
| `NotSupportedException` | `command` does not implement `IVeloxCommandStatus`. |

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

**Returns:** `int` — how many executions are running right now.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `NotSupportedException` when it does not implement `IVeloxCommandStatus`.

###### `VeloxCommandExtensions.PendingCount`

**Signature:**
`int PendingCount(this IVeloxCommand command)`

**Returns:** `int` — how many calls are waiting for a free slot.

**Exceptions:** `ArgumentNullException` when `command` is `null`; `NotSupportedException` when it does not implement `IVeloxCommandStatus`.

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

- The `NotSupportedException` message is produced by the private `Unsupported` helper: *"This command does not implement {interfaceName}. Every command built by VeloxCommand does; a hand-written IVeloxCommand implementation has to opt in."*
- Every command built by `VeloxCommand` implements both `IVeloxCommandCompletion` and `IVeloxCommandStatus`, so these extensions never throw for a generated command property.
