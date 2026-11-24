# View Hosting and Virtualization

A large workflow has more nodes than a viewport can usefully show. VeloxDev splits the problem in two: a **spatial index** decides which components are visible for a given viewport, and a **view pool** turns that visible set into one UI view per item, recycling views as the viewport moves.

## What the feature covers

- **A visible set, not the whole graph.** `TreeHelper(cellSize)` turns virtualization on; `Helper.VisibleItems` is an `ObservableCollection<IWorkflowComponent>` containing the virtual link, the nodes near the viewport, and the links between them.
- **One view per visible item.** An adapter's `ViewPool` attached property consumes `VisibleItems`, creates a view through your template selector, and recycles it by runtime type when the item leaves.
- **A five-layer contract.** Factory, container, arranger, scheduler and diagnostics are separate interfaces in Core, composed by `ViewSourcePipelineCore`; each adapter closes the layers with its own property system.
- **Optional policies.** `AdaptiveViewPoolPolicy` tunes batch size and frame budget from measured throughput; a platform can replace it with a fixed policy.

## Where each piece lives

| Layer | Types | Responsibility |
|---|---|---|
| Core | `TreeHelper(double cellSize)`, `Viewport`, `VisibleItems`, `MarkDirty`, `WithSynchronizationContext` | The virtualization switch and the visible-set observable. |
| Core | `WorkflowSpatialManager`, `SpatialGridHashMap<T>`, `WorkflowSpatialEx.Virtualize` / `EnableMap` / `SetVirtualizeInset` | Node grid, node-pair grid for links, viewport query, ruler inset. |
| Core | `ViewPoolCore<...>`, `ViewPool<...>`, `ViewHostCore<...>`, `ViewSourcePipelineCore<...>`, `AdaptiveViewPoolPolicy`, `ViewPoolOptions` | The pool, batching, recycling and the contract composition. |
| WPF | `ViewPool.ItemsSource` / `ViewPool.TemplateSelector`, `ViewSourcePipeline`, `ViewFactory`, `ViewContainer`, `ViewScheduler` | The WPF closure of the layers. |
| WPF | `WorkflowSurfaceBehavior` | Pushes the viewport into the tree, which is what triggers virtualization. |

## Pages

- [Prerequisites](00_prerequisites/index.md) — targets, packages and the demo.
- [Enable virtualization](01_enable-virtualization/index.md) — the helper, the cell size, the visible set and its thread rules.
- [Host views](02_host-views/index.md) — attach the pool, write the selector, know what is recycled.
- [Verification](03_verification/index.md) — run it, count visible items, complete code and run declaration.

## The two halves

```mermaid
flowchart LR
    Scroll["Scroll / zoom"] --> Viewport["TreeHelper.Viewport"]
    Viewport --> Virtualize["WorkflowSpatialEx.Virtualize"]
    Virtualize --> Visible["Helper.VisibleItems"]
    Visible --> Pool["ViewPool.ItemsSource"]
    Pool --> View["One view per item"]
    View --> Recycle["Back to the pool on removal"]
```

The left half is Core geometry and runs on the thread that installed the helper. The right half is the adapter's pool and must run on the host UI thread; the scheduler is the only thread boundary.

## Evidence

- Demo: `Examples/Workflow/Avalonia Trimmed/Demo/Demo/ViewModels/Workflow/Helper/VirtualizeHelper.cs`, `TreeView.axaml`, `TreeView.axaml.cs`; the WPF Trimmed mirror uses the same shape.
- Tests: `Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/ViewPoolTests.cs`, `AdaptiveViewPoolPolicyTests.cs`, `SpatialIndexFreshnessTests.cs`, `TreeHelperTickTests.cs`; `Src/Test/Headless/VeloxDev.Avalonia.Headless.Tests/Tests/ViewPoolHeadlessTests.cs`.
