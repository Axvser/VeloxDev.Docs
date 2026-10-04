# MVVM — Command generator

`VeloxDev.Generators.Command` is the Roslyn incremental generator that exposes methods annotated with `[VeloxCommand]` as lazily-created `IVeloxCommand` properties. Sources: `Src/Generators/VeloxDev.Core.Generator/Command.cs`, `Writers/CommandWriter.cs`, `Diagnostics.cs`.

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

            // report diagnostics first: an unsupported signature never reaches the generated file
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

1. `Analizer.Filters.Targets` (`Base/Analizer.cs`, line 107) streams every class carrying `VeloxDev.MVVM.VeloxCommandAttribute` (one of `TriggerAttributes`, line 82), once per type.
2. `Analizer.Filters.Resolve` (line 142) re-resolves the symbol against the current compilation.
3. `CommandWriter.ReadCommandConfig` (`Writers/CommandWriter.cs`, line 43) scans the class methods for `[VeloxCommand]` and builds a `CommandSpec` per method.
4. Diagnostics collected in `CommandWriter.Diagnostics` are reported **before** anything is emitted, so a refusal lands on the author's own line.
5. `CanWrite` (line 243) is `CommandConfig.Count > 0`; the file name is `{ClassName}_{Namespace_With_Underscores}_Commands.g.cs`.

## Per-method resolution

`ReadCommandConfig` resolves the attribute arguments — positional first, then named-argument overrides:

| Attribute argument | Effect |
|---|---|
| `name` | Positional first, named overrides. `"Auto"` derives the command name from `methodSymbol.Name.Replace("Async", "")`, so *every* `Async` substring is removed, not just a suffix. The generated property is `{name}Command`. |
| `canValidate` | When `true`, the emitted property uses `canExecute: CanExecute{name}Command` and the generator declares `private partial bool CanExecute{name}Command(object? parameter)`. When `false`, the emitted predicate is `_ => true`. |
| `semaphore` | Positional first, named overrides; stored as `Math.Max(1, semaphore)`. |

`TryBuildCommandExpression` (line 133) then decides how the method becomes a command. Return type and parameter list are judged separately:

| Return type | Leading parameters | Emitted expression and construction |
|---|---|---|
| `void` | 0 | the method group, `new VeloxCommand(command: M, …)` → `Action` |
| `void` | 1 (`object?`) | the method group → `Action<object?>` |
| `void` | 1 (typed) | `parameter => M((T)parameter!)` → `Action<object?>` |
| `Task` / `Task<T>` | 0 | method group → `Func<Task>`, or `CreateTaskOnlyWithCancellationToken` when a token follows |
| `Task` / `Task<T>` | 1 (`object?`) | method group → primary ctor (with token) or `CreateTaskOnlyWithParameter` |
| `Task` / `Task<T>` | 1 (typed) | `(parameter, ct) => M((T)parameter!, ct)` or `parameter => M((T)parameter!)` as above |
| `ValueTask` / `ValueTask<T>` | 0 | `() => M().AsTask()` or `ct => M(ct).AsTask()` |
| `ValueTask` / `ValueTask<T>` | 1 | `parameter => M((T)parameter!).AsTask()` or `(parameter, ct) => M((T)parameter!, ct).AsTask()` |

`ValueTask` needs the thunk because it has no implicit conversion to `Task` and is a struct, so it cannot hitch a ride on delegate covariance. Producing a `Func<object?, CancellationToken, Task>` — which exists on all four TFMs — keeps the generated code independent of the runtime's `ValueTask` entry points.

## Diagnostic `VELOXCMD001`

**Signature**

```csharp
public static readonly DiagnosticDescriptor UnsupportedCommandSignature = new(
    id: "VELOXCMD001",
    title: "Unsupported [VeloxCommand] signature",
    messageFormat: "'{0}' cannot be turned into a command: {1}",
    category: "VeloxDev.MVVM",
    defaultSeverity: DiagnosticSeverity.Error,
    isEnabledByDefault: true);
```

Declared on `VeloxDev.Generators.Diagnostics.UnsupportedCommandSignature` (`Src/Generators/VeloxDev.Core.Generator/Diagnostics.cs`). It is an **error**, not a warning: the generated file would not have compiled anyway, so the only question is which message the author gets. Without it, an unsupported shape surfaced as `CS1503` / `CS0407` inside `*_Commands.g.cs`, naming a method group and a constructor the author never wrote.

| Rejected shape | Reason text |
|---|---|
| generic method | `it is a generic method; the generated command cannot infer its type arguments from a single object? argument…` |
| unsupported return type | `it returns '…', but a command body must return Task, Task<T>, ValueTask, ValueTask<T> or void` |
| more than one leading parameter | `it takes more than one parameter before the optional CancellationToken, and a command carries a single argument…` |
| `void` with a `CancellationToken` | `it returns void and takes a CancellationToken, which nothing in a synchronous body can observe…` |

A refused method is **skipped** and the rest of the class still generates.

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs, lines 89-99
var (diagnostics, generated) = Run("""
    private Task Good(object? p) { _ = p; return Task.CompletedTask; }
    private void Bad(CancellationToken ct) { _ = ct; }
    """);

Assert.HasCount(1, diagnostics, Describe(diagnostics));
StringAssert.Contains(generated, "GoodCommand", "one bad method must not take the good one down with it");
Assert.DoesNotContain("BadCommand", generated);
```

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs
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

## Notes

- The generated property's type is `IVeloxCommand`, so its extra capabilities are reached through `VeloxCommandExtensions`.
- Both generators share `Analizer.Filters.Targets`; a class with only `[VeloxProperty]` members yields nothing here.
- The generated snippet above is the `canValidate: true` template applied to the `Decrement` method of the Quick Start complete-code program; the same template produces `MinusCommand` for `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`. The user-facing contract is the attribute, on the `01_VeloxCommandAttribute` page; the runtime type is `VeloxCommand`.
