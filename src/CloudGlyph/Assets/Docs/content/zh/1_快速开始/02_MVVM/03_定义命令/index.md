# MVVM — 定义命令

在方法上加 `[VeloxCommand]`，会生成一个懒加载的 `IVeloxCommand` 属性来包装该方法。该命令实现 `System.Windows.Input.ICommand`，因此在 XAML 里的绑定方式与框架自带命令完全一样。

## 1. 特性参数

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]` —— 完整签名见 `Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`：

| 参数 | 含义 |
|---|---|
| `name` | 命令属性名。`"Auto"`（默认）由方法名派生，**移除所有** `Async` 子串：`Plus` → `PlusCommand`，`IncrementAsync` → `IncrementCommand`，`SumToAsync` → `SumToCommand`。传入自定义字符串则原样使用（`name: "Add"` → `AddCommand`）。 |
| `canValidate` | 为 `true` 时属性以 `canExecute: CanExecute{名称}Command` 构造，生成器同时声明 `private partial bool CanExecute{名称}Command(object? parameter)` 供你实现。为 `false` 时生成的谓词是 `_ => true`。 |
| `semaphore` | 最大并发执行数。writer 存入 `Math.Max(1, semaphore)`，因此生成的命令容量绝不会小于 1。 |

## 2. 可接受的方法签名

writer 分两件事判断：**返回类型**决定“值如何变成 Task”，**形参列表**决定“走哪个构造入口”。前导形参可以是 0 个或 1 个，末尾可选跟一个 `CancellationToken`。

| 方法形态 | 解析出的构造方式 |
|---|---|
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter(Func<object?, Task>)` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task>)` |
| `Task M(object? parameter, CancellationToken ct)` | 主构造函数（`Func<object?, CancellationToken, Task>`） |
| `Task<T> M(...)` | 与对应的 `Task M(...)` 行相同 —— `T` 被丢弃 |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M()` | `() => M().AsTask()` thunk → `VeloxCommand(Func<Task>)` |
| `ValueTask M(CancellationToken ct)` | `ct => M(ct).AsTask()` thunk → `CreateTaskOnlyWithCancellationToken` |
| `ValueTask<T> M(...)` | 与对应的 `ValueTask M(...)` 行相同 |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | thunk 对参数做强转：`parameter => M((T)parameter!)`（`ValueTask` 再补 `.AsTask()`） |

**被拒绝的形态**会触发生成器诊断 **`VELOXCMD001`**（`Src/Generators/VeloxDev.Core.Generator/Diagnostics.cs`），级别为**错误**，该方法被跳过 —— 类里其余部分照常生成：

| 被拒绝的形态 | 原因 |
|---|---|
| `void M(CancellationToken ct)` | 同步方法体无法观测该 token；想可取消就返回 `Task` |
| 泛型方法 `M<T>(...)` | 生成的 method group 无法从单个 `object?` 实参推断类型实参（泛型**类**不受影响） |
| 末尾 token 之前有多于一个形参 | 一条命令只携带一个实参；改用 record 或元组 |
| 返回类型不是 `Task`、`Task<T>`、`ValueTask`、`ValueTask<T>` 或 `void` | 无法把它变成命令 |

**预期结果：** 每一种被接受的形态都能编译并生成非空的命令属性；被拒绝的形态会让构建以 `VELOXCMD001` 失败（消息里含方法名与原因），且不会为它生成 `{名称}Command` 属性。

## 3. 最小命令与其生成代码

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

真实生成的属性（每个类一个文件 `{类名}_{命名空间}_Commands.g.cs`）是：

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_IncrementCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand IncrementCommand
{
    get
    {
        _buffer_IncrementCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Increment,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_IncrementCommand;
    }
}
```

属性在首次访问时创建并缓存在 `_buffer_IncrementCommand` 中。

带单个强类型形参的 `ValueTask` 方法体会解析为一段转换 thunk，而不是 method group —— 运行时不需要 `ValueTask` 版的 `VeloxCommand`，因此同一份生成代码在所有支持目标框架上都可用：

```csharp
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
```

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_SumToCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand SumToCommand
{
    get
    {
        _buffer_SumToCommand ??= global::VeloxDev.MVVM.VeloxCommand.CreateTaskOnlyWithParameter(
            command: parameter => SumToAsync((int)parameter!).AsTask(),
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_SumToCommand;
    }
}
```

**预期结果：** `vm.IncrementCommand` 非空且 `CanExecute(null)` 为 `true`；`vm.SumToCommand.Execute(10)` 会以 `limit == 10` 抵达 `SumToAsync`。thunk 里的强转是运行期强转 —— 传错类型会让该次执行以 `InvalidCastException` 失败（`CommandOutcome.Failed`），而不会静默地什么都不做。

## 4. 可执行性校验（`canValidate: true`）

开启校验后，生成器会声明一个你必须实现的 `partial` 谓词 —— 不实现是编译错误，而不是一条永远可执行却无人察觉的命令：

```csharp
[VeloxCommand(canValidate: true)]
private Task Decrement(object? parameter, CancellationToken ct)
{
    Count--;
    return Task.CompletedTask;
}

private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
```

每当 `CanExecuteChanged` 被触发时该谓词会被重新查询，因此在任何影响它的变化之后调用 `{名称}Command.Notify()`。WPF 演示正是从属性钩子里这么做的：`partial void OnIndexChanged(int oldValue, int newValue) { MinusCommand.Notify(); }`。

**预期结果：** 当 `Count == 0` 时 `DecrementCommand.CanExecute(null)` 为 `false`，绑定的按钮被禁用；当 `Count > 0` 且执行过 `DecrementCommand.Notify()` 后，`CanExecute(null)` 为 `true`，按钮启用。

## 5. 命令与框架无关

命令运行时是普通类 —— 不引用任何 UI 类型。两个演示都通过 .NET `ICommand` 契约直接绑定 `PlusCommand` / `MinusCommand`，控制台宿主也可以调用同一条命令。

**预期结果：** 同一个视图模型类在 WPF 与 Avalonia 中绑定结果完全一致；最后一页的完整代码程序在没有任何 UI 的情况下对这些命令调用 `ExecuteAndWaitAsync`。

## 运行声明

- ✅ 2026-10-01 实际构建并运行过。第 3 节的两段生成代码逐字取自 `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs`，它由一个临时控制台项目执行 `dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true` 产出（该项目项目引用 `VeloxDev.Core` 与 `VeloxDev.Core.Generator`）。同一次构建中的两条命令也被实际执行，录制输出：

  ```text
  Increment -> Completed (Succeeded=True)
  SumTo(10) -> Completed
  ```

- 第 2 节的拒绝矩阵本次**未**重跑。它转录自 `CommandWriter.TryBuildCommandExpression` 与 `Diagnostics.UnsupportedCommandSignature`，并由 `Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs` 覆盖（直接驱动生成器并断言 `VELOXCMD001` 的 id 与消息片段）。
