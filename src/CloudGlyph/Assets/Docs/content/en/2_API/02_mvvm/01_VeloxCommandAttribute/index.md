# MVVM — `VeloxCommandAttribute`

`VeloxDev.MVVM.VeloxCommandAttribute` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`) marks a method; the Command source generator exposes it as a lazily-created `IVeloxCommand` property on the containing class.

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
- **Targets:** `Method` only. `AllowMultiple = false`, `Inherited = false`.
- **Constructors:** the primary one; all three parameters are optional.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Name` | `string` | Command-property name. `"Auto"` (default) derives it from the method name. |
| `CanValidate` | `bool` | Whether executable validation is enabled for this command. Default `false`. |
| `Semaphore` | `int` | Maximum concurrent executions. Default `1`. |
| `AttributeUsage` | — | `AttributeTargets.Method`, `AllowMultiple = false`, `Inherited = false`. |

## Parameter semantics

| Parameter | Type | Description |
|---|---|---|
| `name` | `string` | The command property name. `"Auto"` derives it from the method name with **every** `Async` substring removed and `Command` appended: `Plus` → `PlusCommand`, `SaveAsync` → `SaveCommand`, `SumToAsync` → `SumToCommand`. Any other value is used verbatim (`name: "Add"` → `AddCommand`). |
| `canValidate` | `bool` | When `true`, the generator emits the property with `canExecute: CanExecute{Name}Command` and declares `private partial bool CanExecute{Name}Command(object? parameter)`, which the class must implement. When `false`, the emitted predicate is `_ => true`. |
| `semaphore` | `int` | Concurrency capacity. The writer stores `Math.Max(1, semaphore)` in the generated `VeloxCommand`, so the generated command's capacity is never below 1. Passing such a value to the `VeloxCommand` constructor directly *does* throw `ArgumentOutOfRangeException`. |

## Accepted method signatures

The annotated method's return type must be `Task`, `Task<T>`, `ValueTask`, `ValueTask<T>` or `void`, and its leading parameters may be zero or one, optionally followed by a trailing `CancellationToken`.

| Signature | Emitted construction |
|---|---|
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken` |
| `Task M(object? parameter, CancellationToken ct)` | primary constructor |
| `Task<T> M(...)` | as the matching `Task M(...)` row (the result is discarded) |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M()` | `() => M().AsTask()` thunk → `Func<Task>` |
| `ValueTask M(CancellationToken ct)` | `ct => M(ct).AsTask()` thunk → `CreateTaskOnlyWithCancellationToken` |
| `ValueTask<T> M(...)` | as the matching `ValueTask M(...)` row |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | cast thunk `parameter => M((T)parameter!)` (plus `.AsTask()` for `ValueTask`) |

### Rejected signatures — `VELOXCMD001`

| Signature | Diagnostic message fragment |
|---|---|
| `void M(CancellationToken ct)` | `void` — nothing a synchronous body could observe |
| generic method `M<T>(...)` | `generic` |
| more than one leading parameter | `more than one parameter` |
| a return type outside the accepted set | `it returns '…'` |

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

`PlusCommand` is built with `canExecute: _ => true`; `MinusCommand` with `canExecute: CanExecuteMinusCommand`. Both are lazy — the command object does not exist until something reads the property.

**Notes:**

- The derived property name is `{Name}Command`; `Name` comes from the `name` argument or from the auto rule.
- Call `{Name}Command.Notify()` after a change that may affect `CanExecute{Name}Command` so `CanExecuteChanged` is raised. The WPF demo does this from `partial void OnIndexChanged(...)`.
- Only a `CancellationToken` parameter lets the command actually stop the body. The other shapes build a command whose body never receives a token, so an interrupted execution reports `Canceled` while the body runs on to completion.
- The generated property is typed `IVeloxCommand`, not `VeloxCommand`; the extra capabilities (`ExecuteAndWaitAsync`, `IsBusy`, …) are reached through `VeloxCommandExtensions`.
