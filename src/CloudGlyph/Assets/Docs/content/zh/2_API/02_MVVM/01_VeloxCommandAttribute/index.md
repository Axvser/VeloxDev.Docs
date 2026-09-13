# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`）标记一个方法；Command 源生成器会在所在类上把它暴露为懒创建的 `IVeloxCommand` 属性。

**签名**

```csharp
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false, Inherited = false)]
public sealed class VeloxCommandAttribute(
    string name = "Auto",
    bool canValidate = false,
    int semaphore = 1) : Attribute
{
    public string Name { get; } = name;
    public bool CanValidate { get; } = canValidate;
    public int Semaphore { get; } = semaphore;
}
```

| 参数 | 含义 |
|---|---|
| `name` | 命令属性名。`"Auto"`（默认）根据方法名推导：去掉所有 `Async` 子串，再追加 `Command` — `Plus` → `PlusCommand`、`SaveAsync` → `SaveCommand`。 |
| `canValidate` | 为 `true` 时，生成器产出 `private partial bool CanExecute{Name}Command(object? parameter)`，类必须实现它。 |
| `semaphore` | 最大并发执行数（实际取 `Math.Max(1, semaphore)`）；默认 `1` = 串行并排队。 |

## 可接受的方法签名

按特性 XML 文档，被标记方法必须匹配以下形态之一（返回 `Task` 或 `void`）：

- `Task M(object? parameter, CancellationToken ct)`
- `Task M(object? parameter)`
- `Task M(CancellationToken ct)`
- `Task M()`
- `void M(object? parameter)`
- `void M()`

## 工厂选择（`CommandWriter.ParseConstructorType`）

| 签名 | 选用的构造函数 / 工厂 |
|---|---|
| `Task M(object?, CancellationToken)` | 主构造函数 — 委托 `Func<object?, CancellationToken, Task>` |
| `Task M(object?)` | `VeloxCommand.CreateTaskOnlyWithParameter` — 委托 `Func<object?, Task>` |
| `Task M(CancellationToken)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` — 委托 `Func<CancellationToken, Task>` |
| `Task M()` | `Func<Task>` 构造函数 |
| `void M(object?)` | `Action<object?>` 构造函数 |
| `void M()` | `Action` 构造函数 |

生成器只选择工厂；剩余方法组绑定到哪个 `VeloxCommand` 构造函数由 C# 重载解析决定。完整构造函数/工厂列表见 [VeloxCommand](../03_VeloxCommand/index.md)。

## `canValidate` 命名契约（Demo 验证）

`canValidate: true` 时，产出的属性把生成的 `partial` 方法作为 `canExecute` 谓词，因此类必须实现 `private partial bool CanExecute{Name}Command(object? parameter)`。当可能影响谓词结果的状态发生变化时，请调用 `{Name}Command.Notify()` 以便触发 `CanExecuteChanged`。

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 70-81 行：

```csharp
[VeloxCommand(canValidate: true)]
private Task Minus(object? sender, CancellationToken ct)
{
    Index--;
    Greeting = $"current index: {Index}";
    return Task.CompletedTask;
}
/* This partial method must be implemented at this point */
private partial bool CanExecuteMinusCommand(object? parameter)
{
    return _index > 0;
}
```

派生的属性名为 `MinusCommand`（方法名 `Minus`，没有需要去掉的 `Async` 后缀）。`canValidate: false` 时，产出的 `canExecute` 谓词是 `_ => true`。

## 生命周期语义

生成的每条命令在达到 `semaphore` 容量后会把多余的执行排队，并触发 `IVeloxCommand` 生命周期事件（`Created`、`Enqueued`、`Dequeued`、`Started`、`Completed`、`Failed`、`Canceled`、`Exited`）——见 [IVeloxCommand](../02_IVeloxCommand/index.md)。只有接收 `CancellationToken` 的签名（`Task M(object?, CancellationToken)` / `Task M(CancellationToken)`）才能取消正在运行的方法；详见 [VeloxCommand](../03_VeloxCommand/index.md) 的取消说明。
