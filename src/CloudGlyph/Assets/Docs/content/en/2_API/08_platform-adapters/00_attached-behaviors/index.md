# API — Attached Workflow Behaviors

Every GUI adapter hosts the workflow views through a shared set of types in the **`VeloxDev.WorkflowSystem.AttachedBehaviors`** namespace (source: `Src/Adapters/<Adapter>/Attached/Workflow/*.cs`). The same class names exist on every platform, but each adapter declares them with that framework's base classes and property system:

| Adapter | Base / property system used by the behavior classes |
|---|---|
| WPF, WinUI, Jalium | attached `DependencyProperty`; behavior classes derive from `DependencyObject` (static classes where the framework requires it) |
| Avalonia | attached `AvaloniaProperty` (`RegisterAttached<Owner, Host, T>`); classes derive from `AvaloniaObject` |
| MAUI | `BindableProperty.CreateAttached`; static holder classes with `Get*` / `Set*` on `BindableObject` |
| WinForms | no attached-property system — static holder classes with `Get*` / `Set*` over a `Control` and a private per-control state table |
| Razor | Blazor components (`.razor` partial classes) instead of attached properties; event handlers surface as public methods |

So a XAML view binds e.g. `behaviors:WorkflowSurfaceBehavior.IsEnabled="True"`, a WinForms host calls `WorkflowSurfaceBehavior.SetIsEnabled(control, true)`, and a Razor page uses the `<WorkflowSurfaceBehavior>` component. The **names and shapes below are source-verified on all seven adapters**; behavior detail a workflow demo does not exercise is marked `*inferred*`.

## Type set

| Type | Role | Adapters |
|---|---|---|
| `WorkflowSurfaceBehavior` | The surface host behavior: panning, zoom hook, scroll/viewport feed, named-control resolution | all **but Jalium** (Jalium's composite `WorkflowTreeView` owns the surface) |
| `WorkflowCanvasTransformBehavior` | Owns the canvas render transform / translate offset applied to node and link views | WPF, Avalonia, WinUI, WinForms, Razor (not MAUI, not Jalium) |
| `ViewPool` / `ViewManager` | Object-pooled view container over an items collection | all seven (Razor as components) |
| `WorkflowNodeDragBehavior` | Makes a node draggable (executes `MoveCommand`) | all seven |
| `WorkflowSlotConnectionBehavior` | Connects slots on press/release (executes `SendConnectionCommand` / `ReceiveConnectionCommand`) | all seven |
| `WorkflowSlotLayoutBehavior` | Keeps slot anchors in sync with node layout | all seven |
| `WorkflowMinimapOverlay` | Thumbnail of nodes/links with a draggable viewport indicator | all seven |
| `WorkflowLinkOverlay` | MAUI-only: viewport-sized paint layer for the links that have no view of their own (the immediate-mode hosts and the frames before a pooled link view materializes) | MAUI |
| `WorkflowGridDecorator` | Grid/ruler decorator element shipped as source (the other XAML adapters get it from the `*-v-decorator` template instead) | WinForms (`.cs`), Jalium (`.cs`), Razor (`.razor`) |
| `WorkflowTreeView` | Composite host control the generated tree-view item derives from (WinForms: `PART_*` named parts; Jalium: `PortLayout` / `GridDecorator` / `TemplateSelector` properties) | WinForms, Jalium |
| `WorkflowNodeView` / `WorkflowSlotView` / `WorkflowLinkView` / `WorkflowTemplateSelector` | Per-role base classes a generated item template derives from (the "no-markup platforms get a base class per role" standard) | WinForms, Jalium |
| `IWorkflowTemplateSelector` | Factory contract mirroring a `DataTemplateSelector` | WinForms, Jalium |
| `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | Data-exchange contracts the overlays implement; **now defined in Core**, namespace `VeloxDev.WorkflowSystem` | all seven (implemented by overlays) |

## Pages

- [surface](00_surface/index.md) — `WorkflowSurfaceBehavior` and `WorkflowCanvasTransformBehavior`.
- [view-pool](01_view-pool/index.md) — `ViewPool`, `ViewManager`, and the template-selector contract.
- [node-slot](02_node-slot/index.md) — `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`.
- [minimap](03_minimap/index.md) — `WorkflowMinimapOverlay` and the `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` contracts.
- [adapter-overlays](04_adapter-overlays/index.md) — adapter-specific overlay / host types (`WorkflowLinkOverlay`, Jalium `WorkflowGridDecorator` / `WorkflowTreeView`, Razor component helpers).
