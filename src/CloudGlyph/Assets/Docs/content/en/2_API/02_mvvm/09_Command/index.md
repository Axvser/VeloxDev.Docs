# MVVM — Command generator

`VeloxDev.Generators.Command` is the Roslyn source generator that exposes methods annotated with `[VeloxCommand]` as lazily-created `IVeloxCommand` properties. Sources: `Src/Generators/VeloxDev.Core.Generator/Command.cs`, `Writers/CommandWriter.cs`.

```csharp
[Generator(LanguageNames.CSharp)]
public class Command : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(Analizer.Filters.FilterContext(context), GenerateSource);
    }
}
```

The generator ships in the analyzer package `VeloxDev.Core.Generator` (version `9.0.0`, `netstandard2.0`), referenced transitively by `VeloxDev.Core` — the same package that carries the MVVM generator (see [MVVM](../08_MVVM/index.md)).

## Pipeline

1. `Analizer.Filters.FilterContext` collects every `partial` class declaration.
2. `CommandWriter.ReadCommandConfig` scans the class methods for `[VeloxCommand]`.
3. `CanWrite` is true when at least one method carries the attribute; each such class then gets one source file `{ClassName}_{Namespace}_Commands.g.cs` (namespace dots replaced by `_`).

## Per-method resolution (`CommandWriter`)

For each annotated method the writer resolves:

- `name` — positional first, named arguments override. `"Auto"` (default) derives the command name from the method name by removing every `Async` substring; the generated property is `{name}Command`.
- `canValidate` — when `true`, the emitted property uses `canExecute: CanExecute{name}Command` and the generator declares `private partial bool CanExecute{name}Command(object? parameter)`, which the class must implement. When `false`, `canExecute: _ => true` is used.
- `semaphore` — positional first, named overrides; effective capacity is `Math.Max(1, semaphore)`.

The method signature selects which `VeloxCommand` entry point to call (`ParseConstructorType`):

| Signature | Emitted factory |
|---|---|
| `Task M(object?, CancellationToken)` | primary constructor — delegate `Func<object?, CancellationToken, Task>` |
| `Task M(object?)` | `CreateTaskOnlyWithParameter` — delegate `Func<object?, Task>` |
| `Task M(CancellationToken)` | `CreateTaskOnlyWithCancellationToken` — delegate `Func<CancellationToken, Task>` |
| `Task M()`, `void M(object?)`, `void M()` | a matching `VeloxCommand` constructor (`Func<Task>` / `Action<object?>` / `Action`) |

## Emitted shape

For each method the writer emits a backing field and a lazy property:

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_MinusCommand = null;
public VeloxDev.MVVM.IVeloxCommand MinusCommand
{
    get
    {
        _buffer_MinusCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Minus,
            canExecute: CanExecuteMinusCommand,
            semaphore: 1);
        return _buffer_MinusCommand;
    }
}
private partial bool CanExecuteMinusCommand(object? parameter);
```

The example above is the `canValidate: true` template applied to the `Minus` method of `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`. The user-facing contract is the attribute, documented in [VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md); the runtime type is [VeloxCommand](../03_VeloxCommand/index.md).
