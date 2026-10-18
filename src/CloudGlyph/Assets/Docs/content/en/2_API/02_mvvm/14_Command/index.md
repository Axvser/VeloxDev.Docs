# MVVM — Command generator

`VeloxDev.Generators.Command` is the Roslyn incremental generator that exposes `[VeloxCommand]` methods as lazily created command properties (or generic accessors). Sources: `Src/Generators/VeloxDev.Core.Generator/Command.cs`, `Writers/CommandWriter.cs`, `Diagnostics.cs`.

## Class: `Command`

**Signature**

```csharp
[Generator(LanguageNames.CSharp)]
public class Command : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(
            Analizer.Filters.Targets(context).Combine(context.CompilationProvider),
            GenerateSource);
    }

    public void GenerateSource(SourceProductionContext context, (ImmutableArray<Analizer.Filters.GeneratorTarget> Targets, Compilation Compilation) input)
    {
        foreach (var (syntax, symbol) in Analizer.Filters.Resolve(input.Targets, input.Compilation))
        {
            var writer = new CommandWriter();
            writer.Initialize(syntax, symbol);

            foreach (var diagnostic in writer.Diagnostics)
            {
                context.ReportDiagnostic(diagnostic);
            }

            if (writer.CanWrite())
            {
                context.AddSource(
                    writer.GetFileName(),
                    SourceText.From(writer.Write(), Encoding.UTF8));
            }
        }
    }
}
```

## Pipeline

1. `Analizer.Filters.Targets` streams every class carrying `VeloxDev.MVVM.VeloxCommandAttribute`.
2. `Analizer.Filters.Resolve` re-resolves the symbol against the current compilation.
3. `CommandWriter.ReadCommandConfig` scans the class's methods and builds a `CommandSpec` per `[VeloxCommand]` method.
4. Diagnostics are reported **before** anything is emitted.
5. `CanWrite` is `CommandConfig.Count > 0`; the file name is `{ClassName}_{Namespace_With_Underscores}_Commands.g.cs`.

## Per-method resolution

`ReadCommandConfig` reads the attribute arguments — positional first, then named-argument overrides:

| Argument | Effect |
| --- | --- |
| `name` | `"Auto"` derives the name from `method.Name.Replace("Async", "")`; every `Async` substring is removed. The member is `{name}Command`. |
| `canValidate` | Emits `canExecute: CanExecute{name}Command` and declares the matching `private partial bool`. |
| `semaphore` | Stored as `Math.Max(1, semaphore)`. |

`BuildSpec` then decides the shape from two independent facts — the return type decides how the value becomes a `Task`, and the leading parameter list decides the construction and whether the property is typed:

| Return type | Leading parameters | Result |
| --- | --- | --- |
| `void` | 0 | `VeloxCommand(Action)` |
| `void` | 1 `object?` | `VeloxCommand(Action<object?>)` |
| `void` | 1 typed | typed command (`IVeloxCommand<T, object?>`) |
| `Task` / `Task<T>` | 0 | `VeloxCommand(Func<Task>)`, or a result-channel factory for `Task<T>` |
| `Task` / `Task<T>` | 1 `object?` | primary constructor or `CreateTaskOnlyWithParameter`; result channel for `Task<T>` |
| `Task` / `Task<T>` | 1 typed | typed constructor/factory; result channel keeps `TResult` |
| `Task` / `Task<T>` | 2–15 typed | arity family `VeloxCommand<T1, …, Tn, TResult>` |
| `ValueTask` / `ValueTask<T>` | any | `.AsTask()` thunk; typed shapes keep the result channel |
| any | trailing `CancellationToken` | the token is passed to the body, making the run cancellable |
| `Task<T>` | generic method `M<T>(T value)` | accessor `GetMCommand<T>()`, one cached command per closed `T` |

`ValueTask` needs the thunk because it has no implicit conversion to `Task` and is a struct, so it cannot use delegate covariance. Producing a `Func<...>` keeps the generated code independent of the runtime's `ValueTask` entry points.

## Diagnostic `VELOX_MVVM_CMD001`

**Signature**

```csharp
public static readonly DiagnosticDescriptor UnsupportedCommandSignature = new(
    id: "VELOX_MVVM_CMD001",
    title: "Unsupported [VeloxCommand] signature",
    messageFormat: "'{0}' cannot be turned into a command: {1}",
    category: "VeloxDev.MVVM",
    defaultSeverity: DiagnosticSeverity.Error,
    isEnabledByDefault: true);
```

It is an **error**: the generated file would not have compiled anyway. Without it, an unsupported shape surfaced as `CS1503` / `CS0407` inside `*_Commands.g.cs`.

| Rejected shape | Reason text (fragments) |
| --- | --- |
| a generic method whose type parameters miss its parameter type | `generic method whose type parameters do not appear in its parameter type` |
| an unsupported return type | `a command body must return Task, Task<T>, ValueTask, ValueTask<T> or void` |
| more than 15 leading parameters | `the generated command carries at most 15` |
| `void` with a `CancellationToken` | `nothing in a synchronous body can observe` |

A refused method is **skipped** and the rest of the class still generates.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs
var (diagnostics, generated) = Run("""
    private Task Good(object? p) { _ = p; return Task.CompletedTask; }
    private void Bad(CancellationToken ct) { _ = ct; }
    """);

Assert.HasCount(1, diagnostics, Describe(diagnostics));
StringAssert.Contains(generated, "GoodCommand");
Assert.DoesNotContain("BadCommand", generated);
```

```csharp
// Source: generated — the canValidate template
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_DecrementCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand DecrementCommand
{
    get
    {
        _buffer_DecrementCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Decrement,
            canExecute: CanExecuteDecrementCommand,
            semaphore: 1);
        return _buffer_DecrementCommand;
    }
}
private partial bool CanExecuteDecrementCommand(object? parameter);
```

For a typed parameter the two key lines are:

```csharp
// Source: Test — CommandSignatureDiagnosticsTests.cs (asserted output)
// public IVeloxCommand<global::System.String, global::System.Object?> MCommand { ... }
// ... CreateTypedTaskOnlyWithParameter<global::System.String>(command: M, ...)
```

## Notes

- A generated property is typed `IVeloxCommand` or `IVeloxCommand<TParam, TResult>`; extra capabilities are reached through `VeloxCommandExtensions` or the typed interface.
- Both generators share `Analizer.Filters.Targets`; a class with only `[VeloxProperty]` members yields nothing here.
- The user-facing contract is the attribute, on the `01_VeloxCommandAttribute` page.
