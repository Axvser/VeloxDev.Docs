# Platform Adapters — Basic Setup / Registration

Scaffold the workflow view suite from the item templates:

```powershell
dotnet new wpf-v-slot -n SlotView -ns MyApp.Views -o Views
dotnet new wpf-v-node -n NodeView -ns MyApp.Views -o Views
dotnet new wpf-v-link -n LinkView -ns MyApp.Views -o Views
dotnet new wpf-v-tree -n TreeView -ns MyApp.Views -o Views
dotnet new wpf-v-selector -n TemplateSelector -ns MyApp.Views -o Views
dotnet new wpf-v-decorator -n GridDecorator -ns MyApp.Views -o Views
dotnet new wpf-v-minimap -n MinimapOverlay -ns MyApp.Views -o Views
```

Each template generates its files under `Views/` with the required VeloxDev workflow behaviors already wired:

- `wpf-v-slot` → `SlotView.xaml/.cs` — `WorkflowSlotConnectionBehavior.IsEnabled="True"` (press = send, release = receive).
- `wpf-v-node` → `NodeView.xaml/.cs` — `WorkflowSlotLayoutBehavior` (slot anchors) + `WorkflowNodeDragBehavior` (drag to move).
- `wpf-v-link` → `LinkView.xaml/.cs` — a passive polyline connection view.
- `wpf-v-tree` → `TreeView.xaml/.cs` — the surface host: `WorkflowSurfaceBehavior`, `ViewPool`, `WorkflowCanvasTransformBehavior`, minimap + grid decorator.
- `wpf-v-selector` → `TemplateSelector.cs` — `DataTemplateSelector` for Node/Slot/Link/Tree.
- `wpf-v-decorator` → `GridDecorator.cs` — `Decorator : IWorkflowGridDecorator` drawing the grid + rulers.
- `wpf-v-minimap` → `MinimapOverlay.cs` — subclass of `WorkflowMinimapOverlay` applying template colors.

**Expected result:** the seven view files are generated under `Views/`, and `dotnet build` compiles them with the behavior namespace `VeloxDev.WorkflowSystem.AttachedBehaviors` resolved from the `VeloxDev.WPF` package.
