# MVVM — 快速开始

## MVVM

VeloxDev MVVM 是一层基于源生成器的 MVVM 抽象，在编译期把普通的 `partial` 类变成完整的 MVVM 视图模型。`[VeloxProperty]` 会把私有字段（或 `partial` 属性）展开为公开可观察属性，触发 `INotifyPropertyChanging` / `INotifyPropertyChanged`，并提供 `partial void` 钩子；`[VeloxCommand]` 会把 `Task`/`void` 方法展开为懒加载的 `IVeloxCommand` 属性，带异步执行队列、取消能力与完整生命周期事件流。

### 快速开始

#### 1. 前置条件

- **支持目标**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` —— 可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK 以运行 MVVM/命令源码生成器；示例面向 `net9.0` —— *被验证过*的配置。
- **包管理器：** NuGet / `dotnet` CLI。
- **所需服务：** 无 —— 运行时与生成器可工作在控制台应用或任意 GUI（WPF / Avalonia / WinUI / MAUI / WinForms / Blazor）。


#### 2. 安装 / 添加依赖

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core`（当前为 `7.0.0`）以普通包引用方式引用了 `VeloxDev.Core.Generator`（`7.0.0`）（`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`，第 26-29 行），因此 Roslyn 生成器随包传递引用 — 无需手动接线分析器。

**预期结果：** `VeloxDev.Core.Generator` 出现在项目的分析器列表中；`dotnet build` 成功。

#### 3. 基本设置 / 注册

声明一个 `partial class` — 任意名称、任意命名空间 — 用 `[VeloxProperty]` 标记字段或 `partial` 属性，用 `[VeloxCommand]` 标记方法。无需基类；当不存在通知基础设施时，生成器会自行合成（`PropertyChanging` / `PropertyChanged` 事件与 `OnPropertyChanging` / `OnPropertyChanged` 方法），或者复用一个已提供这些基础设施的基类。

**预期结果：** 生成的 `.g.cs` 文件出现在 `obj/<配置>/<目标框架>/generated/` 下（例如 `CounterViewModel_ConsoleApp_MVVM.g.cs` 与 `CounterViewModel_ConsoleApp_Commands.g.cs`）；带注解的成员编译为公开的 `Count` 属性以及公开的 `IncrementCommand` / `DecrementCommand` 属性。

#### 4. 核心用法（逐步）

1) 声明可观察属性。partial 属性写法为 `[VeloxProperty] public partial int Count { get; set; }`；私有字段写法为 `[VeloxProperty] private int _count = 0;`。生成器会生成该属性以及 `partial void OnCountChanged(int oldValue, int newValue)`（生成器文档里缩写的 `partial void OnCountChanged(int value)` 就是同一个钩子 — 真实签名同时接收旧值和新值）。
   **预期结果：** `Count = 5` 会依次触发 `PropertyChanging` → 调用 `OnCountChanged` → 触发 `PropertyChanged`；订阅者按该顺序收到两个通知。

2) 声明命令。用 `[VeloxCommand]` 标记方法。返回 `Task` 的两参数形式 `Task Plus(object? sender, CancellationToken ct)` 映射到 `VeloxCommand` 主构造函数（`Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs`，`ParseConstructorType`，第 78-116 行）；生成的命令属性以方法名命名（`Plus` → `PlusCommand`）。
   **预期结果：** 存在公开的 `IVeloxCommand PlusCommand` 属性；调用 `PlusCommand.Execute(null)` 会异步执行该方法。

3) 用 `canValidate: true` 开启可执行性验证。生成器会生成 `private partial bool CanExecuteMinusCommand(object? parameter);`，由你实现（示例：`_index > 0`）。
   **预期结果：** 当谓词返回 `false` 时，`CanExecute(null)` 返回 `false`，绑定的按钮被禁用；在相关变化后调用 `MinusCommand.Notify()` 会重新查询谓词。

4) 通过生成的命令属性执行或绑定。XAML：`Command="{Binding PlusCommand}"`；代码：`vm.PlusCommand.Execute(null)` 或 `await vm.PlusCommand.ExecuteAsync(null)`。
   **预期结果：** 绑定的按钮或代码路径触发命令方法；在 `semaphore: 1` 下，第一个还在运行时再触发一次会被排队而不会丢失。

5) 观察生命周期事件。`IVeloxCommand` 暴露 `Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`，以及 `CanExecuteChanged`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`，第 92-101 行）。
   **预期结果：** 订阅 `cmd.Started += e => ...` 与 `cmd.Completed += e => ...` 会按顺序打印事件：方法体运行前触发 `Started`，方法返回后触发 `Completed`。

#### 5. 验证

运行 MVVM 示例（`Examples/MVVM/WPF/Demo` 或 `Examples/MVVM/Avalonia/Demo`）或下面的控制台示例。每次 set 都会触发属性通知；命令按文档顺序入队 / 执行并触发事件；当 `_index == 0` 时 减少（Minus）按钮被禁用，因为 `CanExecuteMinusCommand` 返回 `false`。示例还演示了集合钩子：`OnItemAddedToItems`、`OnItemRemovedFromItems`、`OnItemMovedInItems`、`OnItemsResetInItems` 以及 `OnCollectionChanged<T>`。

#### 6. 完整代码

一个独立使用两个生成器的控制台程序。它针对 `VeloxDev.Core` 编译，并显式列出所有 `using`（不依赖隐式 using）：

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.MVVM;

public partial class CounterViewModel
{
    [VeloxProperty] public partial int Count { get; set; }

    partial void OnCountChanged(int oldValue, int newValue)
    {
        Console.WriteLine($"[hook] Count {oldValue} -> {newValue}");
    }

    [VeloxCommand]
    private Task IncrementAsync(object? parameter, CancellationToken ct)
    {
        Count++;
        return Task.CompletedTask;
    }

    [VeloxCommand(canValidate: true)]
    private Task DecrementAsync(object? parameter, CancellationToken ct)
    {
        Count--;
        return Task.CompletedTask;
    }

    private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
}

public static class Program
{
    public static async Task Main()
    {
        var vm = new CounterViewModel();

        vm.IncrementCommand.Started += e =>
            Console.WriteLine($"[event] Started ({e.EventType})");
        vm.IncrementCommand.Completed += e =>
            Console.WriteLine($"[event] Completed ({e.EventType})");
        vm.IncrementCommand.Failed += e =>
            Console.WriteLine($"[event] Failed ({e.EventType}, {e.Exception?.Message})");

        vm.Count = 5;

        vm.IncrementCommand.Execute(null);
        vm.DecrementCommand.Execute(null);

        await Task.Delay(300);

        Console.WriteLine($"Final Count = {vm.Count}");
        Console.WriteLine($"Decrement enabled = {vm.DecrementCommand.CanExecute(null)}");
    }
}
```

静态推演的输出（两个命令都是 `Task.CompletedTask`，因此立即完成）：

```text
[hook] Count 0 -> 5
[event] Started (Started)
[event] Completed (Completed)
[event] Started (Started)
[event] Completed (Completed)
Final Count = 5
Decrement enabled = True
```

#### 7. 运行声明

- ⚠️ 未实际运行 — 仅静态验证。上述生成器输出、事件顺序与命令语义依据源码（`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`、`Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs`）以及仓库内已检入的示例/测试推得；本次会话并未编译并运行控制台项目来产生真实输出。
