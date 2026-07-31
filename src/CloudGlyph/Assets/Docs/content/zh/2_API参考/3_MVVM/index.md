# MVVM — API 参考

## 命名空间 `VeloxDev.MVVM`

### 特性（Attributes）

#### `VeloxPropertyAttribute`

完整签名（Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs，第 25-29 行）：

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

目标为私有字段（`_index`）或 `partial` 属性。MVVM 生成器会将其展开为公开可观察属性，并附带 `partial void OnXxxChanging/OnXxxChanged` 钩子；当类型实现 `INotifyCollectionChanged` 时还会附加集合追踪成员。

#### `VeloxCommandAttribute`

完整签名（Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs，第 34-43 行）：

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
| `name` | 命令属性名。`"Auto"`（默认）根据方法名推导（`Plus` → `PlusCommand`），并去掉 `Async` 后缀（CommandWriter.cs，第 63-67 行）。 |
| `canValidate` | 为 `true` 时必须实现 `private partial bool CanXxxCommand(object? parameter)`。 |
| `semaphore` | 最大并发执行数（必须 ≥ 1）；默认 `1` = 串行并排队。 |

可接受的方法签名（特性 XML 文档，第 10-18 行）：`Task M(object?, CancellationToken)`、`Task M(object?)`、`Task M(CancellationToken)`、`Task M()`、`void M(object?)`、`void M()`。

### `IVeloxCommand : ICommand`

完整接口（Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs，第 5-31 行）：

```csharp
public interface IVeloxCommand : ICommand
{
    public event CommandEventHandler? Created;
    public event CommandEventHandler? Started;
    public event CommandEventHandler? Completed;
    public event CommandEventHandler? Canceled;
    public event CommandEventHandler? Failed;
    public event CommandEventHandler? Exited;
    public event CommandEventHandler? Enqueued;
    public event CommandEventHandler? Dequeued;

    public void Lock();
    public void UnLock();
    public void Notify();
    public void Clear();
    public void Interrupt();
    public void Continue();
    public void ChangeSemaphore(int semaphore);

    public Task ExecuteAsync(object? parameter);
    public Task LockAsync();
    public Task UnLockAsync();
    public Task ClearAsync();
    public Task InterruptAsync();
    public Task ContinueAsync();
    public Task ChangeSemaphoreAsync(int semaphore);
}
```

继承自 `ICommand`：`CanExecute(object?)`、`Execute(object?)`、事件 `CanExecuteChanged`。

| 方法 | 用途 |
|---|---|
| `ExecuteAsync(object?)` | 入队/开始执行；返回的 `Task` 在调用被分派后完成。 |
| `Lock()` / `UnLock()` | 切换强制锁定；锁定时新触发会被取消，正在执行的命令不会被打断。 |
| `Interrupt()` / `InterruptAsync()` | 取消当前活动的调用。 |
| `Clear()` / `ClearAsync()` | 取消活动 + 所有排队的调用。 |
| `Continue()` / `ContinueAsync()` | 排空待处理队列（例如 `UnLock` 之后）。 |
| `ChangeSemaphore(int)` | 运行时调整最大并发数（`< 1` 时忽略）。 |
| `Notify()` | 触发 `CanExecuteChanged`。 |

### `VeloxCommand`

`IVeloxCommand` 的具体实现（Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs）。主构造函数（第 16-18 行）：

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

静态工厂与便捷构造函数（第 20-77 行）：

| 成员 | 签名 |
|---|---|
| `CreateTaskOnlyWithParameter` | `static VeloxCommand (Func<object?, Task>, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand (Func<CancellationToken, Task>, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task>, ...)` | 包装 `await command()`；`_isCtsNeeded = false` |
| `VeloxCommand(Action<object?>, ...)` | 同步带参 |
| `VeloxCommand(Action, ...)` | 同步无参 |

内部状态：`SemaphoreSlim _stateLock(1, 1)`、`Queue<CommandEventArgs> _pendingQueue`、`List<CommandEventArgs> _active`、`int _maxConcurrency`、`bool _isForceLocked`（第 82-90 行）。生成的命令属性通过 `_buffer_XxxCommand ??= ...` 懒加载（Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs，第 140-190 行）。入口模板，`canValidate: true` 分支（第 154-168 行，重新缩进）：

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_PlusCommand = null;
public VeloxDev.MVVM.IVeloxCommand PlusCommand
{
    get
    {
        _buffer_PlusCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Plus,
            canExecute: CanExecutePlusCommand,
            semaphore: 1);
        return _buffer_PlusCommand;
    }
}
private partial bool CanExecutePlusCommand(object? parameter);
```

### `CommandEventType`

枚举（VeloxCommand.cs，第 3-14 行）：

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,
    Enqueued,
    Dequeued,
    Started,
    Completed,
    Failed,
    Canceled,
    Exited
}
```

### `CommandEventArgs`

（VeloxCommand.cs，第 382-394 行）：

```csharp
public sealed class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;
    public CancellationTokenSource? Cts { get; internal set; } = cts;

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null)
        => new(Parameter, newType, ex ?? Exception, Cts);
}
```

### `CommandEventHandler`

`public delegate void CommandEventHandler(CommandEventArgs e);`（VeloxCommand.cs，第 380 行）。注意参数是单个 `CommandEventArgs`，不是 `(object sender, CommandEventArgs)` 形式。

### `ObservableCollectionTracker`

静态辅助类（Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs，第 15-56 行）。由生成的 getter/setter 调用，确保即使在字段直接初始化（`= []`）的情况下 `CollectionChanged` 仍保持订阅：

```csharp
public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)
public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)
```

内部使用以集合身份为键的 `ConditionalWeakTable<object, Entry>`；处理器按引用去重（`Entry.TryAdd`），因此不会重复订阅，也不会泄漏。

## 生成器：`VeloxDev.Core.Generator`

| 项目 | 详情 |
|---|---|
| 包 | `VeloxDev.Core.Generator`（6.0.82），由 `VeloxDev.Core` 传递引用 |
| 程序集命名空间 | `VeloxDev.Generators` |
| MVVM 生成器 | `VeloxDev.Generators.MVVM : IIncrementalGenerator`（MVVM.cs，第 12-13 行） |
| 命令生成器 | `VeloxDev.Generators.Command : IIncrementalGenerator`（Command.cs，第 12-13 行） |
| 属性写入器 | `Writers/MVVMWriter.cs` + `Base/Analizer.cs`（`MVVMPropertyFactory`） |
| 命令写入器 | `Writers/CommandWriter.cs` |
| 输出文件名 | `{ClassName}_{Namespace}_MVVM.g.cs`、`{ClassName}_{Namespace}_Commands.g.cs`（MVVMWriter.cs 第 847-854 行；CommandWriter.cs 第 121-130 行） |
