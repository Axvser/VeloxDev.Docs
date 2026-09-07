# Platform Adapters — Setup: Generate the Seven Views

The `VeloxDev.WPF.Templates` pack ships **seven item templates** that scaffold the workflow views with the behaviors already wired. Run them from the root of the WPF project created in [Install](../01_install/index.md). The class names below are not arbitrary: `WorkflowView.xaml` references `NodeView`, `LinkView`, `GridDecorator`, `MinimapOverlay` and `TemplateSelector` by name, and `NodeView` embeds `SlotView`, so keep them in one namespace.

## 1. Generate the view suite

```powershell
dotnet new wpf-v-tree     -n WorkflowView      -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-node     -n NodeView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-slot     -n SlotView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-link     -n LinkView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-selector -n TemplateSelector  -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-decorator -n GridDecorator    -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-minimap  -n MinimapOverlay    -ns Demo.Views.Workflow -o Views
```

**Expected result:** eleven files are generated under `Views/` (a `.xaml` + `.xaml.cs` for `WorkflowView`, `NodeView`, `SlotView`, `LinkView`; a single `.cs` for `TemplateSelector`, `GridDecorator`, `MinimapOverlay`), each in the namespace `Demo.Views.Workflow`.

## 2. What each generated file wires

| File | Template | Role |
|---|---|---|
| `WorkflowView.xaml(.cs)` | `wpf-v-tree` | Surface host: `WorkflowSurfaceBehavior` (with `ZoomEnabled`), named parts `PART_ScrollViewer` / `PART_Canvas` / `PART_GridDecorator` / `PART_SurfaceBorder` / `PART_MinimapOverlay`, `ViewPool` bound to `Helper.VisibleItems`, and the `NodeTemplate` / `LinkTemplate` `DataTemplate`s plus `TemplateSelector` |
| `NodeView.xaml(.cs)` | `wpf-v-node` | Node card: `WorkflowSlotLayoutBehavior` (`PART_InputSlot`, `PART_OutputSlots`, `CoordinateHostName="PART_Canvas"`) and `WorkflowNodeDragBehavior` on the header |
| `SlotView.xaml(.cs)` | `wpf-v-slot` | Connector: `WorkflowSlotConnectionBehavior.IsEnabled="True"` plus pointer handlers that run `SendConnectionCommand` / `ReceiveConnectionCommand`; `SlotState` drives the color |
| `LinkView.xaml(.cs)` | `wpf-v-link` | Passive orthogonal polyline link that draws when `CanRender` and the link is render-ready |
| `TemplateSelector.cs` | `wpf-v-selector` | `DataTemplateSelector` mapping `IWorkflowLinkViewModel` / `IWorkflowSlotViewModel` / `IWorkflowNodeViewModel` / `IWorkflowTreeViewModel` to the four `DataTemplate` properties |
| `GridDecorator.cs` | `wpf-v-decorator` | `Grid`-based decorator implementing `IWorkflowGridDecorator` (grid layer + floating rulers), fed by the surface behavior |
| `MinimapOverlay.cs` | `wpf-v-minimap` | Subclass of `WorkflowMinimapOverlay` applying the color template symbols |

The complete content of each generated file is reproduced verbatim on the [Complete Code](../05_complete-code/index.md) sub-pages.

## 3. Build

```powershell
dotnet build
```

**Expected result:** compilation succeeds with the behavior namespace `VeloxDev.WorkflowSystem.AttachedBehaviors` resolved from the `VeloxDev.WPF` package. At runtime the host still needs its `DataContext` set to an `IWorkflowTreeViewModel` — that is covered on the next page.
