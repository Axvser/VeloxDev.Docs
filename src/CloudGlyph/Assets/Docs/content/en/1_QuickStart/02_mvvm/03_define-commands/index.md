# MVVM — Define Commands

`[VeloxCommand]` on a method generates a lazily created command property (or, for a generic method, a cached accessor) wrapping that method.

## 1. Attribute parameters

`[VeloxCommand(string name = "Auto", bool canValidate = false, int semaphore = 1)]` — declared in `Src/Core/VeloxDev.Core/MVVM/VeloxCommandAttribute.cs`.

| Parameter | Meaning |
| --- | --- |
| `name` | Command name. `"Auto"` (default) derives it from the method name by removing **every** `Async` substring: `Plus` → `PlusCommand`, `IncrementAsync` → `IncrementCommand`, `SumToAsync` → `SumToCommand`. Any other value is used verbatim, and `Command` is still appended. |
| `canValidate` | When `true`, the generated command uses a `private partial bool CanExecute{Name}Command(...)` predicate you must implement. When `false`, the emitted predicate is always true. |
| `semaphore` | Maximum concurrent executions. The writer stores `Math.Max(1, semaphore)`, so a generated command never has a capacity below 1. |

## 2. Accepted method signatures

The return type must be `Task`, `Task<T>`, `ValueTask`, `ValueTask<T>` or `void`. Leading parameters are optional, at most **15**, and may be followed by one trailing `CancellationToken`.

| Shape | Generated command |
| --- | --- |
| no leading parameter, `Task` / `ValueTask` / `void` | untyped `IVeloxCommand`, constructed with a `Task`- or `Action`-taking constructor |
| one `object?` parameter | untyped `IVeloxCommand`; the argument stays boxed |
| one parameter of another type `T` | `IVeloxCommand<T, TResult>`; the property and the pipeline carry `T` unboxed |
| two to fifteen leading parameters | `IVeloxCommand<T1, …, Tn, TResult>` from the arity family in `CommandArities.cs` |
| return type `Task<T>` / `ValueTask<T>` | `TResult` is `T`, and the value is handed back by `IVeloxCommandResult` / the typed `ExecuteAsync` overload |
| return type `Task` / `ValueTask` / `void` | `TResult` is `object?` and is always `null` |
| generic method `M<T>(T value) where T : …` | a cached accessor `IVeloxCommand<T, TResult> GetMCommand<T>()` — one command per closed `T`, each with its own queue and lock |

Only a `CancellationToken` parameter makes the body cancellable. Every other shape builds a command whose body never receives a token: an interrupted execution reports `Canceled`, but the body runs on to completion.

**Rejected shapes** report the error `VELOX_MVVM_CMD001` on the method's own line and are skipped; the rest of the class still generates:

| Rejected shape | Reason |
| --- | --- |
| `void M(CancellationToken ct)` | a synchronous body cannot observe the token |
| a generic method whose type parameters do not appear in its parameter types | the accessor has no type argument to carry |
| more than 15 leading parameters | the generated `Func` would exceed its type-argument limit; pass a record or tuple instead |
| a return type outside the accepted set | there is no way to turn it into a command |

**Expected result:** every accepted shape compiles to a non-null command; a rejected one fails the build with `VELOX_MVVM_CMD001` naming the method and the reason, and no member is emitted for it.

## 3. Generated members

For a plain untyped command the generated file contains:

```csharp
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_SaveCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand SaveCommand
{
    get
    {
        _buffer_SaveCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Save,
            canExecute: _ => true,
            semaphore: 1);
        return _buffer_SaveCommand;
    }
}
```

For `private Task Save(string name)` the property becomes `IVeloxCommand<string, object?>` and the getter uses `VeloxCommand<string, object?>.CreateTypedTaskOnlyWithParameter(...)`. For a method with several parameters it uses the matching arity constructor. The buffer field is created on first read and cached.

**Expected result:** `vm.SaveCommand` is non-null, has the documented type, and `CanExecute` reports `true` unless a predicate or the lock says otherwise.

## 4. Executability validation

```csharp
[VeloxCommand(canValidate: true)]
private Task Remove(NotePayload note)
{
    return Task.CompletedTask;
}

private partial bool CanExecuteRemoveCommand(NotePayload note)
    => note is not null && note.Weight > 0;
```

The validator's parameter list follows the source method's leading parameters: a method with no leading parameter gets `object? parameter`; otherwise the types and names are copied, and a mismatch is `CS8826`. The predicate is re-queried whenever `CanExecuteChanged` is raised, so call `{Name}Command.Notify()` after a change that can affect it. The demos do this from a property hook: `partial void OnIndexChanged(int oldValue, int newValue) { MinusCommand.Notify(); }`.

**Expected result:** a value that fails the predicate reports `CanExecute == false`; after `Notify()` it reports `true` and a bound button enables.

## 5. Commands are framework-agnostic

The command runtime references no UI type. Both demos bind `PlusCommand` / `MinusCommand` through `ICommand`, and a console host can call the same command.

**Expected result:** the same view-model binds unchanged in WPF and Avalonia; the console program on the last page calls these commands with no UI present.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `Writers/CommandWriter.cs`, `Diagnostics.cs`, `MVVM/VeloxCommand.cs`, `MVVM/CommandArities.cs`, `Base/AIContextNaming.cs`, `Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs` and `Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureTests.cs`.
