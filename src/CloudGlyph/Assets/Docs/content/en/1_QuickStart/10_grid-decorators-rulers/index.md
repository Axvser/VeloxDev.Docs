# Grid Decorators and Rulers

A grid decorator is the surface layer that draws the canvas grid and the floating rulers around the canvas. It is not part of the scroll content: it wraps the scroll viewer, sees the scroll and content offsets the surface pushes into it, and paints lines that stay aligned while the content pans.

## What the feature covers

- **A small data contract.** `IWorkflowGridDecorator` has two scroll offsets, two content offsets, and a `RulerBand` thickness. The surface behavior writes the offsets before each render pass; the decorator reads them in `OnRender`.
- **The canvas grid.** `WorkflowSurfaceMath` supplies the four formulas a decorator needs: visible left/top, first snapped line, and the canvas-to-content conversion on each axis.
- **Floating rulers.** The top and left bands are drawn above the content and are hit-test transparent; the canvas is translated by the band thickness so the origin sits at the band edge.
- **Virtualization and the minimap respect the band.** `RulerBand` is pushed to `SetVirtualizeInset` so nodes under the ruler are not culled early, and becomes the minimap's `AvailableTop`.

## Where each piece lives

| Layer | Types | Responsibility |
|---|---|---|
| Core | `IWorkflowGridDecorator` | The offsets and `RulerBand` contract. |
| Core | `WorkflowSurfaceMath.GridCanvasLeft` / `GridCanvasTop` / `GridFirstLine` / `GridX` / `GridY` | All grid arithmetic, written once. |
| Core | `SurfaceMetricsPush.PushGrid`, `SetVirtualizeInset` | Pushing offsets and the ruler inset. |
| WPF | `WorkflowSurfaceBehavior` | Resolves `GridDecoratorName` and pushes on every scroll, pan and zoom. |
| Template / demo | `WorkflowGridDecorator` | The drawing class: item templates `wpf-v-decorator`, `ava-v-decorator`, … and the demos' local classes. |

The adapters do not ship a grid decorator type. You generate one from the item template or write the class; the platform-specific part is only the drawing API.

## Pages

- [Prerequisites](00_prerequisites/index.md) — targets, packages, the decorator item template.
- [Contract and placement](01_contract-placement/index.md) — the interface, where the decorator sits, what the surface pushes.
- [Draw grid and rulers](02_draw-grid-rulers/index.md) — the four formulas, layers, labels and invalidation.
- [Verification](03_verification/index.md) — run it, pan and zoom, complete code and run declaration.

## Why the ruler band is not cosmetic

`RulerBand` is read twice per pass. The grid uses it to offset the canvas; virtualization uses it to inflate the visible query; the minimap uses it as the top of its available corner. Reporting a band of `0` when you draw one makes nodes under the ruler disappear one band too early, and puts the minimap on top of the ruler.

## Evidence

- Demo: `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/WorkflowGridDecorator.cs`; full demos use the same class shape with a workbench palette.
- Template: `Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-grid-decorator/TemplateClass.cs` (short name `wpf-v-decorator`), and the equivalent in the other six packs.
- Tests: `Src/Test/Headless/VeloxDev.Razor.Headless.Tests/Tests/GridDecoratorTests.cs`; `Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/WorkflowSurfaceHeadlessTests.cs` (`Scroll_PushesOffsetsToTheGridDecorator`); `Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/SurfacePipelineTests.cs` (`SurfaceMetricsPush_PushGrid_WritesOffsets`).
