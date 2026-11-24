# Prerequisites and install

## What the packs are

Each pack is a NuGet package with `<PackageType>Template</PackageType>` and `TargetFramework netstandard2.0`. It compiles no C# and references no adapter: its content is the seven item directories plus their `.template.config/template.json`. The pack version in this repository is **12.0.0** for all seven.

The generated files do reference the adapter — through `assembly=VeloxDev.<GUI>` on the markup packs, and through component namespaces on Razor — plus `VeloxDev.WorkflowSystem`, so the matching adapter package must be installed in your project. A pack is installed once per machine; the adapter package is per project.

## Requirements

- A .NET SDK recent enough for `dotnet new`. The pack itself is `netstandard2.0`; the *generated* project decides its own SDK floor.
- The adapter package for the GUI you generate for: `VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor` or `VeloxDev.Jalium`.
- The GUI SDK or workload: WinUI and MAUI need their workloads, Razor needs the ASP.NET Core shared framework, Jalium needs .NET 10.
- No database, service or API key.

## Install a pack

```powershell
dotnet new install VeloxDev.WinForms.Templates
dotnet add package VeloxDev.WinForms
```

Swap both names for the GUI you target. Install the **latest published** version of both; do not pin the adapter to the version printed in this repository.

**Expected result:** `dotnet new list winforms-v` lists seven short names. Without the adapter package the generation still succeeds; the build is what fails later.

## Uninstall / reinstall

A folder-mounted pack and a NuGet pack with the same short name make resolution ambiguous, and `dotnet new install` exits non-zero on a duplicate. Keep one registration per short name:

```powershell
dotnet new uninstall VeloxDev.WinForms.Templates
dotnet new install VeloxDev.WinForms.Templates
```

## One namespace per suite

All seven items must be generated into the same namespace. The tree resolves its selector, decorator, minimap and node/link templates by their default class names through a namespace alias (or bare type name in Razor). Splitting them across namespaces gives a build that cannot find its siblings.

The ViewModels and the host shell are not generated. A minimal ViewModel set is the `ViewModels/Workflow/` folder in `Examples/Workflow/<GUI> Trimmed/Demo/` (the Razor demo folder is named `Blazor Trimmed`); the corresponding adapter quick start shows the four classes:

- [WinForms adapter](../../29_winforms-adapter/01_surface-and-host/index.md)
- [Razor adapter](../../30_razor-adapter/01_surface-and-host/index.md)
- [Jalium adapter](../../31_jalium-adapter/01_surface-and-host/index.md)
