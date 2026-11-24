# Prerequisites

The WPF adapter is a normal WPF class library. It declares four target frameworks, so the framework you pick decides the SDK you need.

## Supported targets

Source: `Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`.

| Property | Declared value |
| --- | --- |
| `TargetFrameworks` | `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows` |
| `UseWPF` | `true` |
| `VeloxDev.Core` dependency | `12.3.0` |
| Package version | `12.3.0` |

The trimmed demo targets `net10.0-windows`; that is the **tested** configuration for this page, not the minimum. A `net8.0-windows` project is supported by the package and needs .NET SDK 8.0 or later.

## Tooling

- **.NET SDK 8.0 or later** for `net8.0-windows`. The .NET Framework target needs C# 10 or later (`LangVersion latest`) because the generated ViewModels use ranged/index syntax.
- **Windows** — WPF has no other host.
- No database, service, API key or network access.

## Add the package

```powershell
dotnet add package VeloxDev.WPF --version 12.3.0
```

**Expected result:** the command exits `0`, `VeloxDev.WPF` appears in the project file, and `VeloxDev.Core` is restored transitively.

The package carries the Core generator as an analyzer dependency, so the `[WorkflowBuilder.*]` and `[VeloxProperty]` attributes on the next page produce `InitializeWorkflow()`, `CreateNodeCommand`, `Helper`, `Nodes`, `Links` and the property changed hooks without a second package reference.

## Check the target

```powershell
dotnet --list-sdks
```

**Expected result:** at least one `8.0.*` (or later) entry. In a `net8.0-windows` project, `dotnet build` succeeds before any workflow type is added.
