# MVVM — Verify and Complete Code

This page shows how the feature is verified (demos and automated tests), then gives the single runnable console program the whole Quick Start builds toward.

## 1. Verify with the demos

Two GUI demos ship with the feature, sharing an almost identical view-model:

- `Examples/MVVM/WPF/Demo` (`net9.0-windows`, `UseWPF`) — `MainWindowViewModel.cs`, `MainWindow.xaml`.
- `Examples/MVVM/Avalonia/Demo` (`net9.0`, Avalonia `11.3.0`) — `ViewModels/MainWindowViewModel.cs`, `Views/MainWindow.axaml`.

`MainWindowViewModel` is a `partial` class deriving only from a small `ObservableViewModelBase` that supplies the `INotifyPropertyChanged` plumbing. One screen demonstrates every capability from the previous pages: `[VeloxProperty]` scalar and collection fields (`_index`, `_greeting`, `_items`, `_selectedItem`, ...), the generated `partial void OnXxxChanged` hooks, `[VeloxCommand]` buttons (`PlusCommand`, `MinusCommand`, `AddItemCommand`, `RemoveSelectedItemCommand`, `MoveLastToFirstCommand`, `ReplaceItemsCommand`, `ClearItemsCommand`) bound straight from XAML, `canValidate: true` with `CanExecuteMinusCommand` / `CanExecuteRemoveSelectedItemCommand` / `CanExecuteMoveLastToFirstCommand`, the per-item collection hooks and the `OnCollectionChanged<T>` override, and the interrupt APIs (`FreeCommand` vs `FreeCommandAsync`).

Neither demo needs configuration: no adapter, no key, no service.

**Expected result:** both projects build with zero warnings (recorded below), and launching one shows the 增加 / 减少 buttons moving a live index with 减少 disabled at index 0, while the collection buttons drive the status texts that echo the generated hooks.

## 2. Verify with the automated tests

`Src/Core/VeloxDev.Core.Test/MVVM/` is the behavioural contract — 20 files:

| Area | Files |
|---|---|
| Construction and the plain execution path | `VeloxCommandTests` |
| Lifecycle stage order and payload | `VeloxCommandLifecycleTests`, `CommandEventArgsTests` |
| Queueing, concurrency cap, capacity changes | `VeloxCommandConcurrencyTests` |
| Cancellation and the single-`Canceled` rule | `VeloxCommandCancellationTests` |
| Lock / interrupt / clear / continue | `VeloxCommandControlTests`, `VeloxCommandLockInvariantTests` |
| The awaitable result and the read model | `VeloxCommandCompletionTests`, `VeloxCommandStatusTests` |
| Per-execution source disposal | `VeloxCommandDisposalTests` |
| Broken subscribers and the diagnostics hook | `VeloxCommandDiagnosticsTests` |
| `EventContext` posting | `VeloxCommandEventContextTests` |
| Generator coverage of every accepted signature | `CommandSignatureTests`, `CommandSignatureViewModel`, `GenericOuterNestedCommandViewModel`, `GlobalNamespaceCommandViewModel` |
| The rejection side (`VELOXCMD001`) | `CommandSignatureDiagnosticsTests` |
| Allocation behaviour of unsubscribed stages | `CommandAllocationTests` |
| Collection subscription tracking | `ObservableCollectionTrackerTests` |

`CommandSignatureTests` is worth noting: it compiles *and executes* one command per documented signature inside the test assembly, so a shape that generates code which does not compile fails there rather than in a demo.

**Expected result:** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj` runs the MVVM folder green. This was **not** run in this documentation pass.

## 3. Complete code

A single console program combining a `[VeloxProperty]` scalar, a `[VeloxProperty]` collection, property hooks, a validated and a non-validated command, a `ValueTask<T>` command with a typed parameter, `ExecuteAndWaitAsync`, the status triple, and a refusal under lock. Every `using` is explicit and the class needs no base class — the generator synthesizes the notification infrastructure:

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
            Console.WriteLine($"SumTo(10) -> {sum.Outcome}");

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

There are no `...` omissions; every identifier is defined in the block above. Two generated names are worth tracing: `DecrementCommand` comes from the method name `Decrement`, and `SumToCommand` from `SumToAsync` — the auto-namer removes every `Async` substring, so the property is `SumToCommand`, not `SumToAsyncCommand`. The `ValueTask<int>` body with an `int` parameter is reached through the generated cast thunk, so `ExecuteAndWaitAsync(10)` passes `10` as `limit`.

## 4. Run declaration

- ✅ Actually built, actually run, on 2026-10-01. The program in section 3 was compiled and executed in a scratch console project (`net9.0`) that project-references `VeloxDev.Core.csproj` and `VeloxDev.Core.Generator.csproj` (the latter as an analyzer, Debug), with `dotnet run -c Debug`. Recorded output, verbatim:

  ```text
  [collection] added: ready
  initial: Count=0, CanExecute(Decrement)=False
  Items: ready
  [count] 0 -> 3
  after set: Count=3, CanExecute(Decrement)=True
  [count] 3 -> 4
  [collection] added: increment -> 4
  Increment -> Completed (Succeeded=True)
  [count] 4 -> 3
  [collection] added: decrement -> 3
  Decrement -> Completed
  status: IsBusy=False, Active=0, Pending=0
  SumTo(10) -> Completed
  while locked -> Refused
  final: Count=3, CanExecute(Decrement)=True
  Items: ready, increment -> 4, decrement -> 3
  LastAction: added: decrement -> 3
  ```

- The same scratch build also produced the generated files quoted on the earlier pages (`dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true`), and both demos were built with `dotnet build <proj> -c Debug` — each reported `0 个警告 0 个错误` (0 warnings, 0 errors).
- **Not verified in this pass:** `dotnet test` on `Src/Core/VeloxDev.Core.Test` (section 2), and the GUI demos were built but their windows were not launched. The `Replace` and `Reset` collection actions are covered by the generated switch rather than by an executed assertion here.
