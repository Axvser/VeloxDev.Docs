# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`）标记一个方法；Command 源生成器把它暴露为所在类上的懒加载 `IVeloxCommand` 属性。

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
|---|---|---|
| `Name` | `string` | 命令属性名。`"Auto"`（默认）由方法名派生。 |
| `CanValidate` | `bool` | 是否为该命令启用可执行性校验。默认 `false`。 |
| `Semaphore` | `int` | 最大并发执行数。默认 `1`。 |
| `AttributeUsage` | — | `AttributeTargets.Method`、`AllowMultiple = false`、`Inherited = false`。 |

## 参数语义

| 参数 | 类型 | 说明 |
|---|---|---|
| `name` | `string` | 命令属性名。`"Auto"` 由方法名派生：移除**所有** `Async` 子串再追加 `Command` —— `Plus` → `PlusCommand`，`SaveAsync` → `SaveCommand`，`SumToAsync` → `SumToCommand`。其它取值原样使用（`name: "Add"` → `AddCommand`）。 |
| `canValidate` | `bool` | 为 `true` 时生成器以 `canExecute: CanExecute{名称}Command` 构造属性，并声明 `private partial bool CanExecute{名称}Command(object? parameter)`，该类必须实现它。为 `false` 时生成的谓词是 `_ => true`。 |
| `semaphore` | `int` | 并发容量。写入生成代码的是 `Math.Max(1, semaphore)`，因此生成的命令容量绝不小于 1。把小于 1 的值直接传给 `VeloxCommand` 构造函数**会**抛 `ArgumentOutOfRangeException`。 |

## 可接受的方法签名

被标注方法的返回类型必须是 `Task`、`Task<T>`、`ValueTask`、`ValueTask<T>` 或 `void`；前导形参可以是 0 个或 1 个，末尾可选跟一个 `CancellationToken`。

| 签名 | 生成的构造方式 |
|---|---|
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` |
| `Task M(object? parameter, CancellationToken ct)` | 主构造函数 |
| `Task<T> M(...)` | 与对应的 `Task M(...)` 行相同（返回值被丢弃） |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M()` | `() => M().AsTask()` thunk → `Func<Task>` |
| `ValueTask M(CancellationToken ct)` | `ct => M(ct).AsTask()` thunk → `CreateTaskOnlyWithCancellationToken` |
| `ValueTask<T> M(...)` | 与对应的 `ValueTask M(...)` 行相同 |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | 强转 thunk `parameter => M((T)parameter!)`（`ValueTask` 再补 `.AsTask()`） |

### 被拒绝的签名 —— `VELOXCMD001`

| 签名 | 诊断消息片段 |
|---|---|
| `void M(CancellationToken ct)` | `void` —— 同步方法体无法观测它 |
| 泛型方法 `M<T>(...)` | `generic` |
| 多于一个前导形参 | `more than one parameter` |
| 不在接受集合内的返回类型 | `it returns '…'` |

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 60-81
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

private partial bool CanExecuteMinusCommand(object? parameter)
{
    return _index > 0;
}
```

`PlusCommand` 以 `canExecute: _ => true` 构造；`MinusCommand` 以 `canExecute: CanExecuteMinusCommand` 构造。两者都是懒加载的 —— 在有人读取该属性之前命令对象并不存在。

**Notes:**

- 派生出的属性名是 `{名称}Command`；`名称` 来自 `name` 参数或自动命名规则。
- 在可能影响 `CanExecute{名称}Command` 的变化之后调用 `{名称}Command.Notify()`，以触发 `CanExecuteChanged`。WPF 演示从 `partial void OnIndexChanged(...)` 里这么做。
- 只有 `CancellationToken` 形参能让命令真正停止方法体。其它形态构造出的命令，其方法体永远拿不到 token，所以被中断时上报 `Canceled`，而方法体仍会跑完。
- 生成的属性类型是 `IVeloxCommand` 而非 `VeloxCommand`；额外能力（`ExecuteAndWaitAsync`、`IsBusy` 等）经 `VeloxCommandExtensions` 取得。
