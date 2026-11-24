# Prerequisites

The sample in this feature is WPF. Avalonia closes the same roles; its pool template selector is an `IDataTemplate` instead of a WPF `DataTemplateSelector`.

## Supported targets

| Package | Target frameworks |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, `net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`, `net5.0-windows`, `netcoreapp3.0`, `net8.0-windows` |
| `VeloxDev.Avalonia` (alternative) | `netstandard2.0`, `net6.0`, `net8.0` |

The sample targets `net8.0-windows`. The demos target `net10.0-windows` / `net10.0`; those are tested configurations, not minimums.

## Toolchain

- .NET SDK 8.0+.
- Windows for WPF.
- NuGet.

No external service is required.

## Add the packages

```powershell
dotnet new wpf -n WorkflowPoolDemo
cd WorkflowPoolDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` brings `VeloxDev.Core`. The generator is an analyzer; a NuGet reference to Core carries it. A `ProjectReference` does not, so that project needs the generator as an analyzer reference. The sample installs it explicitly for its build-time Roslyn check.

## Runnable reference

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

The WPF mirror is `Examples/Workflow/WPF Trimmed/Demo/Demo.csproj`. The generator reference for both comes from `Examples/Workflow/Directory.Build.props`.

## Expected result

- `dotnet build` exits 0.
- The project resolves `VeloxDev.WorkflowSystem.AttachedBehaviors.ViewPool` in XAML.
- The `[WorkflowBuilder.Tree<...>]` partial class compiles and exposes `InitializeWorkflow()`.

If `InitializeWorkflow` is not found, the generator reference is missing. If `ViewPool` is not found, the adapter package is.
