# MVVM — `VeloxCommandAttribute`

Marks a method to be wrapped as an `IVeloxCommand`.

**Signature** (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`, lines 34-43):

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
| `name` | Command property name. `"Auto"` (default) derives it from the method name and strips a trailing `Async` suffix (`Plus` → `PlusCommand`, `IncrementAsync` → `IncrementCommand`) — `CommandWriter.cs`, lines 63-67. |
| `canValidate` | When `true`, a `private partial bool CanXxxCommand(object? parameter)` must be implemented. |
| `semaphore` | Max concurrent executions (must be >= 1); default `1` = serial with queueing. |

**Accepted method signatures** (attribute XML docs, lines 10-18): `Task M(object?, CancellationToken)`, `Task M(object?)`, `Task M(CancellationToken)`, `Task M()`, `void M(object?)`, `void M()`.

**Factory mapping** (`CommandWriter.ParseConstructorType`, lines 78-116):

| Signature | Generated factory |
|---|---|
| `Task M(object?, CancellationToken)` | `new VeloxCommand(command: M, ...)` (primary ctor) |
| `Task M(object?)` | `VeloxCommand.CreateTaskOnlyWithParameter(command: M, ...)` |
| `Task M(CancellationToken)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(command: M, ...)` |
| `Task M()` | `new VeloxCommand(command: M, ...)` (binds the `Func<Task>` ctor) |
| `void M(object?)` | `new VeloxCommand(command: M, ...)` (binds the `Action<object?>` ctor) |
| `void M()` | `new VeloxCommand(command: M, ...)` (binds the `Action` ctor) |

- **Example:** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 64-84 — `[VeloxCommand(canValidate: true)] private Task Minus(object? sender, CancellationToken ct)`.
