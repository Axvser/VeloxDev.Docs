# MVVM — `CommandOutcome`

`VeloxDev.MVVM.CommandOutcome` (`Src/Core/VeloxDev.Core/MVVM/CommandCompletion.cs`) says how a single execution ended. It is the type of `CommandCompletion.Outcome`.

## Enum: `CommandOutcome`

**Signature**

```csharp
public enum CommandOutcome
{
    /// <summary>The body ran to completion without throwing.</summary>
    Completed,

    /// <summary>The body threw.</summary>
    Failed,

    /// <summary>The execution was cancelled.</summary>
    Canceled,

    /// <summary>The call never ran because the command was locked.</summary>
    Refused,
}
```

##### Fields

| Name | Value | Description |
|---|---|---|
| `Completed` | `0` | The body ran to completion without throwing. |
| `Failed` | `1` | The body threw. `CommandCompletion.Exception` carries the failure. |
| `Canceled` | `2` | The execution was cancelled — by a lifecycle call such as `Interrupt` or `Clear`, by the body honouring its token, or because it was still queued when `Clear` emptied the queue. |
| `Refused` | `3` | The call never ran because the command was locked. |

**Notes on the values:** no explicit numeric values are assigned in the declaration, so the members take `0, 1, 2, 3` in declaration order. `Completed == default`, which means a default-initialized `CommandCompletion` reads as a success with `Exception == null`.

## Why `Canceled` covers two different situations

A call dropped from the queue by `Clear` is reported as `Canceled` rather than as a distinct outcome because, from the caller's side, it is the same answer: it will never run.

## Why `Refused` has no event counterpart

`Refused` deliberately has **no** matching `CommandEventType` member. A refused call raises `CommandEventType.Canceled` and never reaches `CommandEventType.Exited`, so `CommandEventType` alone cannot tell a refusal apart from a cancellation. `CommandOutcome.Refused` is therefore observable **only** through `ExecuteAndWaitAsync`.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 72-82
var command = new VeloxCommand(() => Task.CompletedTask);
await command.LockAsync();

var completion = await command.ExecuteAndWaitAsync(null).WaitAsync(CommandTestKit.Timeout);

Assert.AreEqual(CommandOutcome.Refused, completion.Outcome,
    "a refused call never raises Exited, so this is the only way to observe it");
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandCompletionTests.cs, lines 84-100
var queued = command.ExecuteAndWaitAsync(null);
await CommandTestKit.WaitUntilAsync(() => command.PendingCount() == 1);

await command.ClearAsync();

Assert.AreEqual(CommandOutcome.Canceled, (await queued.WaitAsync(CommandTestKit.Timeout)).Outcome,
    "a queued call dropped by Clear never raises Exited either");
```
