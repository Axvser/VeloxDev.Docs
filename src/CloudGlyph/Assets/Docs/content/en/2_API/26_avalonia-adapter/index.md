# Avalonia adapter

`VeloxDev.Avalonia` closes the same seven workflow roles as the WPF adapter, registered through `AvaloniaProperty` and resolved with `FindControl`. Compiled bindings are the demos' default, so templates carry a concrete `x:DataType`. The public surface is namespace `VeloxDev.WorkflowSystem.AttachedBehaviors` (assembly `VeloxDev.Avalonia`), plus `VeloxDev.WorkflowSystem.ViewHosting`, `VeloxDev.TransitionSystem` and `VeloxDev.DynamicTheme`.

| Role | Avalonia type |
| --- | --- |
| Surface host | `WorkflowSurfaceBehavior` |
| Canvas transform | `WorkflowCanvasTransformBehavior` |
| Node drag | `WorkflowNodeDragBehavior` |
| Slot connection | `WorkflowSlotConnectionBehavior` |
| Slot layout | `WorkflowSlotLayoutBehavior` |
| View pool | `ViewPool` |
| Minimap | `WorkflowMinimapOverlay` |
| Model events | `WorkflowEvents` |

The grid decorator is host-supplied: an element named by `GridDecoratorName` implements `IWorkflowGridDecorator`. The adapter registers its wheel handlers with `RoutingStrategies.Tunnel` because Avalonia has no preview-wheel phase.

The reference demo is `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/`; the project sits at `Demo/Demo/`, so the views are one level deeper than the WPF demo. The Avalonia headless suite also drives real pointer input for the Ctrl+wheel direction and the `[0.1, 10]` zoom clamp.

## Pages

- [Surface behavior](00_surface-behavior/index.md) — the attached points and `Refresh`.
- [Canvas transform and node drag](01_canvas-transform-and-node-drag/index.md) — the transform carrier and the drag behavior.
- [Slot behaviors](02_slot-behaviors/index.md) — connection and anchor measurement.
- [View pool](03_view-pool/index.md) — the attached pool, its pipeline and the Avalonia pool policy.
- [View hosting](04_view-hosting/index.md) — the concrete hosting layers.
- [Minimap overlay](05_minimap-overlay/index.md) — the overlay element and its pipeline.
- [Workflow events](06_events/index.md) — the sink attached properties.
- [Transition and theme bridges](07_transition-and-theme-bridges/index.md) — the transition and theme types.

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**Expected result:** the surface resolves the named parts, publishes the viewport, and registers `WorkflowInput.Scroller` / `Navigator`; the plain wheel scrolls through the adapter rather than `ScrollViewer` inertia.
