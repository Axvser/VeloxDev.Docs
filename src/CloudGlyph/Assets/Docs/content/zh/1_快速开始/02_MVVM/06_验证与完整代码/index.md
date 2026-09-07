# MVVM — 验证与完整代码

本页先说明该特性如何被验证（演示与自动化测试），再给出整个快速开始一直在构建的那个可运行单文件控制台程序。

## 1. 用演示验证

特性自带两个 GUI 演示，共享几乎一致的视图模型：

- `Examples/MVVM/WPF/Demo`（`net9.0-windows`）—— `MainWindowViewModel.cs`、`MainWindow.xaml`。
- `Examples/MVVM/Avalonia/Demo`（`net9.0`）—— `ViewModels/MainWindowViewModel.cs`、`Views/MainWindow.axaml`。

`MainWindowViewModel` 是 `partial` 类，只继承一个负责提供 `INotifyPropertyChanged` 基础、很小的 `ObservableViewModelBase`。它在一个界面里演示了前面各页覆盖的全部能力：`[VeloxProperty]` 标量与集合字段（`_index`、`_greeting`、`_items`、`_selectedItem`、...）、生成的 `partial void OnXxxChanged` 钩子、直接从 XAML 绑定的 `[VeloxCommand]` 按钮（`PlusCommand`、`MinusCommand`、集合命令）、`canValidate: true` 配合 `CanExecuteMinusCommand` / `CanExecuteRemoveSelectedItemCommand` / `CanExecuteMoveLastToFirstCommand`、逐项集合钩子（`OnItemAddedToItems`、`OnItemRemovedFromItems`、`OnItemMovedInItems`、`OnItemsResetInItems`）与 `OnCollectionChanged<T>` 重写、以及中断 API（`FreeCommand` vs `FreeCommandAsync`）。

在仓库里启动 `Examples/MVVM/WPF/Demo` 或 `Examples/MVVM/Avalonia/Demo` 即可运行。无需任何其它配置 —— 没有适配器、没有密钥、没有服务。

**预期结果：** 增加 / 减少按钮移动实时索引，索引为 0 时减少按钮禁用；集合按钮驱动文本状态，回显生成的钩子。

## 2. 用自动化测试验证

`Src/Core/VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs` 钉死**运行时** `VeloxCommand`（直接构造）：同步/异步完成、参数转发、`canExecute` 谓词、空命令校验与 `CreateTaskOnlyWithParameter` 工厂。**生成器**表面由演示源码佐证（前面各页转录了生成的命令/属性形态），而非专门的生成器测试。

**预期结果：** 在 `VeloxDev.Core.Test` 上 `dotnet test` 使 8 个 `VeloxCommandTests` 用例全部通过。

## 3. 完整代码

一个自包含的控制台程序，组合了 `[VeloxProperty]` 标量、`[VeloxProperty]` 集合、属性钩子、带验证与不带验证的命令、以及 `CanExecute` 生命周期行为。它针对 `VeloxDev.Core` 编译，所有 `using` 都显式写出；类无需基类 —— 生成器合成整套通知基础设施：

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

没有 `...` —— 每个标识符都在上文定义。命令同步完成（每个方法体都是 `Task.CompletedTask`），因此下面的记录是可确定的。静态推演的输出：

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

起点 `Count=0` 意味着首次 set/`Increment` 使 `Count > 0` 之前，`CanExecute(Decrement)` 是 `False` —— 这正是命令页所述的可执行性契约。

## 4. 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。本次文档编写未编译或执行该程序；记录是通过跟踪生成形态（来自生成器 writers）与 `VeloxCommand.ExecuteAsync`（来自 `VeloxDev.Core/MVVM/VeloxCommand.cs`）在“完全同步”条件下推演而来。留给读者的端到端检查是：以 Debug 项目引用 `VeloxDev.Core`，构建并运行它。
