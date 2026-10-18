# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`）标记一个方法；`VeloxDev.Generators.Command` 把它暴露为懒加载命令属性（或泛型访问器）。

## Class: `VeloxCommandAttribute`

**Signature**

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

- **基类型：** `System.Attribute`。`sealed`。
- **目标：** 仅 `Method`。`AllowMultiple = false`、`Inherited = false`。
- **构造函数：** 主构造函数；三个参数都可选。

##### Properties

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `Name` | `string` | 命令名。`"Auto"` 由方法名派生。 |
| `CanValidate` | `bool` | 是否启用可执行性校验。默认 `false`。 |
| `Semaphore` | `int` | 最大并发执行数。默认 `1`。 |

## 参数语义

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 命令名。`"Auto"` 从方法名移除**所有** `Async` 子串，再追加 `Command`：`Plus` → `PlusCommand`、`SaveAsync` → `SaveCommand`、`SumToAsync` → `SumToCommand`。其它取值原样使用（`name: "Add"` → `AddCommand`）。 |
| `canValidate` | `bool` | 为 `true` 时生成器使用 `CanExecute{Name}Command`，并把它声明为 `private partial bool`。跟随源方法：无前导形参时接收 `object? parameter`，否则复制源方法前导形参的类型与名字。为 `false` 时谓词恒为 true。 |
| `semaphore` | `int` | 并发容量。写入器保存 `Math.Max(1, semaphore)`，因此生成的命令容量绝不小于 1。把更小的值直接传给 `VeloxCommand` 构造函数**会**抛 `ArgumentOutOfRangeException`。 |

## 可接受的方法签名

返回类型必须是 `Task`、`Task<T>`、`ValueTask`、`ValueTask<T>` 或 `void`。前导形参可选，最多 **15** 个，末尾可跟一个 `CancellationToken`。

| 签名 | 生成的构造方式 |
| --- | --- |
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` |
| `Task M(object? parameter, CancellationToken ct)` | 主构造函数 |
| `Task<T> M(...)` | 非强类型时走结果通道（`CreateTaskWithResult` / `CreateTaskOnlyWithResult`）；强类型时走 `VeloxCommand<T, TResult>` |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M(...)` | `.AsTask()` thunk → `Func<...>` |
| `ValueTask<T> M(...)` | 带结果通道的 `.AsTask()` thunk |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | 强类型命令：`IVeloxCommand<T, TResult>`；getter 使用强类型构造/工厂 |
| `M(T1 a, T2 b, ...)` | 强类型 arity 命令：`IVeloxCommand<T1, T2, ..., TResult>` |
| `Task M<T>(T value) where T : ...` | 缓存访问器 `IVeloxCommand<T, TResult> GetMCommand<T>()`；每个封闭 `T` 一条命令 |

对于 `Task<T>` / `ValueTask<T>`，`TResult` 为 `T`；其它返回类型的 `TResult` 为 `object?`，恒为 `null`。

### 被拒绝的签名 —— `VELOX_MVVM_CMD001`

| 签名 | 原因 |
| --- | --- |
| `void M(CancellationToken ct)` | 同步方法体无法观测它 |
| 类型参数未出现在形参类型中的泛型方法 | 访问器没有可携带的类型实参 |
| 多于 15 个前导形参 | 生成的 `Func` 会超出类型实参上限 |
| 不在接受集合内的返回类型 | 无法转换成命令 |

被拒绝的方法会被跳过；类中其余部分照常生成。

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs
[VeloxCommand(name: "Auto", canValidate: false, semaphore: 1)]
private Task Plus(object? sender, CancellationToken ct)
{
    Index++;
    Greeting = $"current index: {Index}";
    return Task.CompletedTask;
}

[VeloxCommand(canValidate: true)]
private Task Minus(object? sender, CancellationToken ct)
{
    Index--;
    Greeting = $"current index: {Index}";
    return Task.CompletedTask;
}

private partial bool CanExecuteMinusCommand(object? sender)
{
    return _index > 0;
}
```

`PlusCommand` 使用恒真谓词；`MinusCommand` 使用 `CanExecuteMinusCommand`。两者都是懒加载的 —— 在有人读取属性之前命令对象并不存在。

**说明：**

- 派生成员名是 `{Name}Command`；`Name` 来自 `name` 参数或自动规则。
- 在可能影响校验器的变化之后调用 `{Name}Command.Notify()`。WPF 示例从 `partial void OnIndexChanged(...)` 里这么做。
- 只有 `CancellationToken` 形参能让命令停止方法体。其它形态被中断时上报 `Canceled`，而方法体仍会跑完。
- 生成的属性类型是 `IVeloxCommand` 或 `IVeloxCommand<TParam, TResult>`；额外能力经 `VeloxCommandExtensions` 或强类型接口取得。
