# API — Attached Behaviors · ViewPool & ViewManager

`ViewPool` + `ViewManager` provide object-pooled view virtualization for the workflow surface: as items enter/leave the bound collection, the manager materializes one view per item, reuses pooled views by type, and hides removed ones.

## Class: `ViewPool`

Attached object-pool support that turns a container into a virtualized host. On the XAML-style adapters it is an attached-property holder; on Razor it is a component; on WinForms it is a static holder with `Control`-keyed state.

| Adapter | Shape | `ItemsSource` (type) | `TemplateSelector` (type) |
|---|---|---|---|
| WPF | `sealed class : DependencyObject` | attached `INotifyCollectionChanged?` | attached `DataTemplateSelector?` |
| Avalonia | `sealed class : AvaloniaObject` | `INotifyCollectionChanged?` | `IDataTemplate?` |
| WinUI | `sealed class : DependencyObject` | `INotifyCollectionChanged?` | `DataTemplateSelector?` |
| MAUI | `sealed class` | `BindableProperty` `INotifyCollectionChanged?` | `DataTemplateSelector?` |
| WinForms | `sealed class` | static `SetItemsSource(Control, INotifyCollectionChanged?)` | static `SetTemplateSelector(Control, IWorkflowTemplateSelector?)` |
| Jalium | `public static class` | attached `INotifyCollectionChanged?` | attached `IWorkflowTemplateSelector?` |

Members follow the attached-property convention `GetItemsSource(container)` / `SetItemsSource(container, value)` (and likewise for `TemplateSelector`); the intended XAML use binds the collection into the container:

```xml
<Canvas ViewPool.ItemsSource="{Binding Helper.VisibleItems}" />
```

On change of `ItemsSource` (WPF/Avalonia/WinUI/MAUI) the pool creates a `ViewManager` for the container, attaches it to the collection, and cleans it up on `Unloaded` / old-value replacement. **Jalium** additionally exposes `internal static void UpdateRenderTransforms(Panel panel, Transform transform)` to mirror the surface's canvas transform onto pooled views.

## Class: `ViewManager`

Sealed per-container manager (created by `ViewPool`). It pools views per item `Type` in a `Queue`, keeps active views plus a pending batch, subscribes to collection change / item property change, and renders.

| Adapter | Constructor / factory | Extra public members |
|---|---|---|
| WPF | `ViewManager(Panel panel)` | `void Attach(INotifyCollectionChanged)`; `void Detach()` |
| Avalonia | `ViewManager(Panel panel, IDataTemplate? templateSelector = null)` | `void Attach(INotifyCollectionChanged)`; `void Detach()` |
| WinUI | `ViewManager(Panel panel)` | `void SetTemplateSelector(DataTemplateSelector?)`; `void Attach(INotifyCollectionChanged)`; `void Detach()` |
| MAUI | `ViewManager(Layout layout)` | `void Attach(INotifyCollectionChanged)`; `void Detach()` |
| WinForms | `ViewManager(Control host)` (`: IDisposable`) | `void SetTemplateSelector(IWorkflowTemplateSelector)`; `void Attach(INotifyCollectionChanged)`; `void Detach()`; `void Dispose()` |
| Jalium | `ViewManager(Panel host)` (`: IDisposable`) | `void SetTemplateSelector(IWorkflowTemplateSelector)`; `void Attach(INotifyCollectionChanged)`; `void Detach()`; `void Dispose()` |

**Rendering (verified, WPF):** renders in batches of **3** views per dispatcher `Background` tick. Removed items are collapsed (`Visibility.Collapsed`), unbound, and returned to the pool. The other adapters implement the same batching semantics; whether each reuses the exact batch size is `*inferred*`.

**Template lookup: the selector is consulted first, and only some adapters have anything to fall back to.** The four XAML-style adapters resolve `ViewPool.TemplateSelector` → resource-walk of the container → `Application.Current.Resources`, so a selector that does **not** match degrades to the platform's own lookup. **WinForms, Jalium and Razor have no platform lookup at all** — their pools create views only through the selector (the `IWorkflowTemplateSelector` factory, or the Razor `ItemTemplate` component), so a null or non-matching selector yields **no views and no error**. (Verified WPF/Avalonia/WinForms/Jalium/Razor; the MAUI chain is `*inferred*`.)
**One gotcha shared by the four:** the resolved template is cached **per item `Type`**, and the cache is read *before* the selector — a selector that decides **per instance** (same type, different view) only has its first verdict reused for the whole type.

**Avalonia note:** when a selector is present it is asked *with the item* — the pool builds the view as `IDataTemplate.Build(item)` — so a custom `IDataTemplate` must dispatch on that argument (`Match` picks the selector, `Build` picks and materializes the inner template). A selector that ignores the argument draws nothing, silently.

## Interface: `IWorkflowTemplateSelector`

WinForms and Jalium replace the XAML `DataTemplateSelector` / `IDataTemplate` with a small factory contract (namespace `VeloxDev.WorkflowSystem.AttachedBehaviors`). WinForms declares it in `ViewManager.cs`; Jalium in its own file.

| Adapter | Signature |
|---|---|
| WinForms | `Control CreateView(object item)` |
| Jalium | `FrameworkElement CreateView(object item)` |

## Razor component: `ViewPool`

`ViewPool.razor` + code-behind (`partial class ViewPool : ComponentBase`):

| Parameter | Type | Description |
|---|---|---|
| `ItemsSource` | `IEnumerable?` | Items to render. |
| `ItemTemplate` | `RenderFragment<object>?` | Per-item content. |
| `EmptyContent` | `RenderFragment?` | Rendered when the source is empty. |
| `KeySelector` | `Func<object, object>?` | Pooling/identity key. |
