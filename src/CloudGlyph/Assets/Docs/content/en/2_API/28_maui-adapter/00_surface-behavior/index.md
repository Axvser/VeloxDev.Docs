# Surface behavior

`WorkflowSurfaceBehavior` resolves the named parts, feeds the viewport, owns pan/pinch gestures plus the Windows wheel hook, routes input, opens the link menu, and registers the scroll/navigation capabilities. MAUI has no render-transform carrier; the surface and the view arranger own the geometry.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.MAUI`.

## WorkflowSurfaceBehavior

**Signature:** `sealed class WorkflowSurfaceBehavior` (a static attached-property class; no `BindableObject` base)

### Attached properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Master switch. |
| `ScrollViewerName` | `string?` | `null` | `ScrollView` whose offsets define the measured viewport. |
| `CanvasName` | `string?` | `null` | `AbsoluteLayout` the view pool fills. |
| `GridDecoratorName` | `string?` | `null` | Element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | Element whose blank-area press starts panning. |
| `MinimapOverlayName` | `string?` | `null` | Element implementing `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables pinch and the Ctrl+wheel zoom gesture. |
| `LinkMenuKey` | `string?` | `null` | Resource key of the link `MenuFlyout`. |

Accessors are the standard static pairs taking a `BindableObject`, for example `GetIsEnabled` / `SetIsEnabled` and `GetScrollViewerName` / `SetScrollViewerName`.

`MenuFlyout` has no `DataContext`, so the adapter feeds each `MenuFlyoutItem.DataContext` the pressed link. On Windows it opens the native flyout; off Windows it materializes its own overlay layer positioned by `Margin`.

### Methods

| Method | Signature | Description |
| --- | --- | --- |
| `Refresh` | `static void Refresh(ContentView host)` | Re-resolves the named parts and rebinds the surface. |
| `RequestViewportRestore` | `static void RequestViewportRestore(ContentView host, double viewportX, double viewportY)` | Writes the canvas-local position to `Layout.ViewportOffset`, captures it with a fresh `SurfaceViewportRestoreCore`, and refreshes so the next layout pass restores it. Ignored when `IsEnabled` is false. |

`RequestViewportRestore` throws `ArgumentNullException` for a null host. It is the MAUI-specific entry for an explicit restore; the ordinary attach path captures the saved viewport itself.

### Gestures

- **Pan** uses a `PanGestureRecognizer`, plus native pointer handling on Windows.
- **Zoom** uses a `PinchGestureRecognizer` for touch and a `#if WINDOWS` wheel hook.
- The adapter sets the Windows `ScrollViewer.ManipulationMode` to `None` so its programmatic `ChangeView` is the only scroll driver; leave that value alone.
- The candidate receiver during a connection drag is reported by the slot-connection behavior, not the surface, because a viewport-sized overlay cannot answer "which slot" by visual hit-testing.

```csharp
public partial class TreeView : ContentView
{
    public TreeView()
    {
        InitializeComponent();
        BindingContextChanged += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
    }
}
```

**Expected result:** the surface subscribes on `BindingContextChanged`, pans and zooms, and writes the viewport; a detached surface stops writing it.
