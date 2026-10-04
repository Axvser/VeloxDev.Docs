# MVVM — 验证与完整代码

本页先说明该特性如何验证（演示与自动化测试），再给出整个快速开始逐步导向的那个可运行单文件控制台程序。

## 1. 用演示验证

该特性自带两个 GUI 演示，它们的视图模型几乎完全相同：

- `Examples/MVVM/WPF/Demo`（`net9.0-windows`，`UseWPF`）—— `MainWindowViewModel.cs`、`MainWindow.xaml`。
- `Examples/MVVM/Avalonia/Demo`（`net9.0`，Avalonia `11.3.0`）—— `ViewModels/MainWindowViewModel.cs`、`Views/MainWindow.axaml`。

`MainWindowViewModel` 是一个只继承小型 `ObservableViewModelBase`（提供 `INotifyPropertyChanged` 基础设施）的 `partial` 类。一个界面就演示了前面各页的全部能力：`[VeloxProperty]` 的标量字段与集合字段（`_index`、`_greeting`、`_items`、`_selectedItem` 等）、生成的 `partial void OnXxxChanged` 钩子、直接从 XAML 绑定的 `[VeloxCommand]` 按钮（`PlusCommand`、`MinusCommand`、`AddItemCommand`、`RemoveSelectedItemCommand`、`MoveLastToFirstCommand`、`ReplaceItemsCommand`、`ClearItemsCommand`）、带 `canValidate: true` 的 `CanExecuteMinusCommand` / `CanExecuteRemoveSelectedItemCommand` / `CanExecuteMoveLastToFirstCommand`、按条目的集合钩子与 `OnCollectionChanged<T>` 重写，以及中断 API（`FreeCommand` 与 `FreeCommandAsync`）。

两个演示都无需任何配置：没有适配器、没有密钥、没有服务。

**预期结果：** 两个项目零警告构建（录制见下）；启动任一个后，增加 / 减少 按钮驱动一个实时索引，索引为 0 时 减少 被禁用，而集合按钮驱动那些回显生成钩子的状态文本。

## 2. 用自动化测试验证

`Src/Core/VeloxDev.Core.Test/MVVM/` 就是行为契约 —— 共 20 个文件：

| 领域 | 文件 |
|---|---|
| 构造与普通执行路径 | `VeloxCommandTests` |
| 生命周期阶段顺序与负载 | `VeloxCommandLifecycleTests`、`CommandEventArgsTests` |
| 排队、并发容量、容量变更 | `VeloxCommandConcurrencyTests` |
| 取消与单条 `Canceled` 规则 | `VeloxCommandCancellationTests` |
| 加锁 / 中断 / 清空 / 继续 | `VeloxCommandControlTests`、`VeloxCommandLockInvariantTests` |
| 可等待结果与读模型 | `VeloxCommandCompletionTests`、`VeloxCommandStatusTests` |
| 每次执行 token 源的释放 | `VeloxCommandDisposalTests` |
| 抛异常的订阅者与诊断钩子 | `VeloxCommandDiagnosticsTests` |
| `EventContext` 投递 | `VeloxCommandEventContextTests` |
| 生成器对所有受支持签名的覆盖 | `CommandSignatureTests`、`CommandSignatureViewModel`、`GenericOuterNestedCommandViewModel`、`GlobalNamespaceCommandViewModel` |
| 拒绝侧（`VELOXCMD001`） | `CommandSignatureDiagnosticsTests` |
| 无订阅阶段的分配行为 | `CommandAllocationTests` |
| 集合订阅追踪 | `ObservableCollectionTrackerTests` |

`CommandSignatureTests` 值得一提：它在测试程序集内为每一种受文档支持的签名**编译并执行**一条命令，因此“生成了编译不过的代码”这种问题会在这里失败，而不是等到演示里才暴露。

**预期结果：** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj` 中 MVVM 目录全部通过。本次文档编写**未**运行它。

## 3. 完整代码

下面这一个控制台程序组合了 `[VeloxProperty]` 标量、`[VeloxProperty]` 集合、属性钩子、一条带校验与一条不带校验的命令、一条带强类型形参的 `ValueTask<T>` 命令，以及 `ExecuteAndWaitAsync`、状态三元组和锁定下的拒绝。所有 `using` 都显式写出，该类不需要基类 —— 通知基础设施由生成器合成：

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

上面没有 `...` 省略，每个标识符都在本段中定义过。有两个生成名值得追踪：`DecrementCommand` 来自方法名 `Decrement`；`SumToCommand` 来自 `SumToAsync` —— 自动命名会移除所有 `Async` 子串，所以属性是 `SumToCommand` 而不是 `SumToAsyncCommand`。带 `int` 形参的 `ValueTask<int>` 方法体经由生成的强转 thunk 抵达，因此 `ExecuteAndWaitAsync(10)` 会把 `10` 作为 `limit` 传入。

## 4. 运行声明

- ✅ 2026-10-01 实际构建、实际运行。第 3 节的程序在一个临时控制台项目（`net9.0`）中编译并执行：该项目项目引用 `VeloxDev.Core.csproj`，并以 analyzer 方式（Debug）引用 `VeloxDev.Core.Generator.csproj`，用 `dotnet run -c Debug` 运行。录制输出（逐字）：

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

- 同一次临时构建还用 `dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true` 产出了前面几页引用的生成文件；两个演示均以 `dotnet build <proj> -c Debug` 构建，分别报告 `0 个警告 0 个错误`。
- **本次未验证：** 对 `Src/Core/VeloxDev.Core.Test` 运行 `dotnet test`（第 2 节）；两个 GUI 演示只做了构建，窗口未启动。集合的 `Replace` 与 `Reset` 动作由生成的 switch 覆盖，本页没有对它们做实际断言。
