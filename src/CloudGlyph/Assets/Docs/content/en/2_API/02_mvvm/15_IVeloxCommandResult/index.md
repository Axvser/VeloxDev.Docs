# MVVM — `IVeloxCommandResult`

`VeloxDev.MVVM.IVeloxCommandResult` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandResult.cs`) is a command that can hand the value its body returned back to the caller. It is implemented by `CommandPipeline<TParam, TResult>` and therefore by `VeloxCommand` and the typed family.

## Interface: `IVeloxCommandResult`

**Signature**

```csharp
namespace VeloxDev.MVVM;

public interface IVeloxCommandResult
{
    Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken);
    void Execute(object? parameter, out object? result);
}
```

It declares no events and inherits nothing. It is separate from `IVeloxCommand` so that adding it broke no hand-written implementer (the older targets have no default interface members).

## Why it exists

`IVeloxCommand.ExecuteAsync(object?)` returns as soon as the call is accepted, and `IVeloxCommandCompletion.ExecuteAndWaitAsync` reports only how the execution ended. Neither exposes the value of a `Task<T>` / `ValueTask<T>` body. This interface is that channel.

The value belongs to one execution, never to the command: two overlapping calls get their own.

##### Methods

###### `IVeloxCommandResult.ExecuteAsync`

**Signature:**
`Task<object?> ExecuteAsync(object? parameter, CancellationToken cancellationToken)`

| Parameter | Type | Description |
| --- | --- | --- |
| `parameter` | `object?` | The argument to pass to the body. |
| `cancellationToken` | `CancellationToken` | Abandons the wait only — it does not cancel the execution. Use `Interrupt` or `Clear` to stop work under way. |

**Returns:** `Task<object?>` — the body's value, boxed, or `null` when it returned none.

**Exceptions:**

| Exception | Condition |
| --- | --- |
| `Exception` | the body threw; the original instance is rethrown |
| `OperationCanceledException` | the execution was cancelled |
| `InvalidOperationException` | the call was refused because the command was locked |

**Notes:** there is deliberately no default for `cancellationToken`: a default would make a one-argument call ambiguous with `ExecuteAsync(object?)`.

###### `IVeloxCommandResult.Execute`

**Signature:**
`void Execute(object? parameter, out object? result)`

**Returns:** `void`; `result` receives the body's value.

**Exceptions:** the same outcomes as `ExecuteAsync`; on any of them this throws and assigns `result = null`.

**Notes:**

- This blocks on the queue as well as on the body: if the command is at its cap or locked, the calling thread waits for a slot. The pipeline uses `ConfigureAwait(false)` throughout, so it will not deadlock on a synchronization context, but it does occupy a thread for the whole execution.
- Calling it from inside the body of the same command deadlocks on the command's own lock. Prefer the awaitable overload unless the caller is genuinely synchronous.

## Example

```csharp
// Source: Inferred from the declaration and the result-channel generator path
var command = VeloxCommand.CreateTaskWithResult(
    async (parameter, ct) =>
    {
        await Task.Delay(10, ct);
        return (object?)$"loaded:{parameter}";
    });

object? value = await command.ExecuteAsync("orders", CancellationToken.None);
command.Execute("orders", out object? again);
```

For a generated command, the typed overloads of `IVeloxCommand<TParam, TResult>` are the unboxed alternative; see `16_typed-commands`.
