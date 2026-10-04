# MVVM — Define Commands

`[VeloxCommand]` on a method generates a lazily created `IVeloxCommand` property wrapping that method. The command implements `System.Windows.Input.ICommand`, so it binds in XAML exactly like a framework command.

## 1. Attribute parameters

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]` — full signature in `Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`:

| Parameter | Meaning |
|---|---|
| `name` | Command-property name. `"Auto"` (default) derives it from the method name with **every** `Async` substring removed: `Plus` → `PlusCommand`, `IncrementAsync` → `IncrementCommand`, `SumToAsync` → `SumToCommand`. A custom string is used verbatim (`name: "Add"` → `AddCommand`). |
| `canValidate` | When `true`, the property is built with `canExecute: CanExecute{Name}Command`, and the generator declares `private partial bool CanExecute{Name}Command(object? parameter)` for you to implement. When `false`, the emitted predicate is `_ => true`. |
| `semaphore` | Maximum concurrent executions. The writer stores `Math.Max(1, semaphore)`, so the generated command never has a capacity below 1. |

## 2. Accepted method signatures

The writer decides two things separately: the **return type** decides how the value becomes a `Task`, and the **parameter list** decides which constructor or factory is used. Leading parameters may be zero or one, optionally followed by a trailing `CancellationToken`.

| Method shape | Resolved construction |
|---|---|
| `Task M()` | `VeloxCommand(Func<Task>)` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter(Func<object?, Task>)` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(Func<CancellationToken, Task>)` |
| `Task M(object? parameter, CancellationToken ct)` | primary constructor (`Func<object?, CancellationToken, Task>`) |
| `Task<T> M(...)` | same as the matching `Task M(...)` row — the `T` is discarded |
| `void M()` / `void M(object? parameter)` | `VeloxCommand(Action)` / `VeloxCommand(Action<object?>)` |
| `ValueTask M()` | `() => M().AsTask()` thunk → `VeloxCommand(Func<Task>)` |
| `ValueTask M(CancellationToken ct)` | `ct => M(ct).AsTask()` thunk → `CreateTaskOnlyWithCancellationToken` |
| `ValueTask<T> M(...)` | same as the matching `ValueTask M(...)` row |
| `Task M(T value)` / `ValueTask M(T value)` / `void M(T value)` | thunk casts the parameter: `parameter => M((T)parameter!)` (plus `.AsTask()` for `ValueTask`) |

**Rejected shapes** raise the generator diagnostic **`VELOXCMD001`** (`Src/Generators/VeloxDev.Core.Generator/Diagnostics.cs`), an *error*, and the method is skipped — the rest of the class still generates:

| Rejected shape | Why |
|---|---|
| `void M(CancellationToken ct)` | nothing a synchronous body can observe; return `Task` to be cancellable |
| a generic method `M<T>(...)` | the generated method group cannot infer its type arguments from one `object?` argument (a generic *class* is fine) |
| more than one parameter before the trailing token | a command carries a single argument; take a record or tuple instead |
| a return type that is not `Task`, `Task<T>`, `ValueTask`, `ValueTask<T>` or `void` | no way to turn it into a command |

**Expected result:** every accepted shape compiles and produces a non-null command property; a rejected one fails the build with `VELOXCMD001` naming the method and the reason, and no `{Name}Command` property is emitted for it.

## 3. Minimal command and its generated code

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxCommand]
    private Task Increment(object? parameter, CancellationToken ct)
    {
        Count++;
        return Task.CompletedTask;
    }
}
```

The real generated property (one file per class, `{ClassName}_{Namespace}_Commands.g.cs`) is:

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_IncrementCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand IncrementCommand
{
    get
    {
        _buffer_IncrementCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Increment,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_IncrementCommand;
    }
}
```

The property is created on first access and cached in `_buffer_IncrementCommand`.

A `ValueTask` body with a single typed parameter resolves to a conversion thunk instead of a method group — no `ValueTask` overload of `VeloxCommand` is needed at run time, so the same generated code works on every supported target framework:

```csharp
[VeloxCommand]
private async ValueTask<int> SumToAsync(int limit)
{
    await Task.Yield();
    var total = 0;
    for (var i = 1; i <= limit; i++)
    {
        total += i;
    }

    return total;
}
```

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_SumToCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand SumToCommand
{
    get
    {
        _buffer_SumToCommand ??= global::VeloxDev.MVVM.VeloxCommand.CreateTaskOnlyWithParameter(
            command: parameter => SumToAsync((int)parameter!).AsTask(),
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_SumToCommand;
    }
}
```

**Expected result:** `vm.IncrementCommand` is non-null and `CanExecute(null)` is `true`; `vm.SumToCommand.Execute(10)` reaches `SumToAsync` with `limit == 10`. The cast in the thunk is a run-time cast — passing the wrong type makes the execution fail with an `InvalidCastException` (`CommandOutcome.Failed`) rather than silently doing nothing.

## 4. Executability validation (`canValidate: true`)

With validation enabled the generator declares a `partial` predicate you must implement — omitting it is a compile error, not a command that is silently always executable:

```csharp
[VeloxCommand(canValidate: true)]
private Task Decrement(object? parameter, CancellationToken ct)
{
    Count--;
    return Task.CompletedTask;
}

private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
```

The predicate is re-queried whenever `CanExecuteChanged` is raised, so call `{Name}Command.Notify()` after any change that affects it. The WPF demo does exactly that from a property hook: `partial void OnIndexChanged(int oldValue, int newValue) { MinusCommand.Notify(); }`.

**Expected result:** while `Count == 0`, `DecrementCommand.CanExecute(null)` is `false` and a bound button is disabled; once `Count > 0` and `DecrementCommand.Notify()` runs, `CanExecute(null)` is `true` and the button enables.

## 5. Commands are framework-agnostic

The command runtime is a plain class — no UI type is referenced. Both demos bind `PlusCommand` / `MinusCommand` straight through the .NET `ICommand` contract, and a console host can call the same command.

**Expected result:** the same view-model class binds unchanged in WPF and Avalonia; the complete-code program on the last page calls `ExecuteAndWaitAsync` on these commands with no UI present.

## Run declaration

- ✅ Actually built and run on 2026-10-01. The two generated snippets in section 3 are verbatim from `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs`, produced by `dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true` in a scratch console project that project-references `VeloxDev.Core` and `VeloxDev.Core.Generator`. Two commands from that build were also executed; recorded output:

  ```text
  Increment -> Completed (Succeeded=True)
  SumTo(10) -> Completed
  ```

- The rejection matrix in section 2 was not re-run in this pass. It is transcribed from `CommandWriter.TryBuildCommandExpression` and `Diagnostics.UnsupportedCommandSignature`, and is exercised by `Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs` (which drives the generator directly and asserts the `VELOXCMD001` id and message fragments).
