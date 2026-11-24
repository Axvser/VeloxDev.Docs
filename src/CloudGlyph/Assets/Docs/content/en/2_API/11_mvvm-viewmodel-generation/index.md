# MVVM ViewModel Generation

The `VeloxDev.MVVM` namespace and the `VeloxDev.Core.Generator` analyzer. Two attributes drive the generator: `[VeloxProperty]` turns a field or partial property into a notifying property, and `[VeloxCommand]` turns a method into an `IVeloxCommand`. The runtime types that back a generated command — the bounded, queued, cancellable pipeline — live in the same namespace and are usable directly, without the generator.

The generator runs at compile time. A NuGet reference to `VeloxDev.Core` carries it; a `ProjectReference` needs it added separately as an analyzer.

## Type groups

| Group | Types | Page |
|---|---|---|
| Attributes and generated members | `VeloxPropertyAttribute`, `VeloxCommandAttribute`, generated properties, commands and collection hooks, `ObservableCollectionTracker` | [Attributes and generated members](00_attributes-and-generated-members/index.md) |
| Command runtime | `CommandPipeline<TParam, TResult>`, `VeloxCommand`, `VeloxCommand<TParam, TResult>`, the 2–15 argument command family, `CommandOutcome`, `CommandCompletion`, `CommandEventArgs`, `CommandEventType` | [Command runtime](01_command-runtime/index.md) |
| Command interfaces and extensions | `IVeloxCommand`, `IVeloxCommand<TParam, TResult>`, `IVeloxCommandStatus`, `IVeloxCommandResult`, `IVeloxCommandCompletion`, `IVeloxCommandEvents<TParam, TResult>`, `VeloxCommandExtensions` | [Command interfaces](02_command-interfaces/index.md) |

## Setup

Nothing needs registering. Mark the class `partial`, add the attributes, and build; the generated members appear as ordinary C# in `*_MVVM.g.cs` and `*_Commands.g.cs` files under `obj/` when `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` is set. See [MVVM ViewModel Generation quick start](../../1_QuickStart/11_mvvm-viewmodel-generation/index.md) for a complete program.

## Generation rules at a glance

- A field `_name` becomes property `Name`; the leading underscore is dropped and the first letter upper-cased.
- A method's command name removes every `Async` occurrence and appends `Command`: `SaveAsync` becomes `SaveCommand`.
- `[VeloxProperty]` accepts a field or a `partial` property; the generated setter raises `INotifyPropertyChanging` and `INotifyPropertyChanged`.
- `[VeloxCommand(canValidate: true)]` requires a `private partial bool CanExecute{Name}Command(...)` implementation; omitting it is a compile error.
- An `ObservableCollection<T>` property gets lazy subscription and four partial collection hooks.
