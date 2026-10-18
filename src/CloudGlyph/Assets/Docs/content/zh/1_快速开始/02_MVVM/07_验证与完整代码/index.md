# MVVM — 验证与完整代码

本页先说明如何验证该功能，再给出整套快速开始所构建的单个可运行控制台程序。

## 1. 用示例验证

- `Examples/MVVM/WPF/Demo`（`net9.0-windows`、`UseWPF`）—— `MainWindowViewModel.cs`、`MainWindow.xaml`。
- `Examples/MVVM/Avalonia/Demo`（`net9.0`、Avalonia `11.3.0`）—— `ViewModels/MainWindowViewModel.cs`、`Views/MainWindow.axaml`。
- `Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs` —— 两个示例共用；每种可接受的 `[VeloxCommand]` 签名各有一个方法，包括强类型、多形参、泛型方法与 `ValueTask` 形态。

`MainWindowViewModel` 派生自提供通知基础设施的小型 `ObservableViewModelBase`。界面覆盖标量与集合 `[VeloxProperty]` 成员、属性钩子、绑定命令（`PlusCommand`、`MinusCommand`、`AddItemCommand`、`RemoveSelectedItemCommand`、`MoveLastToFirstCommand`、`ReplaceItemsCommand`、`ClearItemsCommand`）、`canValidate: true`、集合钩子、`OnCollectionChanged<T>` 重写，以及中断 API（`FreeCommand` 与 `FreeCommandAsync`）。

**预期结果：** 两个项目都能构建。启动后 增加 / 减少 按钮推动一个实时索引，索引为 0 时 减少 禁用；集合按钮会更新回显生成钩子的状态文本。

## 2. 用自动化测试验证

`Src/Core/VeloxDev.Core.Test/MVVM/` 是行为契约。

| 领域 | 文件 |
| --- | --- |
| 构造与普通执行 | `VeloxCommandTests` |
| 阶段顺序与载荷 | `VeloxCommandLifecycleTests`、`CommandEventArgsTests` |
| 排队、容量、容量调整 | `VeloxCommandConcurrencyTests` |
| 取消与单条 `Canceled` 规则 | `VeloxCommandCancellationTests` |
| 锁定 / 中断 / 清空 / 继续 | `VeloxCommandControlTests`、`VeloxCommandLockInvariantTests` |
| 可等待结果与状态 | `VeloxCommandCompletionTests`、`VeloxCommandStatusTests` |
| 每次执行的源释放 | `VeloxCommandDisposalTests` |
| 故障订阅者与诊断 | `VeloxCommandDiagnosticsTests` |
| `EventContext` 投递 | `VeloxCommandEventContextTests` |
| 每种签名都编译并执行 | `CommandSignatureTests`、`CommandSignatureViewModel` |
| 强类型、多形参与泛型命令 | `CommandMatrixTests`、`TypedCommandEventTests`、`CommandArityTests` |
| 拒绝路径（`VELOX_MVVM_CMD001`） | `CommandSignatureDiagnosticsTests` |
| 分配行为 | `CommandAllocationTests` |
| 集合订阅追踪 | `ObservableCollectionTrackerTests` |

`CommandSignatureTests` 会**编译并执行**文档中每种签名对应的命令，因此生成代码编不过的形态会在这里失败，而不是拖到示例里。

**预期结果：** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj` 中 MVVM 目录全绿。本次文档修订**未运行**。

## 3. 完整代码

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

上面用到的每个标识符都在本页定义。两个生成名值得追踪：`DecrementCommand` 来自 `Decrement`，`SumToCommand` 来自 `SumToAsync` —— 自动命名会移除所有 `Async` 子串。`SumToAsync(int)` 是强类型命令，因此 `SumToCommand` 的类型是 `IVeloxCommand<int, int>`，`ExecuteAndWaitAsync(10)` 会填充结果通道。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 程序已对照生成器规则与运行时公开签名做静态核对，但未在此编译或执行。两个示例项目与 `dotnet test` 也未运行；本组页面中的所有行为结论都来自所引用的源码与测试，而不是本次修订产出的运行记录。
