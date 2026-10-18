# MVVM — Verify and Complete Code

This page shows what verifies the feature, then gives the single runnable console program the Quick Start builds toward.

## 1. Verify with the demos

- `Examples/MVVM/WPF/Demo` (`net9.0-windows`, `UseWPF`) — `MainWindowViewModel.cs`, `MainWindow.xaml`.
- `Examples/MVVM/Avalonia/Demo` (`net9.0`, Avalonia `11.3.0`) — `ViewModels/MainWindowViewModel.cs`, `Views/MainWindow.axaml`.
- `Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs` — shared by both demos; contains one method per accepted `[VeloxCommand]` signature, including typed, multi-parameter, generic-method and `ValueTask` forms.

`MainWindowViewModel` derives from a small `ObservableViewModelBase` that supplies the notification plumbing. The screen exercises scalar and collection `[VeloxProperty]` members, property hooks, bound commands (`PlusCommand`, `MinusCommand`, `AddItemCommand`, `RemoveSelectedItemCommand`, `MoveLastToFirstCommand`, `ReplaceItemsCommand`, `ClearItemsCommand`), `canValidate: true`, the collection hooks, the `OnCollectionChanged<T>` override, and the interrupt APIs (`FreeCommand` vs `FreeCommandAsync`).

**Expected result:** both projects build. Launching one shows 增加 / 减少 moving a live index, with 减少 disabled at index 0, and the collection buttons updating the status texts that echo the generated hooks.

## 2. Verify with the automated tests

`Src/Core/VeloxDev.Core.Test/MVVM/` is the behavioural contract.

| Area | Files |
| --- | --- |
| Construction and plain execution | `VeloxCommandTests` |
| Stage order and payload | `VeloxCommandLifecycleTests`, `CommandEventArgsTests` |
| Queueing, capacity, capacity changes | `VeloxCommandConcurrencyTests` |
| Cancellation and the single-`Canceled` rule | `VeloxCommandCancellationTests` |
| Lock / interrupt / clear / continue | `VeloxCommandControlTests`, `VeloxCommandLockInvariantTests` |
| Awaitable result and status | `VeloxCommandCompletionTests`, `VeloxCommandStatusTests` |
| Per-execution source disposal | `VeloxCommandDisposalTests` |
| Broken subscribers and diagnostics | `VeloxCommandDiagnosticsTests` |
| `EventContext` posting | `VeloxCommandEventContextTests` |
| Every accepted signature, compiled and executed | `CommandSignatureTests`, `CommandSignatureViewModel` |
| Typed, multi-parameter and generic commands | `CommandMatrixTests`, `TypedCommandEventTests`, `CommandArityTests` |
| The rejection side (`VELOX_MVVM_CMD001`) | `CommandSignatureDiagnosticsTests` |
| Allocation behaviour | `CommandAllocationTests` |
| Collection subscription tracking | `ObservableCollectionTrackerTests` |

`CommandSignatureTests` compiles **and executes** one command per documented signature, so a shape whose generated code does not compile fails there rather than in a demo.

**Expected result:** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj` runs the MVVM folder green. This was **not** run in this documentation pass.

## 3. Complete code

```csharp
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.MVVM;

namespace QuickStart.Mvvm
{
    public partial class CounterViewModel
    {
        [VeloxProperty] private int _count;
        [VeloxProperty] private ObservableCollection<string> _items = [];
        [VeloxProperty] private string _lastAction = "(none)";

        public CounterViewModel()
        {
            Items.Add("ready");
        }

        partial void OnCountChanged(int oldValue, int newValue)
        {
            Console.WriteLine($"[count] {oldValue} -> {newValue}");
            DecrementCommand.Notify();
        }

        partial void OnItemAddedToItems(IEnumerable<string> items)
        {
            LastAction = "added: " + string.Join(", ", items);
            Console.WriteLine($"[collection] added: {string.Join(", ", items)}");
        }

        partial void OnItemRemovedFromItems(IEnumerable<string> items)
        {
            LastAction = "removed: " + string.Join(", ", items);
            Console.WriteLine($"[collection] removed: {string.Join(", ", items)}");
        }

        partial void OnItemsResetInItems()
        {
            LastAction = "reset";
            Console.WriteLine("[collection] reset");
        }

        [VeloxCommand]
        private Task Increment(object? parameter, CancellationToken ct)
        {
            Count++;
            Items.Add($"increment -> {Count}");
            return Task.CompletedTask;
        }

        [VeloxCommand(canValidate: true)]
        private Task Decrement(object? parameter, CancellationToken ct)
        {
            Count--;
            Items.Add($"decrement -> {Count}");
            return Task.CompletedTask;
        }

        private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;

        [VeloxCommand]
        private async ValueTask<int> SumToAsync(int limit)
        {
            await Task.Yield();
            var total = 0;
            for (var i = 1; i <= limit; i++)
            {
                total += i;
            }

            return total;
        }
    }

    public static class Program
    {
        public static async Task Main()
        {
            var vm = new CounterViewModel();

            Console.WriteLine($"initial: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");
            Console.WriteLine($"Items: {string.Join(", ", vm.Items)}");

            vm.Count = 3;
            Console.WriteLine($"after set: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");

            var increment = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
            Console.WriteLine($"Increment -> {increment.Outcome} (Succeeded={increment.Succeeded})");

            var decrement = await vm.DecrementCommand.ExecuteAndWaitAsync(null);
            Console.WriteLine($"Decrement -> {decrement.Outcome}");

            Console.WriteLine($"status: IsBusy={vm.IncrementCommand.IsBusy()}, Active={vm.IncrementCommand.ActiveCount()}, Pending={vm.IncrementCommand.PendingCount()}");

            var sum = await vm.SumToCommand.ExecuteAndWaitAsync(10);
            Console.WriteLine($"SumTo(10) -> {sum.Outcome}, value={sum.GetResultOrThrow<int>()}");

            await vm.IncrementCommand.LockAsync();
            var refused = await vm.IncrementCommand.ExecuteAndWaitAsync(null);
            Console.WriteLine($"while locked -> {refused.Outcome}");
            await vm.IncrementCommand.UnlockAsync();

            Console.WriteLine($"final: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");
            Console.WriteLine($"Items: {string.Join(", ", vm.Items)}");
            Console.WriteLine($"LastAction: {vm.LastAction}");
        }
    }
}
```

Every identifier is defined above. Two generated names are worth tracing: `DecrementCommand` comes from `Decrement`, and `SumToCommand` from `SumToAsync` — the auto-namer removes every `Async` substring. `SumToAsync(int)` is a typed command, so `SumToCommand` is `IVeloxCommand<int, int>` and `ExecuteAndWaitAsync(10)` fills the result channel.

## Run declaration

- ⚠️ Not actually run in this documentation pass — the program is statically verified against the generator rules and the public runtime signatures, but it was not compiled or executed here. The demo projects and `dotnet test` were not run either; every behavioural statement on these pages is sourced from the files cited and from the tests, not from a transcript produced for this revision.
