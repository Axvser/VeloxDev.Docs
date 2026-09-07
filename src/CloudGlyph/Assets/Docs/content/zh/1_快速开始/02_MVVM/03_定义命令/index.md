# MVVM — 定义命令

在方法上加 `[VeloxCommand]` 会生成一个懒加载的 `IVeloxCommand` 属性来包装该方法。命令实现了 `System.Windows.Input.ICommand`，因此在 XAML 里可以像框架命令一样直接绑定。

## 1. 特性参数

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`）：

| 参数 | 含义 |
|---|---|
| `name` | 命令属性后缀。`"Auto"`（默认）从方法名派生，并去掉末尾的 `Async`：`IncrementAsync` → `IncrementCommand`、`Plus` → `PlusCommand`。自定义字符串 `name` 原样使用（`name: "Add"` → `AddCommand`）。 |
| `canValidate` | 为 `true` 时要求提供 `Can<名称>Command` 谓词（见下）。 |
| `semaphore` | 最大并发执行数（≥ 1，默认 `1` = 串行）。大于 1 时允许多个实例并行。 |

## 2. 方法签名形态

以下任一形态都被接受（`VeloxCommandAttribute.cs` 的 XML 文档；生成器在编译期解析出对应的 `VeloxCommand` 构造函数/工厂）：

| 方法 | 解析出的命令委托 |
|---|---|
| `Task M(object? parameter, CancellationToken ct)` | 主构造函数 —— 每次运行带 `CancellationToken` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter(...)` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(...)` |
| `Task M()` | `Func<Task>` 构造函数 |
| `void M(object? parameter)` | `Action<object?>` 构造函数 |
| `void M()` | `Action` 构造函数 |

其中的对象参数就是命令参数（来自 `Execute(parameter)` 或绑定的 `CommandParameter`）；带 `CancellationToken` 的形态给方法体提供每次执行的令牌（见并发页）。

## 3. 最小命令

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxCommand]
    private Task Increment(object? parameter, CancellationToken ct)
    {
        Count++;
        return Task.CompletedTask;
    }
}
```

生成结果（按类生成在 `{类名}_{命名空间}_Commands.g.cs` 中）：

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_IncrementCommand = null;

public VeloxDev.MVVM.IVeloxCommand IncrementCommand
{
    get
    {
        _buffer_IncrementCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Increment,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_IncrementCommand;
    }
}
```

`IVeloxCommand` 属性在首次访问时创建并缓存在 `_buffer_IncrementCommand`。

**预期结果：** `vm.IncrementCommand` 非空且 `CanExecute(null)` 返回 `true`。XAML 里 `Command="{Binding IncrementCommand}"` 触发方法；代码里调 `vm.IncrementCommand.Execute(null)`（即发即忘）或 `await vm.IncrementCommand.ExecuteAsync(null)`。

## 4. 可执行性验证（`canValidate: true`）

开启验证后，生成器声明一个必须由你实现的谓词 partial：

```csharp
[VeloxCommand(canValidate: true)]
private Task Decrement(object? parameter, CancellationToken ct)
{
    Count--;
    return Task.CompletedTask;
}

private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
```

生成的 getter 于是传 `canExecute: CanExecuteDecrementCommand`。每次触发 `CanExecuteChanged` 都会重新查询该谓词 —— 影响它的状态变化之后调用 `某命令.Notify()`（或命令自身的刷新触发）。WPF 演示从属性钩子里这么做：`partial void OnIndexChanged(...) { MinusCommand.Notify(); }`。

**预期结果：** 当 `Count == 0` 时，`DecrementCommand.CanExecute(null)` 为 `false`，绑定的按钮被禁用；当 `Count > 0` 且执行 `DecrementCommand.Notify()` 后，`CanExecute(null)` 返回 `true`，按钮可用。

## 5. 命令与框架无关

命令运行时（`VeloxDev.MVVM.VeloxCommand`，各构造函数以及 `CreateTaskOnlyWithParameter` / `CreateTaskOnlyWithCancellationToken` 工厂）是普通类 —— 不引用任何 UI 类型。WPF 演示按钮（`Examples/MVVM/WPF/Demo/MainWindow.xaml`）与 Avalonia 演示直接通过 .NET `ICommand` 契约绑定 `PlusCommand` / `MinusCommand`。

**预期结果：** 同一个视图模型类在 WPF 与 Avalonia 里不加改动即可绑定；无头控制台宿主也能调用命令（完整代码页正是如此）。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。生成的命令属性形态转录自 `Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs`（`GenerateCommand`）；方法形态支持来自特性的 XML 文档与生成器的 `ParseConstructorType`；演示接线来自 `Examples/MVVM/*`。
