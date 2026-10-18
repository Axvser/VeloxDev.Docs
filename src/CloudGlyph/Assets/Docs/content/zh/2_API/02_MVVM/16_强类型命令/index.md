# MVVM — 强类型命令

强类型面让形参与结果以自身类型穿过队列、锁与完成通道。它由四个公开部分加一个事件载荷组成。

## `IVeloxCommand<TParam, TResult>`

`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand{TParam,TResult}.cs`：

```csharp
public interface IVeloxCommand<TParam, TResult> : IVeloxCommand
{
    bool CanExecute(TParam parameter);
    void Execute(TParam parameter);
    Task ExecuteAsync(TParam parameter);
    Task<TResult> ExecuteAsync(TParam parameter, CancellationToken cancellationToken);
    void Execute(TParam parameter, out TResult result);
}
```

**这是类型信息，不是编译期保证。** 由于接口派生自 `IVeloxCommand`，`object?` 重载始终可达：传入错误类型的调用仍能编译，并以携带 `InvalidCastException` 的 `Failed` 执行结束。强类型成员换来的是可读的签名、强类型校验器与未装箱的管线路径。

双实参 `ExecuteAsync` 重载是为了**重载**而不是隐藏 `IVeloxCommand.ExecuteAsync(object?)`：单实参调用仍在受理后立即返回。

**Arity 族。** `Src/Core/VeloxDev.Core/MVVM/CommandArities.cs`（生成文件）为 2 ≤ n ≤ 15 声明 `IVeloxCommand<T1, …, Tn, TResult>` 与 `VeloxCommand<T1, …, Tn, TResult>`。每个类：

```csharp
public sealed class VeloxCommand<T1, T2, TResult>
    : CommandPipeline<(T1, T2), TResult>, IVeloxCommand<T1, T2, TResult>
{
    public VeloxCommand(
        Func<T1, T2, CancellationToken, Task<TResult>> command,
        Func<T1, T2, bool>? canExecute = null,
        int semaphore = 1);

    public static VeloxCommand<T1, T2, TResult> CreateTaskOnlyWithResult(
        Func<T1, T2, Task<TResult>> command,
        Func<T1, T2, bool>? canExecute = null,
        int semaphore = 1);
}
```

元组是实现细节：公开面不含元组，而 `ValueTuple` 不分配。

## `VeloxCommand<TParam, TResult>`

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand{TParam,TResult}.cs`：

```csharp
public sealed class VeloxCommand<TParam, TResult>
    : CommandPipeline<TParam, TResult>, IVeloxCommand<TParam, TResult>
{
    public VeloxCommand(
        Func<TParam, CancellationToken, Task<TResult>> command,
        Predicate<TParam>? canExecute = null,
        int semaphore = 1);   // command 为 null 时抛 ArgumentNullException

    public static VeloxCommand<TParam, TResult> CreateTaskOnlyWithResult(
        Func<TParam, Task<TResult>> command,
        Predicate<TParam>? canExecute = null,
        int semaphore = 1);
}
```

无返回值的方法体把 `TResult` 设为 `object`，且恒为 `null`；生成器通过 `VeloxCommand.CreateTypedTaskOnlyWithParameter<T>` 与 `CreateTypedWithParameter<T>` 做到这点，它们返回 `VeloxCommand<T, object?>`。

## `CommandPipeline<TParam, TResult>`

`Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs` 是每条命令共享的公开抽象基类：

```csharp
public abstract class CommandPipeline<TParam, TResult> :
    IVeloxCommand, IVeloxCommandCompletion, IVeloxCommandStatus, IVeloxCommandResult,
    IVeloxCommandEvents<TParam, TResult>, IDisposable
{
    protected CommandPipeline(
        Func<TParam, CancellationToken, Task> command,
        Func<TParam, CancellationToken, Task<TResult>>? resultCommand,
        Predicate<TParam>? canExecute,
        int semaphore,
        bool isCtsNeeded);
}
```

它提供 `VeloxCommand` 页面上记录的所有成员（事件、`EventContext`、状态、锁 / 中断 / 清空、`ExecuteAndWaitAsync`、`Dispose`），并给子类提供强类型辅助方法：

| 成员 | 访问 | 用途 |
| --- | --- | --- |
| `CanExecuteCore(TParam)` | protected | 谓词加强制锁标志 |
| `ExecuteAsyncCore(TParam)` | protected | 启动执行，受理后返回 |
| `ExecuteAndWaitTypedAsync(TParam, CancellationToken)` | protected | 等待本次执行并返回 `TResult` |
| `ExecuteAndWaitTyped(TParam)` | protected | 阻塞版本 |
| `HandlerException` | public static | 进程级的抛异常订阅者钩子 |

## `IVeloxCommandEvents<TParam, TResult>`

```csharp
public interface IVeloxCommandEvents<TParam, TResult>
{
    event CommandEventHandler<TParam, TResult>? Created;
    event CommandEventHandler<TParam, TResult>? Enqueued;
    event CommandEventHandler<TParam, TResult>? Dequeued;
    event CommandEventHandler<TParam, TResult>? Started;
    event CommandEventHandler<TParam, TResult>? Completed;
    event CommandEventHandler<TParam, TResult>? Failed;
    event CommandEventHandler<TParam, TResult>? Canceled;
    event CommandEventHandler<TParam, TResult>? Exited;
}
```

阶段含义与 `IVeloxCommand` 上完全一致，只是载荷不同。实现是显式的，因为一个类不能声明两个同名的公开事件。

## `CommandEventArgs<TParam, TResult>`

```csharp
public sealed class CommandEventArgs<TParam, TResult> : CommandEventArgs
{
    public TParam TypedParameter { get; }
    public TResult TypedResult { get; }
    public override object? Parameter { get; }
    public new CommandEventArgs<TParam, TResult> With(CommandEventType newType, Exception? ex = null);
}
```

`TypedParameter` 在调用方法体处执行转换，因此经 `ICommand.Execute` 传入的错误实参会让该次执行以 `Failed` 结束，而不是在调用点抛异常。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs
var vm = new CommandSignatureViewModel();

IVeloxCommand<string, object?> text = vm.TypedStringCommand;
IVeloxCommand<string, object?> fromVoid = vm.TypedVoidCommand;

await RunToCompletionAsync(text, "hello");
await RunToCompletionAsync(fromVoid, "void");

CollectionAssert.AreEqual(new[] { "hello", "void" }, vm.TypedSeen);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs
var completion = await vm.TypedStringCommand.ExecuteAndWaitAsync(42);

Assert.AreEqual(CommandOutcome.Failed, completion.Outcome);
Assert.IsInstanceOfType<InvalidCastException>(completion.Exception);
```

第二个例子展示了该注意事项的实际形态：属性虽然是强类型的，但继承来的 `object?` 入口仍接受错误类型，只在运行期失败。
