# Prerequisites

This Quick Start builds a WPF host. The Core contracts are platform-neutral; the Avalonia adapter closes the same role set, but its properties are `AvaloniaProperty` and its template selector is an `IDataTemplate`.

## Supported targets

`VeloxDev.Core` and `VeloxDev.WPF` declare these target frameworks in their project files. A new host can target `net8.0-windows`; the demo projects target `net10.0-windows`, which is one tested configuration, not the minimum.

| Package | Target frameworks |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, `net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`, `net5.0-windows`, `netcoreapp3.0`, `net8.0-windows` |
| `VeloxDev.Avalonia` (alternative) | `netstandard2.0`, `net6.0`, `net8.0` |

## Toolchain

- **.NET SDK 8.0 or newer** for the sample's `net8.0-windows` target.
- **Windows** for WPF.
- A NuGet client (`dotnet` CLI is enough).

No service, database or API key is involved.

## Add the packages

```powershell
dotnet new wpf -n WorkflowSurfaceDemo
cd WorkflowSurfaceDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` brings `VeloxDev.Core`. The generator is a Roslyn analyzer. A NuGet reference to Core carries it; a `ProjectReference` does not, so a project that declares `[WorkflowBuilder.*]` or `[VeloxProperty]` through a project reference must add the generator as an analyzer reference. This tree installs the generator package explicitly for its build-time Roslyn check. The package versions in this tree are 12.3.0; keep the generator on the same version as Core.

If you prefer to run the repository demo instead of building a new project:

```powershell
dotnet run --project "Examples/Workflow/WPF Trimmed/Demo/Demo.csproj"
```

That project already references the adapters and the generator through `Examples/Workflow/Directory.Build.props`.

## Expected result

- `dotnet build` exits with code 0.
- The project file lists `VeloxDev.WPF` and `VeloxDev.Core.Generator`.
- The `VeloxDev.WorkflowSystem.AttachedBehaviors` namespace resolves in XAML.

If the generator is missing, the `[WorkflowBuilder.Tree<...>]` partial classes fail with members that "do not exist" — that is the usual symptom, not a missing adapter reference.
