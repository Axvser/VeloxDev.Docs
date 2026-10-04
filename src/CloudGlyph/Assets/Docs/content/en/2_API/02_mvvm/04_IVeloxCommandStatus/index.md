# MVVM — `IVeloxCommandStatus`

`VeloxDev.MVVM.IVeloxCommandStatus` (`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommandStatus.cs`) is a command that can report how busy it is. It is implemented by `VeloxCommand`, and reached from an `IVeloxCommand` through `VeloxCommandExtensions`.

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

**Why it is a separate interface:** `ICommand.CanExecute` cannot answer "is this command busy" — it reflects the predicate and the lock, never the queue. A command whose only slot is taken still reports itself as executable, so a UI bound to `CanExecute` alone shows a button that does nothing when pressed. Making this a separate interface rather than a member of `IVeloxCommand` means adding it breaks no existing implementer.

##### Properties

| Name | Type | Description |
|---|---|---|
| `IsBusy` | `bool` | Whether an execution is running or waiting for a free slot. |
| `ActiveCount` | `int` | How many executions are running right now. |
| `PendingCount` | `int` | How many calls are waiting for a free slot. |

All three are read without taking the command's internal lock, so a concurrent update can make them one step stale. That is deliberate: they are display values, and a property getter must not block.

## Usage

The members live on this interface, so from an `IVeloxCommand` you reach them through `VeloxCommandExtensions.IsBusy` / `ActiveCount` / `PendingCount`:

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

**Example — binding a button to the queue, not the predicate:**

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

- `IsBusy` is `true` when either `ActiveCount > 0` or `PendingCount > 0`.
- A hand-written `IVeloxCommand` that does not implement this interface makes the extensions throw `NotSupportedException` (or `ArgumentNullException` for a `null` command) rather than guessing an answer. Every command built by `VeloxCommand` implements it.
