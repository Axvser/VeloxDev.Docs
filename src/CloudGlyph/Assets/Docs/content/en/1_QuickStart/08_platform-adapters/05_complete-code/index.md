# Platform Adapters — Complete Code

The seven sub-pages reproduce, **verbatim**, the files that the Setup page's `dotnet new wpf-v-*` commands generate (`-n` names and the `Demo.Views.Workflow` namespace already substituted, template default colors filled in). Combined they are the workflow **view layer** of a WPF project.

## The project file

The suite lives in a WPF project with `UseWPF` enabled and a package reference to the adapter:

```xml
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <OutputType>WinExe</OutputType>
        <TargetFramework>net9.0-windows</TargetFramework>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <UseWPF>true</UseWPF>
    </PropertyGroup>
    <ItemGroup>
        <PackageReference Include="VeloxDev.WPF" Version="9.0.0" />
    </ItemGroup>
</Project>
```

To *see* the workflow you still need an app shell (an `App` + `MainWindow`) that hosts `WorkflowView` and binds its `DataContext` to an `IWorkflowTreeViewModel` built with `[WorkflowBuilder.Tree]` — that tree construction is part of the workflow-system feature, not of this page. The view files below are framework-complete and need only that data context.

Sub-pages (one page per source file):

- [00 WorkflowView — the surface host](00_workflow-view/index.md)
- [01 NodeView — the node card](01_node-view/index.md)
- [02 SlotView — the connector](02_slot-view/index.md)
- [03 LinkView — the polyline link](03_link-view/index.md)
- [04 GridDecorator — grid + rulers](04_grid-decorator/index.md)
- [05 MinimapOverlay — the minimap](05_minimap-overlay/index.md)
- [06 TemplateSelector — the DataTemplate selector](06_template-selector/index.md)

## Run declaration

- ⚠️ Not actually run — statically verified only. Each code block was produced from the real template sources under `Src/Templates/VeloxDev.WPF.Templates/working/content` (symbols substituted with their default values) and cross-checked against the adapter API surface in `Src/Adapters/VeloxDev.WPF`; the files compile against that surface but were not compiled or executed in this environment, so treat the scaffold as verified-by-inspection rather than proven-by-run.
