# MVVM — Typed commands

The typed surface keeps the parameter and the result in their own types through the queue, the lock and the completion. It is built from four public pieces plus the event payload.

## `IVeloxCommand<TParam, TResult>`

`Src/Core/VeloxDev.Core/Interfaces/MVVM/IVeloxCommand{TParam,TResult}.cs`:

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

**This is type information, not a compile-time guarantee.** Because the interface derives from `IVeloxCommand`, the `object?` overloads stay reachable: a call passing the wrong type still compiles and ends as a `Failed` execution carrying an `InvalidCastException`. The typed members buy a readable signature, a strongly typed validator, and an unboxed pipeline path.

The two-argument `ExecuteAsync` overload exists so it *overloads* rather than hides `IVeloxCommand.ExecuteAsync(object?)`: a one-argument call still returns once the call is accepted.

**Arity family.** `Src/Core/VeloxDev.Core/MVVM/CommandArities.cs` (generated) declares `IVeloxCommand<T1, …, Tn, TResult>` and `VeloxCommand<T1, …, Tn, TResult>` for 2 ≤ n ≤ 15. Each class:

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

The tuple is an implementation detail: the public surface is tuple-free, and a `ValueTuple` allocates nothing.

## `VeloxCommand<TParam, TResult>`

`Src/Core/VeloxDev.Core/MVVM/VeloxCommand{TParam,TResult}.cs`:

```csharp
public sealed class VeloxCommand<TParam, TResult>
    : CommandPipeline<TParam, TResult>, IVeloxCommand<TParam, TResult>
{
    public VeloxCommand(
        Func<TParam, CancellationToken, Task<TResult>> command,
        Predicate<TParam>? canExecute = null,
        int semaphore = 1);   // ArgumentNullException when command is null

    public static VeloxCommand<TParam, TResult> CreateTaskOnlyWithResult(
        Func<TParam, Task<TResult>> command,
        Predicate<TParam>? canExecute = null,
        int semaphore = 1);
}
```

A body with no return value uses `object` for `TResult` and always yields `null`; the generator does this through `VeloxCommand.CreateTypedTaskOnlyWithParameter<T>` and `CreateTypedWithParameter<T>`, which return `VeloxCommand<T, object?>`.

## `CommandPipeline<TParam, TResult>`

`Src/Core/VeloxDev.Core/MVVM/CommandPipeline{TParam,TResult}.cs` is the public abstract base every command shares:

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

It supplies every member documented on `VeloxCommand` (events, `EventContext`, status, lock/interrupt/clear, `ExecuteAndWaitAsync`, `Dispose`), plus typed helpers for subclasses:

| Member | Access | Purpose |
| --- | --- | --- |
| `CanExecuteCore(TParam)` | protected | the predicate plus the force-lock flag |
| `ExecuteAsyncCore(TParam)` | protected | start an execution, returning once accepted |
| `ExecuteAndWaitTypedAsync(TParam, CancellationToken)` | protected | await this execution and return `TResult` |
| `ExecuteAndWaitTyped(TParam)` | protected | blocking twin |
| `HandlerException` | public static | process-wide hook for throwing subscribers |

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

The stages mean exactly what they do on `IVeloxCommand`; only the payload differs. The implementation is explicit because a class cannot declare two public events with the same name.

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

`TypedParameter` performs the cast where the body is invoked, so a wrong argument that arrived through `ICommand.Execute` ends the execution as `Failed` instead of throwing at the call site.

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

The second example is the caveat in practice: the property is typed, but the inherited `object?` entry point still accepts the wrong type and only fails at run time.
