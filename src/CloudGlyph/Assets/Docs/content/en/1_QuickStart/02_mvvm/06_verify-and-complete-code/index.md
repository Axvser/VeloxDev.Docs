# MVVM — Verify & Complete Code

This page shows how the feature is verified (demos and automated tests), then gives the single runnable console program the whole Quick Start has been building toward.

## 1. Verify with the demos

Two GUI demos ship with the feature, sharing an almost identical view-model:

- `Examples/MVVM/WPF/Demo` (`net9.0-windows`) — `MainWindowViewModel.cs`, `MainWindow.xaml`.
- `Examples/MVVM/Avalonia/Demo` (`net9.0`) — `ViewModels/MainWindowViewModel.cs`, `Views/MainWindow.axaml`.

`MainWindowViewModel` is a `partial` class deriving only from a tiny `ObservableViewModelBase` that supplies the `INotifyPropertyChanged` plumbing. It demonstrates every capability covered on the previous pages in one screen: `[VeloxProperty]` scalar and collection fields (`_index`, `_greeting`, `_items`, `_selectedItem`, ...), the generated `partial void OnXxxChanged` hooks, `[VeloxCommand]` buttons (`PlusCommand`, `MinusCommand`, collection commands) bound straight from XAML, `canValidate: true` with `CanExecuteMinusCommand` / `CanExecuteRemoveSelectedItemCommand` / `CanExecuteMoveLastToFirstCommand`, the per-item collection hooks (`OnItemAddedToItems`, `OnItemRemovedFromItems`, `OnItemMovedInItems`, `OnItemsResetInItems`) and the `OnCollectionChanged<T>` override, and the interrupt APIs (`FreeCommand` vs `FreeCommandAsync`).

To run one, open the repo and launch `Examples/MVVM/WPF/Demo` or `Examples/MVVM/Avalonia/Demo`. There is nothing else to configure — no adapter, no key, no service.

**Expected result:** the 增加 / 减少 buttons move a live index and enable/disable 减少 at index 0; the collection buttons drive the status texts that echo the generated hooks.

## 2. Verify with the automated tests

`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs` pins the **runtime** `VeloxCommand` (direct construction): sync/async completion, parameter forwarding, the `canExecute` predicate, null-command validation and the `CreateTaskOnlyWithParameter` factory. The **generator** surface is evidenced by the demos' source (the generated command/property shapes are transcribed on the earlier pages) rather than by a dedicated generator test.

**Expected result:** `dotnet test` on `VeloxDev.Core.Test` runs the eight `VeloxCommandTests` cases green.

## 3. Complete code

One self-contained console program that combines a `[VeloxProperty]` scalar, a `[VeloxProperty]` collection, property hooks, validated and non-validated commands, and the lifecycle `CanExecute` behavior. It compiles against `VeloxDev.Core` with all `using` directives explicit; the class needs no base class — the generator synthesizes the whole notification infrastructure:

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
    }

    public static class Program
    {
        public static void Main()
        {
            var vm = new CounterViewModel();

            Console.WriteLine($"initial: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");
            Console.WriteLine($"Items: {string.Join(", ", vm.Items)}");

            vm.Count = 3;
            Console.WriteLine($"after set: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");

            vm.IncrementCommand.Execute(null);
            vm.DecrementCommand.Execute(null);
            vm.DecrementCommand.Execute(null);

            Console.WriteLine($"final: Count={vm.Count}, CanExecute(Decrement)={vm.DecrementCommand.CanExecute(null)}");
            Console.WriteLine($"Items: {string.Join(", ", vm.Items)}");
            Console.WriteLine($"LastAction: {vm.LastAction}");
        }
    }
}
```

No `...` — every identifier is defined above. The commands complete synchronously (every body is `Task.CompletedTask`), so the transcript below is deterministic. Statically reasoned output:

```text
[collection] added: ready
initial: Count=0, CanExecute(Decrement)=False
Items: ready
[count] 0 -> 3
after set: Count=3, CanExecute(Decrement)=True
[count] 3 -> 4
[collection] added: increment -> 4
[count] 4 -> 3
[collection] added: decrement -> 3
[count] 3 -> 2
[collection] added: decrement -> 2
final: Count=2, CanExecute(Decrement)=True
Items: ready, increment -> 4, decrement -> 3, decrement -> 2
LastAction: added: decrement -> 2
```

The `Count=0` starting point means `CanExecute(Decrement)` is `False` until the first set/`Increment` makes `Count > 0` — exactly the executability contract of the commands page.

## 4. Run declaration

- ⚠️ Not actually run — statically verified only. The program was not compiled or executed in this documentation pass; the transcript is derived by tracing the generated shapes (from the generator writers) and `VeloxCommand.ExecuteAsync` (from `VeloxDev.Core/MVVM/VeloxCommand.cs`) under the fully-synchronous condition described above. Building and running it against a Debug project reference to `VeloxDev.Core` is left as the reader's end-to-end check.
