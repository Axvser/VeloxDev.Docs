# API — Attached Workflow Behaviors

Every GUI adapter hosts the workflow views through a shared set of types in the **`VeloxDev.WorkflowSystem.AttachedBehaviors`** namespace (source: `Src/Adapters/<Adapter>/Attached/Workflow/*.cs`). The same class names exist on every platform, but each adapter declares them with that framework's base classes and property system:

| Adapter | Base / property system used by the behavior classes |
|---|---|
| WPF, WinUI | attached `DependencyProperty`; behavior classes derive from `DependencyObject` (the surface and the three gesture behaviors are `sealed`; the canvas transform is a `static class`) |
| Jalium | attached `DependencyProperty`; the surface is a `static class`, and the gesture behaviors derive from `DependencyObject`; the canvas transform is the surface's `CanvasTransform` attached property (no separate class) |
| Avalonia | attached `AvaloniaProperty` (`RegisterAttached<Owner, Host, T>`); classes derive from `AvaloniaObject` |
| MAUI | `BindableProperty.CreateAttached`; static holder classes with `Get*` / `Set*` on `BindableObject` |
| WinForms | no attached-property system — static holder classes with `Get*` / `Set*` over a `Control` and a private per-control state table |
| Razor | Blazor components (`.razor` partial classes) instead of attached properties; event handlers surface as public methods |

So a XAML view binds e.g. `behaviors:WorkflowSurfaceBehavior.IsEnabled="True"`, a WinForms host calls `WorkflowSurfaceBehavior.SetIsEnabled(control, true)`, and a Razor page uses the `<WorkflowSurfaceBehavior>` component. The **names and shapes below are source-verified on all seven adapters**; behavior detail a workflow demo does not exercise is marked `*inferred*`.

## Type set

| Type | Role | Adapters |
|---|---|---|
| `WorkflowSurfaceBehavior` | The surface host behavior: panning, zoom hook, scroll/viewport feed, named-control resolution, link menu | all seven (WPF/WinUI/Avalonia/MAUI are `sealed` behavior classes; Jalium is a `static class`) |
| `WorkflowCanvasTransformBehavior` | Owns the canvas render transform / translate offset applied to node and link views | WPF, Avalonia, WinUI, WinForms, Razor (not MAUI; Jalium exposes `WorkflowSurfaceBehavior.CanvasTransform` instead) |
| `ViewPool` / `ViewManager` | Object-pooled view container over an items collection | all seven (Razor as components) |
| `WorkflowNodeDragBehavior` | Makes a node draggable (executes `MoveCommand`) | all seven |
| `WorkflowSlotConnectionBehavior` | Connects slots on press/release (executes `SendConnectionCommand` / `ReceiveConnectionCommand`) and reports the candidate receiver while the pointer moves | all seven |
| `WorkflowSlotLayoutBehavior` | Keeps slot anchors in sync with node layout | all seven |
| `WorkflowMinimapOverlay` | Thumbnail of nodes/links with a draggable viewport indicator | all seven |
| `WorkflowLinkOverlay` | MAUI-only: viewport-sized paint layer for the links that have no view of their own (the immediate-mode hosts and the frames before a pooled link view materializes) | MAUI |
| `WorkflowLinkBounds` | Jalium-only: static helper that positions a link view from its canvas-local points and reports the origin | Jalium |
| `WorkflowGridDecorator` | Grid/ruler decorator element. WinForms ships a `Panel` subclass implementing `IWorkflowGridDecorator`; Razor ships a component; the XAML adapters (including Jalium) get one from the `*-v-decorator` template | WinForms, Razor (WPF/Avalonia/WinUI/MAUI/Jalium: template) |
| `WorkflowTreeView` | Composite host control the generated WinForms tree-view item derives from (`PART_*` named parts, view factories) | WinForms |
| `WorkflowNodeAttachment` / `WorkflowSlotAttachment` / `WorkflowLinkAttachment` | Per-role **attachments**: a generated WinForms item template calls `Attach(Control)` on a control it already owns instead of deriving from a base class | WinForms |
| `WorkflowTemplateSelector` | Factory that binds a model to its view — the type the generated WinForms selector derives from | WinForms |
| `IWorkflowTemplateSelector` | Factory contract mirroring a `DataTemplateSelector` (WinForms only; Jalium uses `DataTemplateSelector`) | WinForms |
| `WorkflowEvents` | Attached `Node` / `Slot` / `Tree` properties that hand a component's **model** events to an `IWorkflow*EventSink` through `WorkflowEventRelay` | WPF, WinUI, Avalonia, MAUI, Jalium |
| `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | Data-exchange contracts the overlays implement; **defined in Core**, namespace `VeloxDev.WorkflowSystem` | all seven (implemented by overlays) |

## Pages

- [surface](00_surface/index.md) — `WorkflowSurfaceBehavior` and `WorkflowCanvasTransformBehavior`.
- [view-pool](01_view-pool/index.md) — `ViewPool`, `ViewManager`, and the template-selector contract.
- [node-slot](02_node-slot/index.md) — `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`.
- [minimap](03_minimap/index.md) — `WorkflowMinimapOverlay` and the `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` contracts.
- [adapter-overlays](04_adapter-overlays/index.md) — adapter-specific overlay / host types (`WorkflowLinkOverlay`, Jalium `WorkflowLinkBounds` and its template-supplied pieces, Razor component helpers).
