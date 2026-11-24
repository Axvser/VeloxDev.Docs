# Adapter view pool

The WPF adapter closes the Core contract with one attached behavior and one pipeline class. The behavior is what a host uses; the pipeline and its layer classes are public for a host that composes its own pool.

Namespaces: `VeloxDev.WorkflowSystem.AttachedBehaviors` for the attached behavior, `VeloxDev.WorkflowSystem.ViewHosting` for the pipeline and layers.

## ViewPool (attached behavior)

```csharp
public sealed class ViewPool : DependencyObject
```

Attached to a `Panel` such as the `PART_Canvas`. Each panel gets exactly one pipeline, held in a `ConditionalWeakTable`.

### Attached properties

| Property | Type | Default | Description |
|---|---|---|---|
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | The visible set. Bind `Helper.VisibleItems`, never `tree.Nodes`. |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | Chooses a template by runtime type; when absent, the panel's own `DataTemplates` are used. |

| Accessor | Description |
|---|---|
| `GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)` | Reads or writes the source. |
| `GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)` | Reads or writes the selector. |

Changing either property disposes the old pipeline and builds a new one. Unloading the panel disposes it too.

Usage:

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

## ViewSourcePipeline

```csharp
public sealed class ViewSourcePipeline
    : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent,
        DispatcherPriority, ViewFactory, ViewContainer, ViewArranger,
        ViewScheduler, ViewDiagnostics>
```

| Signature | Description |
|---|---|
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | Composes the WPF layers and starts the pool. `poolPolicy` defaults to `new AdaptiveViewPoolPolicy()` (64 initial, 8 ms). |

Inherited members: `Pool` (a `ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority>`), `Dispose()`, and every `IViewHost` layer property.

## Layer classes

All are `public sealed` in `VeloxDev.WorkflowSystem.ViewHosting`.

### ViewFactory

```csharp
public ViewFactory(Panel panel, DataTemplateSelector? templateSelector);
public bool WantsItem(IWorkflowComponent item);      // always true
public FrameworkElement? CreateView(IWorkflowComponent item);
```

Resolves a template through the selector, then the panel's visual-tree resources, then application resources. The choice is cached by runtime type; no match yields `null`.

### ViewContainer

```csharp
public void Attach(Panel host, FrameworkElement view);      // adds to Children, idempotent
public void Detach(Panel host, FrameworkElement view);      // no-op
public void Activate(FrameworkElement view, IWorkflowComponent item); // DataContext + Visible
public void Deactivate(FrameworkElement view);              // clear DataContext + Collapsed
public void SetZOrder(FrameworkElement view, int zIndex);   // no-op; templates bind ZIndex
public void Destroy(Panel host, FrameworkElement view);     // removes from Children
```

### ViewArranger

```csharp
public void Arrange(FrameworkElement view, IWorkflowComponent item); // no-op
```

WPF templates own geometry through bindings.

### ViewScheduler

```csharp
public ViewScheduler(Dispatcher dispatcher);
public DispatcherPriority BatchPriority => DispatcherPriority.Background;
public bool Schedule(Action batch, DispatcherPriority priority); // Dispatcher.BeginInvoke
```

Returns `true` for every accepted post. The dispatcher argument throws `ArgumentNullException` when null.

### ViewDiagnostics

```csharp
public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception);
```

Writes `[ViewDiagnostics] {stage} failed for {type|batch}: {exception}` to the debug output.

### ViewLayerPolicy

```csharp
public int GetZOrder(IWorkflowComponent item); // always 0
```

### ViewLinkLayer

```csharp
public bool IsActive => false;
public bool Handles(IWorkflowComponent item) => false;
public void Render(Panel host, IReadOnlyList<IWorkflowComponent> items); // no-op
```

WPF uses one pooled view per link, so the link layer is inactive.

### ViewMeasureHost

```csharp
public void Measure(Panel host, FrameworkElement view, IWorkflowComponent item); // no-op
```

## Notes

- The selector must cover links. `VisibleItems` always contains the virtual link; a selector that handles only nodes caches "unsupported" for the link type.
- A view handed to another item receives a new `DataContext`; identity of the view is not identity of the item.
- The pool never runs a batch inline while the collection is changing; the scheduler is the thread boundary.
