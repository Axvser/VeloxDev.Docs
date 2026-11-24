# Prerequisites

The minimap sample is WPF. The Avalonia overlay is derived from the same Core pipeline and carries the same property names (through `AvaloniaProperty`).

## Supported targets

| Package | Target frameworks |
|---|---|
| `VeloxDev.Core` | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, `net8.0` |
| `VeloxDev.WPF` | `netframework4.6.1`, `net5.0-windows`, `netcoreapp3.0`, `net8.0-windows` |
| `VeloxDev.Avalonia` (alternative) | `netstandard2.0`, `net6.0`, `net8.0` |

The sample targets `net8.0-windows`. The demos run on `net10.0-windows` / `net10.0`.

## Toolchain

- .NET SDK 8.0+.
- Windows for WPF.
- NuGet.

No service is required.

## Add the packages

```powershell
dotnet new wpf -n WorkflowMinimapDemo
cd WorkflowMinimapDemo
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

`VeloxDev.WPF` brings `VeloxDev.Core`. The sample declares `[WorkflowBuilder.*]` and `[VeloxProperty]`; a NuGet reference to Core carries the analyzer, and the generator package is installed explicitly for its build-time Roslyn check.

## Runnable reference

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

The minimap appears in the top-right of the canvas. Use the check-box in the explorer to toggle it. The WPF full workbench (`Examples/Workflow/WPF/Demo`) has the same overlay with a toggle bound to `IsMinimapVisible`.

## Expected result

- `dotnet build` exits 0.
- `VeloxDev.WorkflowSystem.AttachedBehaviors.WorkflowMinimapOverlay` resolves in XAML.
- The demo shows a minimap over the canvas.

If the type is not found, the adapter package is missing. If the overlay is blank, the surface behavior did not resolve `MinimapOverlayName` or `ScrollViewerName`.
