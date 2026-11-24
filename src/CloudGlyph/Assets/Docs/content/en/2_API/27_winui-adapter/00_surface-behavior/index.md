# Surface behavior

`WorkflowSurfaceBehavior` resolves the surface's named parts, feeds the viewport, starts panning, hooks zoom, forwards pointer and key input, opens the link menu, and registers the scroll/navigation capabilities. WinUI has no preview pointer phase, so the wheel is taken on the canvas with `handledEventsToo: true`, and panning moves the canvas with a composition translation instead of binding a render transform.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WinUI`.

## WorkflowSurfaceBehavior

**Signature:** `sealed class WorkflowSurfaceBehavior : DependencyObject`

### Attached properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Master switch. |
| `ScrollViewerName` | `string?` | `null` | Scroll container whose offsets define the measured viewport. |
| `CanvasName` | `string?` | `null` | Canvas/panel the view pool fills. |
| `GridDecoratorName` | `string?` | `null` | Element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | Element whose blank-area press starts panning. |
| `MinimapOverlayName` | `string?` | `null` | Element implementing `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables the Ctrl+wheel zoom gesture. |
| `LinkMenuKey` | `string?` | `null` | Resource key of the link `MenuFlyout`. |

Accessors are the standard static pairs, for example `GetIsEnabled(DependencyObject)` / `SetIsEnabled(DependencyObject, bool)` and `GetScrollViewerName` / `SetScrollViewerName`.

`MenuFlyout` has no `DataContext`, so the adapter feeds each `MenuFlyoutItem.DataContext` the pressed link. The adapter also suspends `WorkflowInput` while the flyout is open.

### Methods

| Method | Signature | Description |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | Re-resolves the named parts and rebinds the surface. |

A missing name disables that part silently. Call `Refresh` after `Loaded` or after a template change; the name scope is ready at that point.

### Panning

WinUI children do not bind a render transform. The surface applies the pan as a composition translation on the canvas (`state.Canvas.Translation`). A custom link view must therefore bake the same `ActualOffset` into its geometry and position itself at the negative offset; the next page of the demo pair shows that frame.

```csharp
public sealed partial class WorkflowSurface : UserControl
{
    public WorkflowSurface()
    {
        InitializeComponent();
        DataContext = new TreeViewModel();
        Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
    }
}
```

**Expected result:** pan and zoom move the whole canvas, the viewport is published, and a detached surface stops writing the model.
