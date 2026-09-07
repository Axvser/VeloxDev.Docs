# Platform Adapters — Install / Add Dependency

Install the **template pack** and add the **adapter package** for the GUI framework you are targeting. This Quick Start uses WPF; every other platform substitutes its own pack/package name from the table in the feature overview.

## 1. Install the template pack

```powershell
dotnet new install VeloxDev.WPF.Templates
```

If you build the template packs from this repository instead, `dotnet pack` the pack project and install the produced `.nupkg`:

```powershell
dotnet pack Src/Templates/VeloxDev.WPF.Templates
dotnet new install Src/Templates/VeloxDev.WPF.Templates/bin/Debug/VeloxDev.WPF.Templates.8.0.0.nupkg
```

The template pack for your framework is the sibling of the adapter package: `VeloxDev.{Platform}.Templates`, whose item templates are all named `{prefix}-v-*` (`wpf-v-*`, `winforms-v-*`, `ava-v-*`, `winui-v-*`, `maui-v-*`, `razor-v-*`, `jalium-v-*`). The grid decorator item is `{prefix}-v-decorator` on every platform.

**Expected result:** `dotnet new list wpf-v` lists the seven `wpf-v-*` item templates (they are also visible under `dotnet new list` with the `VeloxDev.WPF.Workflow*` identities).

## 2. Reference the adapter package

Create or open the GUI project, then add the matching package:

```powershell
dotnet new wpf -n WorkflowDemo -f net9.0
cd WorkflowDemo
dotnet add package VeloxDev.WPF
```

The six sibling packages are added the same way (`VeloxDev.WinForms`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.Razor`, `VeloxDev.Jalium`). All of them package-reference `VeloxDev.Core` and pull in the workflow engine transitively. When working from the repository, use a project reference to the adapter instead (the in-repo demos do this, e.g. `Examples/Workflow/WPF/Demo/Demo.csproj` references `Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`).

**Expected result:** the `.csproj` gains a `<PackageReference Include="VeloxDev.WPF" Version="8.0.0" />` (or the project reference), and `dotnet build` compiles — the `VeloxDev.WorkflowSystem.AttachedBehaviors` namespace is now resolvable in XAML and code.

## 3. All packages at a glance

| Adapter package | Package for the workflow engine | Template pack |
|---|---|---|
| `VeloxDev.WPF` | `VeloxDev.Core` | `VeloxDev.WPF.Templates` |
| `VeloxDev.WinForms` | `VeloxDev.Core` | `VeloxDev.WinForms.Templates` |
| `VeloxDev.Avalonia` | `VeloxDev.Core` | `VeloxDev.Avalonia.Templates` |
| `VeloxDev.WinUI` | `VeloxDev.Core` | `VeloxDev.WinUI.Templates` |
| `VeloxDev.MAUI` | `VeloxDev.Core` | `VeloxDev.MAUI.Templates` |
| `VeloxDev.Razor` | `VeloxDev.Core` | `VeloxDev.Razor.Templates` |
| `VeloxDev.Jalium` | `VeloxDev.Core` | `VeloxDev.Jalium.Templates` |
