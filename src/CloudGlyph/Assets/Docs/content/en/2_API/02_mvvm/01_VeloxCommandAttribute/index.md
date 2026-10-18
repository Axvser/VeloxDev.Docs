# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`) marks a method; `VeloxDev.Generators.Command` exposes it as a lazily created command property (or a generic accessor).

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

- **Base type:** `System.Attribute`. `sealed`.
- **Target:** `Method` only. `AllowMultiple = false`, `Inherited = false`.
- **Constructors:** the primary one; all three parameters are optional.

##### Properties

| Name | Type | Description |
| --- | --- | --- |
| `Name` | `string` | Command name. `"Auto"` derives it from the method name. |
| `CanValidate` | `bool` | Whether executability validation is enabled. Default `false`. |
| `Semaphore` | `int` | Maximum concurrent executions. Default `1`. |

## Parameter semantics

| Parameter | Type | Description |
| --- | --- | --- |
| `name` | `string` | The command name. `"Auto"` removes **every** `Async` substring from the method name, then appends `Command`: `Plus` → `PlusCommand`, `SaveAsync` → `SaveCommand`, `SumToAsync` → `SumToCommand`. Any other value is used verbatim (`name: "Add"` → `AddCommand`). |
| `canValidate` | `bool` | When `true`, the generated command uses `CanExecute{Name}Command`, and the generator declares it as a `private partial bool`. Following the source method, it takes `object? parameter` when there is no leading parameter, or else the source's leading parameter types and names. When `false`, the emitted predicate is always true. |
| `semaphore` | `int` | Concurrency capacity. The writer stores `Math.Max(1, semaphore)`, so a generated command never has a capacity below 1. Passing a smaller value to the `VeloxCommand` constructor directly *does* throw `ArgumentOutOfRangeException`. |

## Accepted method signatures

The return type must be `Task`, `Task<T>`, `ValueTask`, `ValueTask<T>` or `void`. Leading parameters are optional, at most **15**, and may be followed by a trailing `CancellationToken`.

| Signature | Emitted construction |
| --- | --- |
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` |
| `Task M(object? parameter, CancellationToken ct)` | primary constructor |
| `Task<T> M(...)` | a result-channel construction (`CreateTaskWithResult` / `CreateTaskOnlyWithResult`) when untyped; `VeloxCommand<T, TResult>` when typed |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M(...)` | `.AsTask()` thunk → `Func<...>` |
| `ValueTask<T> M(...)` | `.AsTask()` thunk with a result channel |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | typed command: `IVeloxCommand<T, TResult>`; the property getter uses a typed constructor/factory |
| `M(T1 a, T2 b, ...)` | typed arity command: `IVeloxCommand<T1, T2, ..., TResult>` |
| `Task M<T>(T value) where T : ...` | cached accessor `IVeloxCommand<T, TResult> GetMCommand<T>()`; one command per closed `T` |

For `Task<T>` / `ValueTask<T>`, `TResult` is `T`; for the other return types, `TResult` is `object?` and is always `null`.

### Rejected signatures — `VELOX_MVVM_CMD001`

| Signature | Why |
| --- | --- |
| `void M(CancellationToken ct)` | nothing a synchronous body could observe |
| a generic method whose type parameters do not appear in its parameter types | the accessor has no type argument to carry |
| more than 15 leading parameters | the generated `Func` would exceed its type-argument limit |
| a return type outside the accepted set | no way to turn it into a command |

A refused method is skipped; the rest of the class still generates.

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 64-84
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

`PlusCommand` is built with an always-true predicate; `MinusCommand` with `CanExecuteMinusCommand`. Both are lazy — the command object does not exist until something reads the property.

**Notes:**

- The derived member name is `{Name}Command`; `Name` comes from the `name` argument or the auto rule.
- Call `{Name}Command.Notify()` after a change that may affect the validator. The WPF demo does this from `partial void OnIndexChanged(...)`.
- Only a `CancellationToken` parameter lets the command stop the body. Other shapes report `Canceled` on interrupt while the body runs to completion.
- A generated property is typed `IVeloxCommand` or `IVeloxCommand<TParam, TResult>`; extra capabilities are reached through `VeloxCommandExtensions` or the typed interface.
