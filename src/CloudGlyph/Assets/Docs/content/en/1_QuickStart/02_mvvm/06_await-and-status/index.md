# MVVM — Awaiting a Command and Reading its Status

`ExecuteAsync` returns as soon as the call is *accepted* — queued or started. Two other questions need their own APIs: "how did **this** call end?" (`ExecuteAndWaitAsync` → `CommandCompletion`) and "is this command busy right now?" (`IsBusy` / `ActiveCount` / `PendingCount`). A third, only for typed commands, is "what did the body return?" (`IVeloxCommandResult` and `IVeloxCommand<TParam, TResult>`).

## 1. Awaiting one execution

```csharp
static async Task RunAsync(IVeloxCommand command)
{
    CommandCompletion completion = await command.ExecuteAndWaitAsync(null);

    Console.WriteLine(completion.Outcome);   // Completed / Failed / Canceled / Refused
    Console.WriteLine(completion.Succeeded); // true only for Completed
    if (completion.Exception is not null)
    {
        Console.WriteLine(completion.Exception.Message);
    }
}
```

`ExecuteAndWaitAsync` is declared on `IVeloxCommandCompletion`; the extension `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, ...)` reaches it from the interface type that generated properties are declared with. Every command built by `VeloxCommand` implements it.

**Expected result:** the awaited value describes this execution. A body that returns normally produces `Outcome == Completed` and `Succeeded == true`.

## 2. Every way an execution can end

| `CommandOutcome` | Meaning |
| --- | --- |
| `Completed` | the body ran to completion without throwing |
| `Failed` | the body threw; `Exception` carries it |
| `Canceled` | the run was cancelled, or it was still queued when `Clear` emptied the queue |
| `Refused` | the call never ran because the command was locked |

`Refused` has **no** `CommandEventType` counterpart: a refused execution raises `Canceled` through the events and never reaches `Exited`, so the event stream alone cannot distinguish it from a cancellation.

Because a refused or cleared call never raises `Exited`, a hand-rolled wait built from `Exited` + `Failed` hangs on exactly those cases.

**Expected result:** with the command locked, the awaited call returns `Refused` immediately instead of never completing.

## 3. Getting the body's value

A body returning `Task<T>` or `ValueTask<T>` fills the result channel:

```csharp
CommandCompletion completion = await command.ExecuteAndWaitAsync(10);
int value = completion.GetResultOrThrow<int>();   // throws when the outcome is not Completed
```

`CommandCompletion.Result` is the boxed value (`null` when the body returned none). `GetResultOrThrow()` rethrows the original exception; `GetResultOrThrow<TR>()` also throws `InvalidCastException` when the value is not a `TR`.

A typed command exposes the value without boxing:

```csharp
IVeloxCommand<NotePayload, int> measure = vm.MeasureNoteCommand;
int weight = await measure.ExecuteAsync(note, CancellationToken.None);
measure.Execute(note, out int alsoWeight);        // synchronous twin
```

`IVeloxCommandResult.ExecuteAsync(object? parameter, CancellationToken cancellationToken)` is the untyped shape of the same operation.

**Expected result:** a successful `Task<int>` body yields its value; a failed one rethrows the original exception instance with its stack trace; a wrong `TR` throws `InvalidCastException`.

## 4. The wait's own cancellation token

The `CancellationToken` overload abandons **the wait only** — it does not cancel the execution:

```csharp
using var cts = new CancellationTokenSource();
var running = command.ExecuteAndWaitAsync(null, cts.Token);
cts.Cancel();                    // the await throws OperationCanceledException
await command.InterruptAsync();  // this is what actually stops the work
```

**Expected result:** cancelling the wait throws `OperationCanceledException` while `ActiveCount` stays unchanged.

## 5. Reading the status

`ICommand.CanExecute` reflects the predicate and the lock, never the queue. These members answer the queue question:

| Member | Meaning |
| --- | --- |
| `IsBusy` | an execution is running **or** waiting for a free slot |
| `ActiveCount` | how many executions are running |
| `PendingCount` | how many calls are waiting |

They live on `IVeloxCommandStatus`, reached from `IVeloxCommand` through `VeloxCommandExtensions`:

```csharp
Console.WriteLine(command.IsBusy());       // bool
Console.WriteLine(command.ActiveCount());  // int
Console.WriteLine(command.PendingCount()); // int
```

They are read without taking the internal lock, so a concurrent update can leave them one step stale — deliberate, because a getter must not block. Bind to `IsBusy`, not to `CanExecute`, when the point is to stop a user pressing a button whose work is already queued.

**Expected result:** an idle command reports `IsBusy=false, ActiveCount=0, PendingCount=0`; a command whose slot is taken reports `IsBusy=true` while `CanExecute(null)` is still `true`.

## 6. Hand-written implementations must opt in

`IVeloxCommandCompletion`, `IVeloxCommandResult`, `IVeloxCommandStatus` and `IVeloxCommandEvents<TParam, TResult>` are separate interfaces so that adding them broke no existing implementer. A hand-written `IVeloxCommand` that omits them makes the extensions throw `NotSupportedException` naming the missing interface; a `null` command throws `ArgumentNullException`.

**Expected result:** `plainCommand.IsBusy()`, `.ActiveCount()`, `.PendingCount()` and `.ExecuteAndWaitAsync(null)` all throw `NotSupportedException` for a class that only implements `IVeloxCommand`.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `Interfaces/MVVM/{IVeloxCommandCompletion,IVeloxCommandResult,IVeloxCommandStatus}.cs`, `MVVM/{CommandCompletion,VeloxCommandExtensions}.cs` and the tests under `Src/Core/VeloxDev.Core.Test/MVVM/` (`VeloxCommandCompletionTests`, `VeloxCommandStatusTests`, `CommandSignatureTests`).
