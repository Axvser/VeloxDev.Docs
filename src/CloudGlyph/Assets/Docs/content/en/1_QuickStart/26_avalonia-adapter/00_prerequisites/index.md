# Prerequisites

## Supported targets

Source: `Src/Adapters/VeloxDev.Avalonia/VeloxDev.Avalonia.csproj`.

| Property | Declared value |
| --- | --- |
| `TargetFrameworks` | `netstandard2.0;net6.0;net8.0` |
| `AvaloniaVersion` | `11.1.0` |
| `AvaloniaUseCompiledBindingsByDefault` | `true` |
| `VeloxDev.Core` dependency | `12.3.0` |
| Package version | `12.3.0` |

The adapter builds against Avalonia 11.1.0 and the shipped demos run on the 12.x line. A `net8.0` application is the configuration this page follows.

## Tooling

- **.NET SDK 8.0 or later** for `net8.0`.
- **A desktop OS** — the complete code uses `Avalonia.Desktop` and `IClassicDesktopStyleApplicationLifetime`.
- No database, service, API key or network access.

## Add the packages

```powershell
dotnet add package VeloxDev.Avalonia --version 12.3.0
dotnet add package Avalonia.Desktop --version 11.1.0
dotnet add package Avalonia.Themes.Fluent --version 11.1.0
```

**Expected result:** all three commands exit `0`; the project file lists `VeloxDev.Avalonia`, `Avalonia.Desktop` and `Avalonia.Themes.Fluent`, and `VeloxDev.Core` is restored transitively.

The Core generator travels as an analyzer dependency of the package, so the `[WorkflowBuilder.*]` and `[VeloxProperty]` attributes produce `InitializeWorkflow()` and the standard commands without an extra reference.

## Project settings

```xml
<PropertyGroup>
  <OutputType>WinExe</OutputType>
  <TargetFramework>net8.0</TargetFramework>
  <AvaloniaUseCompiledBindingsByDefault>true</AvaloniaUseCompiledBindingsByDefault>
  <Nullable>enable</Nullable>
  <LangVersion>latest</LangVersion>
</PropertyGroup>
```

**Expected result:** `dotnet build` succeeds before any workflow type is added. With compiled bindings on, a binding scope without `x:DataType` reports `AVLN2100` instead of silently returning nothing.
