# Minimap

A minimap is a second, much smaller reading of the same tree: every node becomes a thumbnail and a rectangle shows the current viewport. Core owns the pipeline, the mapping math, and three platform seams; each adapter supplies an overlay and a renderer.

All Core types are in `VeloxDev.WorkflowSystem`. The WPF overlay is in `VeloxDev.WorkflowSystem.AttachedBehaviors`; its pipeline and platform classes are in `VeloxDev.WorkflowSystem.ViewHosting`.

## Pages

- [Minimap contract](00_minimap-contract/index.md) — the overlay, renderer, viewport-host, and input-host interfaces, plus `MinimapMetrics` and `SurfaceAvailableArea`.
- [Pipeline](01_pipeline/index.md) — `MinimapHostCore`, `MinimapPipelineCore`, and `MinimapDrawContext`.
- [Minimap math](02_minimap-math/index.md) — the `WorkflowSurfaceMath` fit, mapping, and drag functions.
- [Adapter overlay](03_adapter-overlay/index.md) — the WPF `WorkflowMinimapOverlay` and its three platform classes.

## Layer split

| Layer | Types | Responsibility |
|---|---|---|
| Core | `IWorkflowMinimapOverlay` | Data pushed by the surface behavior. |
| Core | `IMinimapRenderer<TSurface>`, `IMinimapViewportHost`, `IMinimapInputHost` | The three platform seams the pipeline composes. |
| Core | `MinimapPipelineCore<...>`, `MinimapHostCore<...>` | Tree subscription, dirty debounce, mapping, placement, drag. |
| Core | `MinimapDrawContext`, `MinimapMetrics`, `SurfaceAvailableArea` | One pass's geometry and the sizing inputs. |
| Core | `WorkflowSurfaceMath` (minimap members) | Fit, local mapping, viewport rectangle, drag conversion. |
| Adapter (WPF shown) | `WorkflowMinimapOverlay`, `MinimapPipeline`, `MinimapRenderer`, `MinimapViewportHost`, `MinimapInputHost` | Property system, drawing, scroll apply, pointer capture. |

## Related

- [Minimap Quick Start](../../1_QuickStart/09_minimap/index.md) attaches an overlay to a surface.
- [View Hosting and Virtualization](../08_view-hosting-virtualization/index.md) supplies the viewport and visible set the minimap reads.
- [Canvas Input and Navigation](../07_canvas-input-navigation/index.md) defines the surface metrics the overlay receives.
