# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`) marks a method; the Command source generator exposes it as a lazily-created `IVeloxCommand` property on the containing class.

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

| Parameter | Meaning |
|---|---|
| `name` | Command property name. `"Auto"` (default) derives it from the method name with every `Async` substring removed, then appends `Command` — `Plus` → `PlusCommand`, `SaveAsync` → `SaveCommand`. |
| `canValidate` | When `true`, the generator emits `private partial bool CanExecute{Name}Command(object? parameter)`, which the class must implement. |
| `semaphore` | Maximum concurrent executions (effective value `Math.Max(1, semaphore)`); default `1` = serial execution with queueing. |

## Accepted method signatures

From the attribute XML documentation, the annotated method must match one of these shapes (return `Task` or `void`):

- `Task M(object? parameter, CancellationToken ct)`
- `Task M(object? parameter)`
- `Task M(CancellationToken ct)`
- `Task M()`
- `void M(object? parameter)`
- `void M()`

## Factory selection (`CommandWriter.ParseConstructorType`)

| Signature | Selected constructor / factory |
|---|---|
| `Task M(object?, CancellationToken)` | primary constructor — delegate `Func<object?, CancellationToken, Task>` |
| `Task M(object?)` | `VeloxCommand.CreateTaskOnlyWithParameter` — delegate `Func<object?, Task>` |
| `Task M(CancellationToken)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` — delegate `Func<CancellationToken, Task>` |
| `Task M()` | `Func<Task>` constructor |
| `void M(object?)` | `Action<object?>` constructor |
| `void M()` | `Action` constructor |

The generator selects only the factory; which `VeloxCommand` constructor the remaining method groups bind to is resolved by C# overload resolution. See [VeloxCommand](../03_VeloxCommand/index.md) for the full constructor/factory list.

## `canValidate` naming contract (Demo-verified)

For `canValidate: true`, the emitted property uses the generated `partial` method as its `canExecute` predicate, so the class must implement `private partial bool CanExecute{Name}Command(object? parameter)`. Call `{Name}Command.Notify()` whenever the predicate result may change so `CanExecuteChanged` is raised.

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 70-81:

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

The derived property name is `MinusCommand` (method name `Minus`, no `Async` suffix to strip). For `canValidate: false` the emitted `canExecute` predicate is `_ => true`.

## Lifecycle semantics

Each generated command queues excess executions once the `semaphore` capacity is reached and raises the `IVeloxCommand` lifecycle events (`Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`) — see [IVeloxCommand](../02_IVeloxCommand/index.md). Cancelling the running method is only possible for signatures that receive a `CancellationToken` (`Task M(object?, CancellationToken)` / `Task M(CancellationToken)`); see the cancellation note in [VeloxCommand](../03_VeloxCommand/index.md).
