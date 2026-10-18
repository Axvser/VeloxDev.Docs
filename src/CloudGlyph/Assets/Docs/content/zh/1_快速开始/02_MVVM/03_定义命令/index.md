# MVVM — 定义命令

方法上的 `[VeloxCommand]` 会生成一个懒加载的命令属性（泛型方法则生成缓存访问器），包装该方法。

## 1. 特性参数

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]` —— 声明于 `Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`。

| 参数 | 含义 |
| --- | --- |
| `name` | 命令名。`"Auto"`（默认）由方法名移除**所有** `Async` 子串得到：`Plus` → `PlusCommand`、`IncrementAsync` → `IncrementCommand`、`SumToAsync` → `SumToCommand`。其它取值原样使用，仍会追加 `Command`。 |
| `canValidate` | 为 `true` 时，生成的命令使用 `private partial bool CanExecute{Name}Command(...)` 谓词，该类必须实现它。为 `false` 时生成的谓词恒为 true。 |
| `semaphore` | 最大并发执行数。写入器保存 `Math.Max(1, semaphore)`，因此生成的命令容量绝不小于 1。 |

## 2. 可接受的方法签名

返回类型必须是 `Task`、`Task<T>`、`ValueTask`、`ValueTask<T>` 或 `void`。前导形参可选，最多 **15** 个，末尾可再跟一个 `CancellationToken`。

| 形态 | 生成的命令 |
| --- | --- |
| 无前导形参，返回 `Task` / `ValueTask` / `void` | 非强类型 `IVeloxCommand`，用接收 `Task` 或 `Action` 的构造函数创建 |
| 一个 `object?` 形参 | 非强类型 `IVeloxCommand`，实参保持装箱 |
| 一个其它类型 `T` 的形参 | `IVeloxCommand<T, TResult>`；属性与管线以未装箱的 `T` 传递 |
| 二到十五个前导形参 | `CommandArities.cs` 中 arity 族的 `IVeloxCommand<T1, …, Tn, TResult>` |
| 返回 `Task<T>` / `ValueTask<T>` | `TResult` 为 `T`，值由 `IVeloxCommandResult` / 强类型 `ExecuteAsync` 重载交回 |
| 返回 `Task` / `ValueTask` / `void` | `TResult` 为 `object?`，且恒为 `null` |
| 泛型方法 `M<T>(T value) where T : …` | 缓存访问器 `IVeloxCommand<T, TResult> GetMCommand<T>()` —— 每个封闭 `T` 一条命令，各有自己的队列与锁 |

只有 `CancellationToken` 形参能让方法体真正可取消。其它形态构造出的命令，其方法体永远拿不到 token：被中断时上报 `Canceled`，但方法体仍会跑完。

**被拒绝的形态**会在方法自己的代码行上报告错误 `VELOX_MVVM_CMD001` 并被跳过；类中其余部分照常生成：

| 被拒绝的形态 | 原因 |
| --- | --- |
| `void M(CancellationToken ct)` | 同步方法体无法观测 token |
| 类型参数未出现在形参类型中的泛型方法 | 访问器没有可携带的类型实参 |
| 多于 15 个前导形参 | 生成的 `Func` 会超出类型实参上限；改用 record 或元组 |
| 不在接受集合内的返回类型 | 无法转换成命令 |

**预期结果：** 每个被接受的形态都编译出非空命令；被拒绝的形态以 `VELOX_MVVM_CMD001` 使构建失败并指出方法名与原因，且不为它生成任何成员。

## 3. 生成的成员

普通非强类型命令的生成文件包含：

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_SaveCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand SaveCommand
{
    get
    {
        _buffer_SaveCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Save,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_SaveCommand;
    }
}
```

对于 `private Task Save(string name)`，属性变为 `IVeloxCommand<string, object?>`，getter 使用 `VeloxCommand<string, object?>.CreateTypedTaskOnlyWithParameter(...)`。多形参方法使用对应的 arity 构造函数。缓冲字段在首次读取时创建并缓存。

**预期结果：** `vm.SaveCommand` 非空、类型符合文档；除非谓词或锁另有决定，`CanExecute` 返回 `true`。

## 4. 可执行性校验

```csharp
[VeloxCommand(canValidate: true)]
private Task Remove(NotePayload note)
{
    return Task.CompletedTask;
}

private partial bool CanExecuteRemoveCommand(NotePayload note)
    => note is not null && note.Weight > 0;
```

校验器的形参表跟随源方法的前导形参：无前导形参时是 `object? parameter`；否则复制类型与名字，不一致会报 `CS8826`。`CanExecuteChanged` 每次触发时都会重新查询谓词，因此在可能影响它的变化之后调用 `{Name}Command.Notify()`。示例在属性钩子里这么做：`partial void OnIndexChanged(int oldValue, int newValue) { MinusCommand.Notify(); }`。

**预期结果：** 不满足谓词的值报告 `CanExecute == false`；调用 `Notify()` 后变为 `true`，绑定的按钮启用。

## 5. 命令与框架无关

命令运行时不引用任何 UI 类型。两个示例都通过 `ICommand` 绑定 `PlusCommand` / `MinusCommand`，控制台宿主也可以调用同一条命令。

**预期结果：** 同一份视图模型在 WPF 与 Avalonia 中无需改动即可绑定；最后一页的控制台程序在没有任何 UI 的情况下调用这些命令。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `Writers/CommandWriter.cs`、`Diagnostics.cs`、`MVVM/VeloxCommand.cs`、`MVVM/CommandArities.cs`、`Base/AIContextNaming.cs`、`Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs` 与 `Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs` 做了静态核对。
