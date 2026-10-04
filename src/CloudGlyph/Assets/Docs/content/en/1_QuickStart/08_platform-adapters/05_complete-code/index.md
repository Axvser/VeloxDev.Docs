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
        <PackageReference Include="VeloxDev.WPF" Version="10.0.0" />
    </ItemGroup>
</Project>
```

To *see* the workflow you still need an app shell (an `App` + `MainWindow`) that hosts `WorkflowView` and binds its `DataContext` to an `IWorkflowTreeViewModel` built with `[WorkflowBuilder.Tree]` — that tree construction is part of the workflow-system feature, not of this page. The view files below are framework-complete and need only that data context.

Sub-pages (one page per source file):

- [00 WorkflowView — the surface host](00_workflow-view/index.md)
- [01 NodeView — the node card](01_node-view/index.md)
- [02 SlotView — the connector](02_slot-view/index.md)
- [03 LinkView — the curve link](03_link-view/index.md)
- [04 GridDecorator — grid + rulers](04_grid-decorator/index.md)
- [05 MinimapOverlay — the minimap](05_minimap-overlay/index.md)
- [06 TemplateSelector — the DataTemplate selector](06_template-selector/index.md)

## Run declaration

- ✅ Generated and diffed on 2026-10-01. The seven `dotnet new wpf-v-*` commands on the [Setup](../02_setup/index.md) page were actually run against the installed `VeloxDev.WPF.Templates` pack; they produced exactly **11 files** under `Views/`:

```text
已成功创建模板“VeloxDev WPF Workflow Tree View”。
已成功创建模板“VeloxDev WPF Workflow Node View”。
已成功创建模板“VeloxDev WPF Workflow Slot View”。
已成功创建模板“VeloxDev WPF Workflow Link View”。
已成功创建模板“VeloxDev WPF Workflow Template Selector”。
已成功创建模板“VeloxDev WPF Workflow Grid Decorator”。
已成功创建模板“VeloxDev WPF Workflow Minimap Overlay”。
```

  The code blocks on the seven sub-pages were then byte-compared against the generated files: **9 of 11 match verbatim**; the two that did not (`WorkflowView.xaml` missing `CornerRadius="3"`, and a mangled comment in `NodeView.xaml`) were corrected to match.
- ✅ The demo that hosts this view layer built on the same date: `dotnet build Examples/Workflow/WPF/Demo/Demo.csproj` succeeded with 0 warnings / 0 errors (see the [Verification](../04_verification/index.md) run declaration).
- ⚠️ The generated scaffold was not compiled *in isolation* (it was emitted into a scratch folder, not a WPF project) and the assembled app was not launched — treat it as verified-by-generation plus verified-by-build of the equivalent in-repo demo, not as a proven end-to-end run of this exact scaffold.
