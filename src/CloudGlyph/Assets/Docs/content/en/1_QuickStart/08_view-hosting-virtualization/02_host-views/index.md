# Host views

A `ViewPool` attached to a `Panel` consumes the visible set and materialises one view per item. It is not an `ItemsControl`: the pool keeps its own active map, promotes batches on the host's dispatcher, and recycles views by runtime type instead of recreating them.

## Attach the pool

```xml
<Canvas x:Name="PART_Canvas"
        Width="{Binding Layout.ActualSize.Width}"
        Height="{Binding Layout.ActualSize.Height}"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

| Attached property | Type | Meaning |
|---|---|---|
| `ItemsSource` | `INotifyCollectionChanged` | The visible set. Bind `Helper.VisibleItems`, never `tree.Nodes`. |
| `TemplateSelector` | `DataTemplateSelector` (WPF) | Chooses a template by runtime type. Optional; without it the panel's own `DataTemplates` are used. |

Changing either property disposes the old pipeline and rebuilds it, so a source or selector swap never leaves an old collection handler attached. Unloading the panel disposes the system as well.

## The selector must cover links

`VisibleItems` always contains the tree's `VirtualLink`, plus real links whose endpoints are visible. A selector that handles only `INodeComponent` returns `null` for a link; the pool treats `null` as "this runtime type is unsupported" and permanently caches that verdict for the system's lifetime.

```csharp
public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    public override DataTemplate? SelectTemplate(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate,
            INodeComponent => NodeTemplate,
            _ => null,
        };
}
```

Let the link template handle both real and virtual links. A virtual link is a link whose two endpoint slots are not attached to nodes; its `IsVisible` is `false` until a connection drag starts. Binding the view's visibility to `IsVisible` is enough.

## What the pool does with one item

```mermaid
flowchart LR
    Add["Visible set Add"] --> Pending["pending queue"]
    Pending --> Batch["Scheduler batch"]
    Batch --> Factory["Factory.WantsItem"]
    Factory --> Create["CreateView or reuse"]
    Create --> Activate["Activate (DataContext)"]
    Activate --> Attach["Attach (Children.Add)"]
    Attach --> Arrange["Arrange / SetZOrder"]
```

- The batch is scheduled on the adapter's dispatcher; it never runs inline while the collection is changing.
- `Activate` sets the `DataContext`, `Attach` adds the view to the host, `Arrange` writes geometry where the platform is imperative, and `Measure` is an optional hook.
- A removed item is deactivated, detached and returned to the pool. Removal past `MaxRecycledViewsPerType` destroys the view instead of hiding it; hiding alone would keep the host rooting it.
- A failed item reports `Diagnostics.Failed(item, stage, exception)` and the rest of the batch continues.

## Batching and the default policy

WPF and the other five pool-based adapters use Core's `AdaptiveViewPoolPolicy` by default. It starts at 64 items per batch and an 8 ms frame budget, and adjusts from measured throughput and pending count:

| Pending | Frame budget target |
|---|---|
| more than 1024 | 16 ms |
| more than 256 | 12 ms |
| otherwise | 8 ms |

Batch size grows by up to 1.25× and shrinks to 0.8× with hysteresis. `ViewPoolOptions` exposes every parameter and `AdaptiveViewPoolPolicy.FromOptions(options)` can replace the policy wholesale. A platform that wants a fixed policy supplies one, as the Avalonia adapter's `ViewPoolPolicy` does.

The contract is one batch per frame at most: `IViewScheduler.Schedule` must post, never call the batch synchronously. The only exception is a host with no dispatcher (WinForms without a handle), where the implementation runs inline but queues a re-entrant next batch instead of recursing.

## Layers and the link overlay

The Core contract is five narrow layers — `IViewFactory`, `IViewContainer`, `IViewArranger`, `IViewScheduler`, `IViewDiagnostics` — plus optional `IViewLayerPolicy`, `IViewLinkLayer` and `IViewMeasureHost`. `ViewSourcePipelineCore` composes them; an adapter's `ViewSourcePipeline` closes the generic parameters. A platform that draws links in an overlay (MAUI) sets `LinkLayer.IsActive = true` and `Handles` for links; those items never enter the main pool.

## Expected result

- Four visible nodes produce four child views under `PART_Canvas`, not one per node in the graph.
- Scrolling removes views for nodes that left and reuses them for nodes that entered; a view handed to another node receives a new `DataContext`.
- Changing `TemplateSelector` at runtime rebuilds the pool once and does not attach a second detach handler.
- Adding a link to `VisibleItems` while the selector has no link template produces no view and no repeated exception; the unsupported type is cached.

## Next

[Verification](../03_verification/index.md) puts the helper and the pool together in one runnable sample.
