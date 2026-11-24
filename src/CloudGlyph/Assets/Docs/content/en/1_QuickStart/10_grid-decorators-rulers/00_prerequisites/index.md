# Prerequisites

The sample is WPF. The Avalonia, WinUI, MAUI, WinForms, Razor and Jalium packs ship equivalent decorator items; the drawing API differs, the contract does not.

## Supported targets

| Package | Target frameworks |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, `net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`, `net5.0-windows`, `netcoreapp3.0`, `net8.0-windows` |
| `VeloxDev.Avalonia` (alternative) | `netstandard2.0`, `net6.0`, `net8.0` |

The sample targets `net8.0-windows`; the demos run on `net10.0-windows` / `net10.0`.

## Toolchain

- .NET SDK 8.0+.
- Windows for WPF.
- NuGet and the `dotnet new` template engine.

No service is required.

## Add the packages

```powershell
dotnet new wpf -n WorkflowGridDemo
cd WorkflowGridDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

## Generate the decorator (optional)

```powershell
dotnet new install VeloxDev.WPF.Templates
dotnet new wpf-v-decorator -n WorkflowGridDecorator -o Views/Workflow
```

The generated class implements `IWorkflowGridDecorator`, exposes `RulerThickness`, `GridSpacing`, `MajorLineEvery`, the four offsets and `RulerBand`, and draws a grid plus rulers. The sample on this feature's [Verification](../03_verification/index.md) page is a compact version of the same class.

Install the pack only once per machine. If `dotnet new wpf-v-decorator` is ambiguous, a folder-mounted template with the same short name is registered as well; `dotnet new uninstall` lists the installed items and shows which one has no package id.

## Runnable reference

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

The WPF mirror is `Examples/Workflow/WPF Trimmed/Demo/Demo.csproj`; its decorator is `Views/Workflow/WorkflowGridDecorator.cs`.

## Expected result

- `dotnet build` exits 0.
- `IWorkflowGridDecorator` resolves from `VeloxDev.WorkflowSystem`.
- `dotnet new wpf-v-decorator` creates one `.cs` file with the class you named.

If the template command is missing, the template pack was not installed; if the type does not compile, the adapter package is missing.
