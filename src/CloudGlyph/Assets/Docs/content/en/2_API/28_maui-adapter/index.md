# MAUI adapter

`VeloxDev.MAUI` closes the workflow surface for .NET MAUI. The host is a `ContentView`, the tree arrives as its `BindingContext`, and links are drawn by one viewport-sized `WorkflowLinkOverlay` instead of one pooled view per link. The adapter has no `WorkflowCanvasTransformBehavior`; the surface and the view arranger own the geometry. The public surface is namespace `VeloxDev.WorkflowSystem.AttachedBehaviors` (assembly `VeloxDev.MAUI`), plus `VeloxDev.WorkflowSystem.ViewHosting`, `VeloxDev.TransitionSystem` and `VeloxDev.DynamicTheme`.

| Role | MAUI type |
| --- | --- |
| Surface host | `WorkflowSurfaceBehavior` |
| Node drag | `WorkflowNodeDragBehavior` |
| Slot connection | `WorkflowSlotConnectionBehavior` |
| Slot layout | `WorkflowSlotLayoutBehavior` |
| View pool | `ViewPool` |
| Link rendering | `WorkflowLinkOverlay` |
| Minimap | `WorkflowMinimapOverlay` |
| Model events | `WorkflowEvents` |

The reference demo is `Examples/Workflow/MAUI Trimmed/Demo/Controls/Workflow/` — `Controls/`, not `Views/`. MAUI has a demo but **no headless conformance suite**: `Src/Test/Headless/README.md` records that it has no windowless host.

## Pages

- [Surface behavior](00_surface-behavior/index.md) — attached points, `Refresh`, gestures and `RequestViewportRestore`.
- [Node drag](01_node-drag/index.md) — the drag behavior.
- [Slot behaviors](02_slot-behaviors/index.md) — connection (including the candidate-receiver probe) and layout.
- [View pool](03_view-pool/index.md) — the attached pool and its pipeline.
- [View hosting](04_view-hosting/index.md) — the concrete hosting layers.
- [Link overlay](05_link-overlay/index.md) — the single viewport-sized link layer.
- [Minimap overlay](06_minimap-overlay/index.md) — the minimap and its pipeline.
- [Workflow events](07_events/index.md) — the sink attached properties.
- [Transition and theme bridges](08_transition-and-theme-bridges/index.md) — the transition and theme types.

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**Expected result:** the surface resolves the named parts, pools node views, and the link overlay paints the links; the tree is the `ContentView.BindingContext`.
