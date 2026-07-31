# MVVM — API Reference

## Namespace `VeloxDev.MVVM`

### Attributes

#### `VeloxPropertyAttribute`

Full signature (Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs, lines 25-29):

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

Targets a private field (`_index`) or a `partial` property. The MVVM generator expands it into a public observable property plus `partial void OnXxxChanging/OnXxxChanged` hooks; when the type implements `INotifyCollectionChanged`, collection-tracking members are added.

#### `VeloxCommandAttribute`

Full signature (Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs, lines 34-43):

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

| Parameter | Meaning |
|---|---|
| `name` | Command property name. `"Auto"` (default) derives it from the method name (`Plus` → `PlusCommand`), stripping a trailing `Async` suffix (CommandWriter.cs, lines 63-67). |
| `canValidate` | When `true`, a `private partial bool CanXxxCommand(object? parameter)` must be implemented. |
| `semaphore` | Max concurrent executions (must be ≥ 1); default `1` = serial with queueing. |

Accepted method signatures (attribute XML docs, lines 10-18): `Task M(object?, CancellationToken)`, `Task M(object?)`, `Task M(CancellationToken)`, `Task M()`, `void M(object?)`, `void M()`.

### `IVeloxCommand : ICommand`

Full interface (Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand.cs, lines 5-31):

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

Inherited from `ICommand`: `CanExecute(object?)`, `Execute(object?)`, event `CanExecuteChanged`.

| Method | Purpose |
|---|---|
| `ExecuteAsync(object?)` | Enqueue/start execution; returns a `Task` that completes once the invocation is dispatched. |
| `Lock()` / `UnLock()` | Toggle a force-lock; new triggers are canceled while locked, running commands are not interrupted. |
| `Interrupt()` / `InterruptAsync()` | Cancel the currently active invocation(s). |
| `Clear()` / `ClearAsync()` | Cancel active + all queued invocations. |
| `Continue()` / `ContinueAsync()` | Drain the pending queue (e.g. after `UnLock`). |
| `ChangeSemaphore(int)` | Adjust the max-concurrency at runtime (ignored when `< 1`). |
| `Notify()` | Raise `CanExecuteChanged`. |

### `VeloxCommand`

Concrete `IVeloxCommand` (Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs). Primary constructor (lines 16-18):

```csharp
public sealed class VeloxCommand(Func<object?, CancellationToken, Task> command,
                    Predicate<object?>? canExecute = null,
                    int semaphore = 1) : IVeloxCommand
```

Static factories and convenience constructors (lines 20-77):

| Member | Signature |
|---|---|
| `CreateTaskOnlyWithParameter` | `static VeloxCommand (Func<object?, Task>, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `CreateTaskOnlyWithCancellationToken` | `static VeloxCommand (Func<CancellationToken, Task>, Predicate<object?>? canExecute = null, int semaphore = 1)` |
| `VeloxCommand(Func<Task>, ...)` | wraps `await command()`; `_isCtsNeeded = false` |
| `VeloxCommand(Action<object?>, ...)` | synchronous with parameter |
| `VeloxCommand(Action, ...)` | synchronous without parameter |

State: `SemaphoreSlim _stateLock(1, 1)`, `Queue<CommandEventArgs> _pendingQueue`, `List<CommandEventArgs> _active`, `int _maxConcurrency`, `bool _isForceLocked` (lines 82-90). The generated command property is created lazily via `_buffer_XxxCommand ??= ...` (Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs, lines 140-190). Entry template, `canValidate: true` branch (lines 154-168, re-indented):

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

Enum (VeloxCommand.cs, lines 3-14):

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

(VeloxCommand.cs, lines 382-394):

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

`public delegate void CommandEventHandler(CommandEventArgs e);` (VeloxCommand.cs, line 380). Note the payload is a single `CommandEventArgs`, not a `(object sender, CommandEventArgs)` pair.

### `ObservableCollectionTracker`

Static helper (Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs, lines 15-56). Called from generated getters/setters so `CollectionChanged` stays subscribed even when the backing field is initialized directly (`= []`):

```csharp
public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)
public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)
```

Internally uses a `ConditionalWeakTable<object, Entry>` keyed by collection identity; handlers are deduplicated by reference (`Entry.TryAdd`), so there is no double subscription and no leak.

## Generator: `VeloxDev.Core.Generator`

| Item | Detail |
|---|---|
| Package | `VeloxDev.Core.Generator` (6.0.82), referenced transitively by `VeloxDev.Core` |
| Assembly namespace | `VeloxDev.Generators` |
| MVVM generator | `VeloxDev.Generators.MVVM : IIncrementalGenerator` (MVVM.cs, lines 12-13) |
| Command generator | `VeloxDev.Generators.Command : IIncrementalGenerator` (Command.cs, lines 12-13) |
| Property writer | `Writers/MVVMWriter.cs` + `Base/Analizer.cs` (`MVVMPropertyFactory`) |
| Command writer | `Writers/CommandWriter.cs` |
| Output names | `{ClassName}_{Namespace}_MVVM.g.cs`, `{ClassName}_{Namespace}_Commands.g.cs` (MVVMWriter.cs lines 847-854; CommandWriter.cs lines 121-130) |
