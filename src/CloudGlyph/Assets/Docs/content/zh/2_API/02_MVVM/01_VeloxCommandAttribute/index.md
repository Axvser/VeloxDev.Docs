# MVVM — `VeloxCommandAttribute`

标记一个方法包装为 `IVeloxCommand`。

**签名**（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`，第 34-43 行）：

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
| `name` | 命令属性名。`"Auto"`（默认）根据方法名推导并去掉 `Async` 后缀（`Plus` → `PlusCommand`、`IncrementAsync` → `IncrementCommand`）— `CommandWriter.cs`，第 63-67 行。 |
| `canValidate` | 为 `true` 时必须实现 `private partial bool CanXxxCommand(object? parameter)`。 |
| `semaphore` | 最大并发执行数（必须 >= 1）；默认 `1` = 串行并排队。 |

**可接受的方法签名**（特性 XML 文档，第 10-18 行）：`Task M(object?, CancellationToken)`、`Task M(object?)`、`Task M(CancellationToken)`、`Task M()`、`void M(object?)`、`void M()`。

**工厂映射**（`CommandWriter.ParseConstructorType`，第 78-116 行）：

| 签名 | 生成的工厂 |
|---|---|
| `Task M(object?, CancellationToken)` | `new VeloxCommand(command: M, ...)`（主构造函数） |
| `Task M(object?)` | `VeloxCommand.CreateTaskOnlyWithParameter(command: M, ...)` |
| `Task M(CancellationToken)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(command: M, ...)` |
| `Task M()` | `new VeloxCommand(command: M, ...)`（绑定 `Func<Task>` 构造函数） |
| `void M(object?)` | `new VeloxCommand(command: M, ...)`（绑定 `Action<object?>` 构造函数） |
| `void M()` | `new VeloxCommand(command: M, ...)`（绑定 `Action` 构造函数） |

- **示例：** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 64-84 行 — `[VeloxCommand(canValidate: true)] private Task Minus(object? sender, CancellationToken ct)`。
