# WinUI adapter

`VeloxDev.WinUI` closes the seven workflow roles for WinUI 3 / Windows App SDK. Two platform shapes differ from the XAML desktop adapters: the canvas pan is a composition translation rather than an attached render transform, and a link view places itself at the negative canvas offset so geometry never leaves its own box. The public surface is namespace `VeloxDev.WorkflowSystem.AttachedBehaviors` (assembly `VeloxDev.WinUI`), plus `VeloxDev.WorkflowSystem.ViewHosting`, `VeloxDev.TransitionSystem` and `VeloxDev.DynamicTheme`.

| Role | WinUI type |
| --- | --- |
| Surface host | `WorkflowSurfaceBehavior` |
| Canvas transform | `WorkflowCanvasTransformBehavior` |
| Node drag | `WorkflowNodeDragBehavior` |
| Slot connection | `WorkflowSlotConnectionBehavior` |
| Slot layout | `WorkflowSlotLayoutBehavior` |
| View pool | `ViewPool` |
| Minimap | `WorkflowMinimapOverlay` |
| Model events | `WorkflowEvents` |

The grid decorator is host-supplied. The reference demo is `Examples/Workflow/WinUI Trimmed/Demo/Views/Workflow/`; read `TreeView.xaml` and `LinkView.xaml.cs` together, because they are the pair implementing the offset frame.

WinUI has a demo but **no headless conformance suite**: `Src/Test/Headless/README.md` records that it has no windowless host. Every page here documents a demo-verified surface.

## Pages

- [Surface behavior](00_surface-behavior/index.md) — attached points, `Refresh`, and the composition-translation pan.
- [Canvas transform and node drag](01_canvas-transform-and-node-drag/index.md) — the transform carrier and the drag behavior.
- [Slot behaviors](02_slot-behaviors/index.md) — connection and canvas-local anchor measurement.
- [View pool](03_view-pool/index.md) — the attached pool and its pipeline.
- [View hosting](04_view-hosting/index.md) — the hosting layers, including the internal layout tracker.
- [Minimap overlay](05_minimap-overlay/index.md) — the overlay and its pipeline.
- [Workflow events](06_events/index.md) — the sink attached properties.
- [Transition and theme bridges](07_transition-and-theme-bridges/index.md) — the transition and theme types.

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
host.Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(host);
```

**Expected result:** the surface resolves the named parts after `Loaded`, pans by translating the canvas, and registers `WorkflowInput.Scroller` / `Navigator`.
