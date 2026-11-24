# Minimap

A minimap is a second, much smaller reading of the same tree: every node becomes a thumbnail, and a rectangle shows what the surface currently displays. Dragging inside the minimap moves the viewport. The feature is a Core pipeline plus one overlay control per adapter; the surface behavior is what keeps the pipeline fed.

## What the feature covers

- **One draw pass from cached geometry.** The Core `MinimapPipelineCore` subscribes to tree, node and link changes, marks itself dirty, and rebuilds the mapping once before the next render. A burst of property changes costs one pass.
- **Placement in the free corner.** The minimap is 200 × 140 by default, 12 px from the corner, clamped to the area left by the ruler band and the scrollbars.
- **Drag to navigate.** A press inside the minimap centres the viewport on that point; moving continues to centre, and the surface's scroll offsets are written through the adapter's viewport layer.
- **Custom drawing is a virtual method.** An adapter overlay draws background, node thumbnails and the viewport block; a subclass overrides `DrawMinimap` or just sets brushes.

## Where each piece lives

| Layer | Types | Responsibility |
|---|---|---|
| Core | `MinimapPipelineCore<TSurface,TRenderer,TViewport,TInput>`, `MinimapHostCore<...>` | Tree subscription, dirty debounce, content/viewport mapping, placement, drag math. |
| Core | `IMinimapRenderer<TSurface>`, `IMinimapViewportHost`, `IMinimapInputHost` | The three platform layers the pipeline composes. |
| Core | `MinimapDrawContext`, `MinimapMetrics`, `SurfaceAvailableArea` | One pass's geometry and the sizing/placement inputs. |
| Core | `IWorkflowMinimapOverlay` | The data-exchange contract the surface pushes into. |
| WPF | `WorkflowMinimapOverlay`, `MinimapPipeline`, `MinimapRenderer`, `MinimapViewportHost`, `MinimapInputHost` | The WPF closure, dependency properties and drawing. |
| WPF | `WorkflowSurfaceBehavior` | Resolves `MinimapOverlayName`, pushes tree, offsets, viewport and available corner. |

The other six adapters each ship a `WorkflowMinimapOverlay` with the same role; Razor's is a component, not a `FrameworkElement`.

## Pages

- [Prerequisites](00_prerequisites/index.md) — targets, packages and the demo.
- [Attach the overlay](01_attach-overlay/index.md) — name it, give it the scroll viewer, let the surface feed it.
- [Appearance and navigation](02_appearance-navigation/index.md) — size, brushes, visibility, drag, custom drawing.
- [Verification](03_verification/index.md) — run it, drag it, complete code and run declaration.

## What one pass draws

The default WPF drawing is the minimap frame, a thumbnail per node in `MappedNodes`, and the viewport indicator in `MappedViewport`. It does not draw links. `MinimapDrawContext` carries node rectangles and the viewport rectangle, not link geometry; a subclass that wants links must compute them from `context.Tree`.

## Evidence

- Demo: `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/MinimapOverlay.cs`; the full demo at `Examples/Workflow/Avalonia/Demo/Views/Workflow/MinimapOverlay.cs` and `Examples/Workflow/WPF/Demo/Views/Workflow/MinimapOverlay.cs`.
- Tests: `Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/MinimapPipelineTests.cs`, `MinimapDrawContextTests.cs`; `Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/MinimapHeadlessTests.cs`.
