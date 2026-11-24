# View Hosting and Virtualization

Virtualization has two halves. Core maintains a spatial index and a visible set on the tree helper; a view pool turns that set into one UI view per item and recycles views as the viewport moves. This section catalogues the pool, the five-layer host contract, the spatial index, and the WPF closure of those layers.

All Core types are in `VeloxDev.WorkflowSystem` unless a page says otherwise. `WorkflowSpatialEx` lives in `VeloxDev.WorkflowSystem.StandardEx`; the WPF types live in `VeloxDev.WorkflowSystem.ViewHosting` and `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Pages

- [View pool](00_view-pool/index.md) — `ViewPool`, `ViewPoolCore`, `ViewPoolOptions`, `AdaptiveViewPoolPolicy`, and `IViewPoolPolicy`.
- [View host contract](01_view-host-contract/index.md) — the nine layer interfaces, `ViewStage`, `ViewHostCore`, and `ViewSourcePipelineCore`.
- [Spatial virtualization](02_spatial-virtualization/index.md) — the `TreeHelper` switch, `Viewport`, `SpatialGridHashMap<T>`, `WorkflowSpatialManager`, and the `WorkflowSpatialEx` extensions.
- [Adapter view pool](03_adapter-viewpool/index.md) — the WPF `ViewPool` attached properties and the layer classes that close the contract.

## Layer split

| Layer | Types | Responsibility |
|---|---|---|
| Core | `TreeHelper(double)`, `VisibleItems`, `Viewport`, `MarkDirty`, `WithSynchronizationContext` | The virtualization switch and the visible-set observable. |
| Core | `WorkflowSpatialManager`, `SpatialGridHashMap<T>`, `WorkflowSpatialEx` | Node grid, node-pair grid, viewport query, ruler inset. |
| Core | `ViewPool<...>`, `ViewPoolCore<...>`, `ViewHostCore<...>`, `ViewSourcePipelineCore<...>` | Batching, recycling, and contract composition. |
| Core | `AdaptiveViewPoolPolicy`, `ViewPoolOptions`, `IViewPoolPolicy` | Batch and recycle policy. |
| Adapter (WPF shown) | `ViewPool.ItemsSource`, `ViewPool.TemplateSelector`, `ViewSourcePipeline`, `ViewFactory`, `ViewContainer`, `ViewScheduler` | The platform closure of each layer. |

## Related

- [View Hosting and Virtualization Quick Start](../../1_QuickStart/08_view-hosting-virtualization/index.md) wires a helper and a pool in a runnable host.
- [Minimap](../09_minimap/index.md) consumes the same viewport and visible set.
