# MVVM ViewModel Generation

Write a console program whose properties, commands and collection hooks are generated from attributes. The generator is a Roslyn analyzer: nothing is reflected at run time, and the generated members appear as ordinary C# after the first build.

## 1. Prerequisites

- **Supported targets of `VeloxDev.Core`** (declared in `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`): `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`. The sample uses `net8.0`; `ValueTask` command bodies on `netstandard2.0` additionally need `System.Threading.Tasks.Extensions`.
- **`VeloxDev.Core.Generator`** is an analyzer that targets `netstandard2.0` and runs inside the C# compiler. It is not a runtime dependency. A NuGet reference to Core carries the analyzer; a `ProjectReference` does not, so that project needs it as an analyzer reference. This sample installs the package explicitly for its build-time Roslyn check.
- .NET SDK 8.0 or later. No services are required.

## 2. Install / Add Dependency

```text
dotnet new console -n MvvmQuickStart
cd MvvmQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** the command exits 0 and `MvvmQuickStart.csproj` contains a `PackageReference` for both packages. After the first build the generated members appear in IntelliSense; set `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` if you want the `*_MVVM.g.cs` and `*_Command.g.cs` files written under `obj/` for inspection.

## 3. Basic Setup / Registration

A class only needs the `partial` modifier. The generator adds the notification interfaces, the backing property, the command object and the collection plumbing.

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => System.Console.WriteLine($"[property] priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => System.Console.WriteLine($"[collection] added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

**Expected result:** the class compiles as `INotifyPropertyChanged`; `Title`, `Priority`, `Tags` and `PromoteCommand` are available even though only the underscore-prefixed fields were written. `_priority` maps to `Priority` by dropping the underscore and upper-casing the first letter.

## 4. Core Usage (Step by Step)

### 4.1 Properties and their callbacks

`[VeloxProperty]` accepts a field or a `partial` property. The generated setter compares old and new, raises `PropertyChanging`/`PropertyChanged`, and calls the `On{Name}Changing` / `On{Name}Changed` partial methods with both values. The field initializer keeps working, so a field can carry its default value.

```csharp
var note = new NoteViewModel();
note.Title = "Ship the wiki";   // generated setter
System.Console.WriteLine(note.Priority);
```

**Expected result:** the assignment compiles against a generated property; no hand-written `SetProperty` call exists.

### 4.2 Commands

The command member name is the method name with every occurrence of `Async` removed, plus `Command`: `Promote` becomes `PromoteCommand`, `SaveAsync` also becomes `SaveCommand`. The body may return `void`, `Task`, `Task<T>`, `ValueTask` or `ValueTask<T>`, and may end with a `CancellationToken`.

```csharp
if (note.PromoteCommand.CanExecute(null))
{
    note.PromoteCommand.Execute(null);
}
```

`canValidate: true` makes the generator declare `private partial bool CanExecutePromoteCommand(...)`; omitting the implementation is a compile error, not a command that is silently always enabled. A method with no leading parameters receives a single `object?` in that validator.

**Expected result:** `CanExecute(null)` is `true` while `Priority < 3`; the execution raises the property callback.

### 4.3 Collection hooks

For an `ObservableCollection<T>` property the generated getter subscribes lazily, and four partial hooks exist: `OnItemAddedTo{Name}`, `OnItemRemovedFrom{Name}`, `OnItemMovedIn{Name}` and `OnItemsResetIn{Name}`. The single generic `OnCollectionChanged<T>` hook sees every action with the old and new items.

```csharp
note.Tags.Add("docs");   // getter subscribes, then the Add raises OnItemAddedToTags
```

**Expected result:** the `OnItemAddedToTags` implementation prints `[collection] added docs`.

### 4.4 Awaiting a result, interrupting, and reloading executability

`IVeloxCommand` exposes `Lock`, `Unlock`, `Notify`, `Interrupt`, `Clear`, `Continue` and awaitable counterparts; `Notify()` raises `CanExecuteChanged` after state the validator reads has changed. A command that returns a value is exposed as `IVeloxCommand<TParam, TResult>`, whose `ExecuteAsync` can be awaited.

```csharp
note.PromoteCommand.Notify();          // re-evaluate CanExecute
await note.PromoteCommand.InterruptAsync();
```

**Expected result:** the UI (or a console check of `CanExecute`) observes the new executability; an interrupt reports `Canceled` on the command's `Canceled` event.

## 5. Verification

Run the complete program below with `dotnet run`. The console must show the collection hook before the first summary, two property changes, and a final priority of 3. The third `CanExecute` check must be `False`, proving the validator is wired.

```text
[collection] added docs
Ship the wiki / priority 1 / tags 1
can execute at 1: True
[property] priority 1 -> 2
can execute at 2: True
[property] priority 2 -> 3
can execute at 3: False
final priority: 3
```

## 6. Complete Code

Replace `Program.cs` with this file. Top-level statements come first; the partial class follows.

```csharp
using System;
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

var note = new NoteViewModel { Title = "Ship the wiki", Priority = 1 };

note.Tags.Add("docs");
Console.WriteLine($"{note.Title} / priority {note.Priority} / tags {note.Tags.Count}");

for (var i = 0; i < 3; i++)
{
    Console.WriteLine($"can execute at {note.Priority}: {note.PromoteCommand.CanExecute(null)}");
    if (note.PromoteCommand.CanExecute(null))
    {
        note.PromoteCommand.Execute(null);
    }
}

Console.WriteLine($"final priority: {note.Priority}");

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => Console.WriteLine($"[property] priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => Console.WriteLine($"[collection] added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

Source for the shared command-signature gallery: `Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs`; the property and collection pattern is in `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against the generator sources (`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`, `Command.cs`, `Base/Analizer.cs`), the attribute declarations (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`, `VeloxCommandAttribute.cs`) and both MVVM demos. The I/O plan is complete; NuGet restore and execution were not performed in this environment.
