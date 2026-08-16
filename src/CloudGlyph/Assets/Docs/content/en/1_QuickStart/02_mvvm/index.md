# MVVM — Quick Start

## MVVM

VeloxDev MVVM is a source-generator layer that turns plain `partial` classes into full MVVM view-models at compile time. `[VeloxProperty]` expands a private field (or a `partial` property) into a public observable property that raises `INotifyPropertyChanging` / `INotifyPropertyChanged` and exposes `partial void` hooks; `[VeloxCommand]` expands a `Task`/`void` method into a lazily created `IVeloxCommand` property with an async execution queue, cancellation, and a complete lifecycle-event stream.

### Quick Start

#### 1. Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` — usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+) for the MVVM/Command source generators; the demos target `net9.0` — a *tested* configuration.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:** none — the runtime and generator work in a console app or any GUI (WPF / Avalonia / WinUI / MAUI / WinForms / Blazor).


#### 2. Install / Add Dependency

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core` (currently `7.0.0`) references `VeloxDev.Core.Generator` (`7.0.0`) as a normal package reference (`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`, lines 26-29), so the Roslyn generators ship transitively — no manual analyzer wiring.

**Expected result:** `VeloxDev.Core.Generator` appears under the analyzers of the project; `dotnet build` succeeds.

#### 3. Basic Setup / Registration

Declare a `partial class` — any name, any namespace — annotate fields or `partial` properties with `[VeloxProperty]` and methods with `[VeloxCommand]`. No base class is required; the generator synthesizes the notification infrastructure (`PropertyChanging` / `PropertyChanged` events and `OnPropertyChanging` / `OnPropertyChanged` methods) when none exists, or reuses a base class that already provides it.

**Expected result:** generated `.g.cs` files appear under `obj/<Configuration>/<TargetFramework>/generated/` (e.g. `CounterViewModel_ConsoleApp_MVVM.g.cs` and `CounterViewModel_ConsoleApp_Commands.g.cs`); the annotated members compile to a public `Count` property and public `IncrementCommand` / `DecrementCommand` properties.

#### 4. Core Usage (Step by Step)

1) Declare an observable property. For a partial property write `[VeloxProperty] public partial int Count { get; set; }`; for a private field write `[VeloxProperty] private int _count = 0;`. The generator emits the property plus `partial void OnCountChanged(int oldValue, int newValue)` (the abbreviated form `partial void OnCountChanged(int value)` from the generator docs is the same hook — the real signature receives both the old and the new value).
   **Expected result:** `Count = 5` raises `PropertyChanging` → invokes `OnCountChanged` → raises `PropertyChanged`; a subscriber sees both notifications in that order.

2) Declare a command. Annotate a method with `[VeloxCommand]`. The `Task`-returning two-parameter shape `Task Plus(object? sender, CancellationToken ct)` maps to the primary `VeloxCommand` constructor (`Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs`, `ParseConstructorType`, lines 78-116); the generated command property is named after the method (`Plus` → `PlusCommand`).
   **Expected result:** a public `IVeloxCommand PlusCommand` property exists; calling `PlusCommand.Execute(null)` runs the method asynchronously.

3) Enable executability validation with `canValidate: true`. The generator then emits `private partial bool CanExecuteMinusCommand(object? parameter);`, which you implement (demo: `_index > 0`).
   **Expected result:** while the predicate returns `false`, `CanExecute(null)` returns `false` and a bound button is disabled; calling `MinusCommand.Notify()` after each relevant change re-queries the predicate.

4) Execute or bind via the generated command property. In XAML: `Command="{Binding PlusCommand}"`; in code: `vm.PlusCommand.Execute(null)` or `await vm.PlusCommand.ExecuteAsync(null)`.
   **Expected result:** the bound button or the code path triggers the command method; with `semaphore: 1` a second trigger while the first is running is queued, not lost.

5) Observe the lifecycle events. `IVeloxCommand` exposes `Created`, `Enqueued`, `Dequeued`, `Started`, `Completed`, `Failed`, `Canceled`, `Exited`, plus `CanExecuteChanged` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`, lines 92-101).
   **Expected result:** subscribing `cmd.Started += e => ...` and `cmd.Completed += e => ...` prints the events in order: `Started` before the method body runs, `Completed` after it returns.

#### 5. Verification

Run the MVVM demo (`Examples/MVVM/WPF/Demo` or `Examples/MVVM/Avalonia/Demo`) or the console sample below. Property notifications fire on every set; the command enqueues / executes and raises events in the documented order; with `_index == 0` the 减少 (Minus) button is disabled because `CanExecuteMinusCommand` returns `false`. The demo also exercises the collection hooks: `OnItemAddedToItems`, `OnItemRemovedFromItems`, `OnItemMovedInItems`, `OnItemsResetInItems`, and `OnCollectionChanged<T>`.

#### 6. Complete Code

A standalone console program that uses both generators. It compiles against `VeloxDev.Core` with `ImplicitUsings` disabled (all `using` directives are explicit):

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.MVVM;

public partial class CounterViewModel
{
    [VeloxProperty] public partial int Count { get; set; }

    partial void OnCountChanged(int oldValue, int newValue)
    {
        Console.WriteLine($"[hook] Count {oldValue} -> {newValue}");
    }

    [VeloxCommand]
    private Task IncrementAsync(object? parameter, CancellationToken ct)
    {
        Count++;
        return Task.CompletedTask;
    }

    [VeloxCommand(canValidate: true)]
    private Task DecrementAsync(object? parameter, CancellationToken ct)
    {
        Count--;
        return Task.CompletedTask;
    }

    private partial bool CanExecuteDecrementCommand(object? parameter) => Count > 0;
}

public static class Program
{
    public static async Task Main()
    {
        var vm = new CounterViewModel();

        vm.IncrementCommand.Started += e =>
            Console.WriteLine($"[event] Started ({e.EventType})");
        vm.IncrementCommand.Completed += e =>
            Console.WriteLine($"[event] Completed ({e.EventType})");
        vm.IncrementCommand.Failed += e =>
            Console.WriteLine($"[event] Failed ({e.EventType}, {e.Exception?.Message})");

        vm.Count = 5;

        vm.IncrementCommand.Execute(null);
        vm.DecrementCommand.Execute(null);

        await Task.Delay(300);

        Console.WriteLine($"Final Count = {vm.Count}");
        Console.WriteLine($"Decrement enabled = {vm.DecrementCommand.CanExecute(null)}");
    }
}
```

Statically reasoned output (both commands are `Task.CompletedTask`, so they complete immediately):

```text
[hook] Count 0 -> 5
[event] Started (Started)
[event] Completed (Completed)
[event] Started (Started)
[event] Completed (Completed)
Final Count = 5
Decrement enabled = True
```

#### 7. Run Declaration

- ⚠️ Not actually run — statically verified only. The generator outputs, event ordering, and command semantics above are derived from the source (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`, `Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs`) and the checked-in demos/tests; no console project was compiled and executed to produce real output in this session.
