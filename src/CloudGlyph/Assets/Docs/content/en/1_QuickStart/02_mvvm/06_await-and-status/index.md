# MVVM — Awaiting a Command and Reading its Status

`ExecuteAsync` returns as soon as the call is *accepted* — queued or started. That is the right contract for a fire-and-forget `ICommand`, but it leaves two questions unanswered: "how did **this** call end?" and "is this command busy right now?". The first is answered by `ExecuteAndWaitAsync` returning a `CommandCompletion`; the second by `IsBusy`, `ActiveCount` and `PendingCount`.

## 1. Awaiting one execution

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.MVVM;

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

`ExecuteAndWaitAsync` lives on `IVeloxCommandCompletion`; `VeloxCommandExtensions.ExecuteAndWaitAsync(this IVeloxCommand, ...)` is the bridge that reaches it from the interface type generated properties are declared with. `VeloxCommand` implements all three interfaces, so the extension always finds the capability on a generated command.

**Expected result:** the awaited value describes *this* execution. For a body that returns normally, `Outcome` is `CommandOutcome.Completed` and `Succeeded` is `true` (recorded run: `Increment -> Completed (Succeeded=True)`).

## 2. Every way an execution can end

| `CommandOutcome` | Meaning |
|---|---|
| `Completed` | the body ran to completion without throwing |
| `Failed` | the body threw — `Exception` carries it |
| `Canceled` | the run was cancelled (interrupt, clear, or the body honouring its token), **or** the call was still queued when the queue was cleared |
| `Refused` | the call never ran because the command was locked |

`Refused` is the one worth calling out: it has **no** `CommandEventType` counterpart. A refused execution raises `Canceled` through the events and never reaches `Exited`, so the event stream alone cannot tell a refusal apart from a cancellation. `ExecuteAndWaitAsync` is the only way to observe it.

Because a refused or cleared call never raises `Exited`, a hand-rolled wait built from `Exited` + `Failed` hangs on exactly those two cases — which is why this API exists.

**Expected result:** with the command locked, the awaited call returns `Refused` immediately (recorded run: `while locked -> Refused`) instead of never completing.

## 3. The wait's own cancellation token

The `CancellationToken` overload abandons **the wait only** — it does not cancel the execution:

```csharp
using var cts = new CancellationTokenSource();
var running = command.ExecuteAndWaitAsync(null, cts.Token);
cts.Cancel();                 // the await throws OperationCanceledException
await command.InterruptAsync(); // this is what actually stops the work
```

To stop work already under way, use `Interrupt` or `Clear` (previous page). Only the caller's own token makes the await throw; a cancelled *execution* is a normal return carrying `CommandOutcome.Canceled`.

**Expected result:** cancelling the wait throws `OperationCanceledException` while `ActiveCount` stays at its previous value — the execution is untouched.

## 4. Reading the status

`ICommand.CanExecute` reports the predicate and the lock, never the queue, so a command whose only slot is taken still reports itself as executable — a button bound to `CanExecute` alone looks enabled and does nothing when pressed. These members answer that:

| Member | Meaning |
|---|---|
| `IsBusy` | an execution is running **or** waiting for a free slot |
| `ActiveCount` | how many executions are running right now |
| `PendingCount` | how many calls are waiting for a free slot |

They live on `IVeloxCommandStatus`, reachable from `IVeloxCommand` through the same extension class:

```csharp
Console.WriteLine(command.IsBusy());       // bool
Console.WriteLine(command.ActiveCount());  // int
Console.WriteLine(command.PendingCount()); // int
```

They are read without taking the command's internal lock, so a concurrent update can leave them one step stale — deliberate, since a property getter must not block. Bind to `IsBusy`, not to `CanExecute`, when the point is to stop the user pressing a button whose work is already queued.

**Expected result:** an idle command reports `IsBusy=false, ActiveCount=0, PendingCount=0` (recorded run); a command whose slot is taken reports `IsBusy=true` while `CanExecute(null)` is still `true`.

## 5. Hand-written implementations must opt in

`IVeloxCommandCompletion` and `IVeloxCommandStatus` are separate interfaces precisely so that adding them breaks no existing implementer. A hand-written `IVeloxCommand` that does not implement them therefore has to say so: the extensions throw `NotSupportedException` with a message naming the missing interface, and `ArgumentNullException` for a `null` command. Every command built by `VeloxCommand` supports all of it.

**Expected result:** `somePlainCommand.IsBusy()`, `.ActiveCount()`, `.PendingCount()` and `.ExecuteAndWaitAsync(null)` all throw `NotSupportedException` for an implementation that only implements `IVeloxCommand`.

## Run declaration

- ✅ Actually built and run on 2026-10-01. A scratch console project referencing `VeloxDev.Core` (Debug project reference) plus the generator was executed with `dotnet run -c Debug`. Recorded output — the three lines that exercise this page:

  ```text
  Increment -> Completed (Succeeded=True)
  status: IsBusy=False, Active=0, Pending=0
  while locked -> Refused
  ```

  The program awaited two commands, printed the status triple, then locked the command with `await vm.IncrementCommand.LockAsync()` and awaited a third call, which reported `Refused`.

- The token semantics of section 3 and the `NotSupportedException` behaviour of section 5 were not executed in this pass; they are transcribed from `VeloxCommand.cs`, `VeloxCommandExtensions.cs` and pinned by `VeloxCommandCompletionTests` / `VeloxCommandStatusTests` under `Src/Core/VeloxDev.Core.Test/MVVM/`.
