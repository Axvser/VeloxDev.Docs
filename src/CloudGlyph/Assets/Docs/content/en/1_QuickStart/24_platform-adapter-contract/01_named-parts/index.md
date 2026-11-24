# Named Parts

A workflow surface is assembled from **seven view roles**. Six are supplied by an adapter; the grid decorator and the minimap implement Core interfaces and are written or generated for the host. The surface finds each one by name, so the `PART_*` names are part of the contract rather than a demo convention.

| Role | Adapter class | Job |
|---|---|---|
| Surface host | `WorkflowSurfaceBehavior` | resolves the named children, feeds the viewport, starts panning, hooks zoom, forwards pointer/keys, opens the link menu, registers `WorkflowInput.Scroller` and `Navigator` |
| Canvas transform | `WorkflowCanvasTransformBehavior` | a value carrier the node and link views bind their `RenderTransform` to |
| View pool | `ViewPool` | object-pooled views over the visible-item collection |
| Node drag | `WorkflowNodeDragBehavior` | turns a drag on a node into `MoveCommand` |
| Slot connection | `WorkflowSlotConnectionBehavior` | press one port, release on another, connect them |
| Slot layout | `WorkflowSlotLayoutBehavior` | measures each port and writes its `Anchor` |
| Grid decorator / minimap | `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | grid, ruler and thumbnail; the XAML adapters do not ship a decorator |

## Attached points

These are the public attached properties of `WorkflowSurfaceBehavior`. The same names exist on the WPF, Avalonia, WinUI and MAUI adapters.

| Attached property | Meaning | Default |
|---|---|---|
| `IsEnabled` | master switch; every other property is read only while it is `true` | `false` |
| `ScrollViewerName` | the scroll container whose offsets define the measured viewport | `null` |
| `CanvasName` | the canvas/panel the view pool fills | `null` |
| `GridDecoratorName` | the element implementing `IWorkflowGridDecorator` | `null` |
| `MinimapOverlayName` | the element implementing `IWorkflowMinimapOverlay` | `null` |
| `PointerPressSourceName` | the element whose blank-area press starts panning | `null` |
| `ZoomEnabled` | enables the Ctrl+wheel zoom gesture | `false` |
| `LinkMenuKey` | resource key of the link context menu, resolved after the resource dictionary exists | `null` |

The supporting roles carry their own points: `WorkflowCanvasTransformBehavior.Transform`, `ViewPool.ItemsSource` / `TemplateSelector`, `WorkflowNodeDragBehavior.IsEnabled` / `CoordinateHostName` / `CoordinateHostType`, `WorkflowSlotConnectionBehavior.IsEnabled`, and `WorkflowSlotLayoutBehavior.IsEnabled` / `SlotNames` / `SlotEnumeratorNames` / `CoordinateHostName` / `CoordinateHostType`.

## A surface skeleton

This is the WPF spelling. Other XAML adapters change the namespace declaration, not the names.

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder">
    <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
        <ScrollViewer x:Name="PART_ScrollViewer">
            <Canvas x:Name="PART_Canvas"
                    Width="{Binding Layout.ActualSize.Width}"
                    Height="{Binding Layout.ActualSize.Height}"
                    Background="Transparent" />
        </ScrollViewer>
    </Border>
</UserControl>
```

**Expected result:** the surface resolves all four names. A missing name disables that part silently — there is no exception and no log, so a surface that does nothing is usually a name typo.

## When the surface is built in code

XAML names live in a `NameScope` on the `UserControl`, not on the visual tree. A code-built surface must register the names explicitly and then ask the surface to resolve them:

```csharp
var scope = new NameScope();
NameScope.SetNameScope(host, scope);
scope.RegisterName("PART_ScrollViewer", scrollViewer);
scope.RegisterName("PART_Canvas", canvas);
scope.RegisterName("PART_SurfaceBorder", border);

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetPointerPressSourceName(host, "PART_SurfaceBorder");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

`Refresh(UserControl)` is a public entry on WPF and WinUI; the other adapters re-resolve on their own lifecycle events. Call it after replacing a template or re-hosting the surface.

**Expected result:** `WorkflowSurfaceBehavior.Refresh(host)` returns with the named parts bound; scrolling the `ScrollViewer` now writes `tree.GetHelper().Viewport`.

## The tree is the surface's data context

Every adapter reads the tree from the host's data context — `DataContext` on WPF/Avalonia/WinUI, `BindingContext` on MAUI. Set it to an `ITreeComponent`; the surface subscribes to changes and rebinds.

**Expected result:** assigning a tree makes the surface publish a viewport and populate `tree.GetHelper().VisibleItems` on the next layout pass.
