# MVVM — Define Commands

`[VeloxCommand]` on a method generates a lazily created `IVeloxCommand` property that wraps the method. The command implements `System.Windows.Input.ICommand`, so it binds in XAML exactly like a framework command.

## 1. Attribute parameters

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`):

| Parameter | Meaning |
|---|---|
| `name` | Command-property suffix. `"Auto"` (default) derives it from the method name, stripping a trailing `Async`: `IncrementAsync` → `IncrementCommand`, `Plus` → `PlusCommand`. A custom string `name` is used verbatim (`name: "Add"` → `AddCommand`). |
| `canValidate` | When `true`, requires a `Can<Name>Command` predicate (see below). |
| `semaphore` | Max concurrent executions (≥ 1, default `1` = serial). Values > 1 let several instances run in parallel. |

## 2. Method signature forms

Any of these shapes is accepted (`VeloxCommandAttribute.cs` XML docs; the generator resolves the matching `VeloxCommand` constructor / factory at compile time):

| Method | Resolved command delegate |
|---|---|
| `Task M(object? parameter, CancellationToken ct)` | primary ctor — per-run `CancellationToken` |
| `Task M(object? parameter)` | `VeloxCommand.CreateTaskOnlyWithParameter(...)` |
| `Task M(CancellationToken ct)` | `VeloxCommand.CreateTaskOnlyWithCancellationToken(...)` |
| `Task M()` | `Func<Task>` ctor |
| `void M(object? parameter)` | `Action<object?>` ctor |
| `void M()` | `Action` ctor |

The object parameter is the command parameter (from `Execute(parameter)` or the binding's `CommandParameter`); the `CancellationToken` form gives the method body its per-execution token (see the concurrency page).

## 3. Minimal command

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

Generated (per class, in `{ClassName}_{Namespace}_Commands.g.cs`):

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_IncrementCommand = null;

public VeloxDev.MVVM.IVeloxCommand IncrementCommand
{
    get
    {
        _buffer_IncrementCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Increment,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_IncrementCommand;
    }
}
```

The `IVeloxCommand` property is created on first access and cached in `_buffer_IncrementCommand`.

**Expected result:** `vm.IncrementCommand` is non-null and `CanExecute(null)` returns `true`. In XAML `Command="{Binding IncrementCommand}"` triggers the method; in code call `vm.IncrementCommand.Execute(null)` (fire-and-forget) or `await vm.IncrementCommand.ExecuteAsync(null)`.

## 4. Executability validation (`canValidate: true`)

With validation enabled the generator declares a predicate partial you must implement:

```csharp
[VeloxCommand(canValidate: true)]
private Task Decrement(object? parameter, CancellationToken ct)
{
    Count--;
    return Task.CompletedTask;
}

private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
```

Generated getter then passes `canExecute: CanExecuteDecrementCommand`. The predicate is re-queried whenever `CanExecuteChanged` is raised — call `SomeCommand.Notify()` (or the command's own refresh triggers) after a change that affects it. The WPF demo does this from the property hook: `partial void OnIndexChanged(...) { MinusCommand.Notify(); }`.

**Expected result:** while `Count == 0`, `DecrementCommand.CanExecute(null)` is `false` and a bound button is disabled; after `Count` becomes `> 0` and `DecrementCommand.Notify()` runs, `CanExecute(null)` returns `true` and the button enables.

## 5. Commands are framework-agnostic

The command runtime (`VeloxDev.MVVM.VeloxCommand`, constructors plus the `CreateTaskOnlyWithParameter` / `CreateTaskOnlyWithCancellationToken` factories) is a plain class — no UI type is referenced. The WPF demo buttons (`Examples/MVVM/WPF/Demo/MainWindow.xaml`) and the Avalonia demo bind `PlusCommand` / `MinusCommand` directly through the .NET `ICommand` contract.

**Expected result:** the same view-model class binds unchanged in WPF and Avalonia; a console host can call the command too (the complete-code page does).

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. The generated command-property shape is transcribed from `Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs` (`GenerateCommand`); method-form support comes from the attribute's XML docs and the generator's `ParseConstructorType`; the demo wiring comes from `Examples/MVVM/*`.
