# Prerequisites and install

## Supported targets

The adapter project declares `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`. Pick `net8.0-windows` for a new project; the demo this page follows is tested on `net10.0-windows`.

- Windows. `UseWindowsForms` and Easel's GDI+ renderer have no other host.
- .NET SDK 8.0 or later for `net8.0-windows`. A .NET Framework target needs C# 10 (`LangVersion latest`), because the generated ViewModels use modern C# syntax.
- No database, service or API key.

## Packages

| Package | Version declared in this repository | Role |
| --- | --- | --- |
| `VeloxDev.WinForms` | 12.3.1 | the adapter |
| `VeloxDev.Core` | 12.3.0 | model and canvas contracts, pulled transitively |
| `WinForms.Easel` | 1.1.1 | the visual runtime, pulled transitively in Release |
| `WinForms.Easel.Generator` | 1.1.0 | compiles `.xaml` into visual controls; must be an analyzer reference |
| `VeloxDev.WinForms.Templates` | 12.0.0 | the seven `dotnet new` item templates |

In a source checkout, the demo replaces the two packages with project references to `Src/Adapters/VeloxDev.WinForms/VeloxDev.WinForms.csproj` and `Easel/Src/Generators/Easel.Generator/Easel.Generator.csproj`. A NuGet consumer only adds the package and the generator package.

## Project file

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <ApplicationHighDpiMode>PerMonitorV2</ApplicationHighDpiMode>
  </PropertyGroup>

  <ItemGroup>
    <!-- Easel XAML files take their base types from Easel; the implicit WinForms
         namespace would make Control / UserControl / Panel ambiguous there. -->
    <Using Remove="System.Windows.Forms" />
    <PackageReference Include="VeloxDev.WinForms" Version="12.3.1" />
    <PackageReference Include="WinForms.Easel.Generator" Version="1.1.0"
                      OutputItemType="Analyzer" ReferenceOutputAssembly="false" />
  </ItemGroup>

  <ItemGroup>
    <AdditionalFiles Include="**/*.xaml" />
  </ItemGroup>
</Project>
```

`ApplicationHighDpiMode=PerMonitorV2` matches the runtime contract: the visual host lays out in logical DIPs and scales its own `Graphics` by `DeviceDpi / 96`.

## Install

```powershell
dotnet new winforms -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.WinForms
dotnet add package WinForms.Easel.Generator
dotnet new install VeloxDev.WinForms.Templates
```

**Expected result:** the package references resolve, and

```powershell
dotnet new list winforms-v
```

lists seven short names: `winforms-v-tree`, `winforms-v-node`, `winforms-v-slot`, `winforms-v-link`, `winforms-v-selector`, `winforms-v-decorator`, `winforms-v-minimap`.

## Generate before the first build

The tree markup type-references `GridDecorator`, `CustomTemplateSelector`, `MinimapOverlay`, `NodeView`, `SlotView` and `LinkView`. A partial suite therefore fails with `CS0246`, not with a runtime error. Generate all seven roles as shown in [Surface and host](../01_surface-and-host/index.md); the pack's item map is in [Workflow item templates](../../32_workflow-item-templates/index.md).

If a previous install left a folder-mounted pack with the same short name, `dotnet new install` may exit non-zero. Run `dotnet new uninstall VeloxDev.WinForms.Templates` first, then install the NuGet package.
