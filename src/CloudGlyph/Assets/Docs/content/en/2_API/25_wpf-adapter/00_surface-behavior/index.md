# Surface behavior

`WorkflowSurfaceBehavior` resolves the surface's named parts, feeds the viewport, starts panning, hooks zoom, forwards pointer and key input, opens the link menu, and registers the scroll/navigation capabilities. It is a static attached-property class; the state lives on the host element.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WPF`.

## WorkflowSurfaceBehavior

**Signature:** `sealed class WorkflowSurfaceBehavior : DependencyObject`

### Attached properties

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Master switch; every other property is read only while it is `true`. |
| `ScrollViewerName` | `string?` | `null` | The scroll container whose offsets define the measured viewport. |
| `CanvasName` | `string?` | `null` | The canvas/panel the view pool fills. |
| `GridDecoratorName` | `string?` | `null` | The element implementing `IWorkflowGridDecorator`. |
| `PointerPressSourceName` | `string?` | `null` | The element whose blank-area press starts panning. |
| `MinimapOverlayName` | `string?` | `null` | The element implementing `IWorkflowMinimapOverlay`. |
| `ZoomEnabled` | `bool` | `false` | Enables the Ctrl+wheel zoom gesture. |
| `LinkMenuKey` | `string?` | `null` | Resource key of the link context menu, resolved after the resource dictionary exists. |

Each property has the standard pair, for example `GetIsEnabled(DependencyObject)` / `SetIsEnabled(DependencyObject, bool)`, `GetScrollViewerName` / `SetScrollViewerName`, and so on for all eight.

`LinkMenuKey` is a key rather than the menu itself because the property sits on the surface root, where a `{StaticResource}` would resolve before the dictionary that defines the menu. The adapter sets the pressed link as the menu's `DataContext` before opening it, suspends `WorkflowInput` while it is open, and resumes on close.

### Methods

| Method | Signature | Description |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | Re-resolves the named parts and rebinds the surface. Call it after replacing a template or re-hosting the surface. |

A missing name disables that part silently: there is no exception and no log, so a surface that does nothing is usually a name typo.

### Lifecycle

- `IsEnabled = true` attaches: resolves the names, captures the tree's saved viewport, schedules one restore, reads the tree from `DataContext`, registers `Scroller` / `Navigator`, and subscribes to the tree and its helpers.
- `IsEnabled = false` detaches: stops writing the model, clears the capabilities, and unsubscribes.
- A `DataContext` change rebinds to the new `ITreeComponent`.
- The adapter resolves `PART_*` through the `UserControl` name scope, not the visual tree. A code-built surface must register the names first.

```csharp
var scope = new NameScope();
NameScope.SetNameScope(host, scope);
scope.RegisterName("PART_ScrollViewer", scrollViewer);
scope.RegisterName("PART_Canvas", canvas);
scope.RegisterName("PART_SurfaceBorder", border);

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetPointerPressSourceName(host, "PART_SurfaceBorder");
WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**Expected result:** scrolling the `ScrollViewer` writes `tree.GetHelper().Viewport`; a detached surface stops writing it.
