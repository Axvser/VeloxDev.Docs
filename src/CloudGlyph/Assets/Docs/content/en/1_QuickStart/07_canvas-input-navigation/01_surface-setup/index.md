# Surface setup

The WPF surface behavior attaches to a `UserControl` and resolves the parts it drives by name. Nothing is found by walking the visual tree for a type: the names below are the contract between your markup and the adapter.

## The markup contract

```xml
<UserControl x:Class="Demo.TreeView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">

    <Border x:Name="PART_SurfaceBorder" BorderBrush="#33FFFFFF" BorderThickness="1">
        <local:WorkflowGridDecorator x:Name="PART_GridDecorator">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent">
                    <Canvas.RenderTransform>
                        <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                            Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                    </Canvas.RenderTransform>
                </Canvas>
            </ScrollViewer>
        </local:WorkflowGridDecorator>
    </Border>

    <local:MinimapOverlay x:Name="PART_MinimapOverlay"
                          HorizontalAlignment="Stretch"
                          VerticalAlignment="Stretch"
                          ScrollViewerName="PART_ScrollViewer" />
</UserControl>
```

Every named part is optional except the scroll viewer and the canvas, which pan and zoom need. `GridDecoratorName` and `MinimapOverlayName` are the hooks the later features attach to; leave them out if you do not use those capabilities.

## Name meanings

| Attached property | The named element must be | What the adapter does with it |
|---|---|---|
| `ScrollViewerName` | `ScrollViewer` | Reads and writes the scroll offsets, measures the viewport, grows the extent on overscroll. |
| `CanvasName` | `Canvas` | The reference frame for pointer positions and the target of the render transform. |
| `GridDecoratorName` | an `IWorkflowGridDecorator` | Pushed scroll/content offsets and the ruler-band inset. |
| `PointerPressSourceName` | the element that receives presses | Presses are routed from this element so blank-surface pan starts there. |
| `MinimapOverlayName` | an `IWorkflowMinimapOverlay` | Pushed tree, offsets, viewport size and available corner. |
| `ZoomEnabled` | `bool` (default `false`) | Enables the Ctrl+wheel zoom gesture. |
| `LinkMenuKey` | a `ContextMenu` resource key | The adapter opens that menu on a right press over a link and suspends the route while it is open. |

The behavior sets `Focusable = true` on the host itself. That is what lets hovered links hand the keyboard focus to the surface, and therefore what lets `Delete` and `Ctrl+Z` reach the tree route.

## Templates bind the transform

A node or link view must bind its `RenderTransform` to the transform the behavior writes. The transform is published as an attached property, not applied to the host.

```xml
<DataTemplate x:Key="NodeTemplate">
    <local:NodeView Width="{Binding Size.Width}"
                    Height="{Binding Size.Height}"
                    Canvas.Left="{Binding Anchor.Horizontal}"
                    Canvas.Top="{Binding Anchor.Vertical}"
                    Panel.ZIndex="{Binding Anchor.Layer}"
                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
</DataTemplate>
```

If the transform is not bound, the nodes render at their world coordinates and ignore pan and zoom — the surface still scrolls, but nothing tracks it.

## Per-view gestures are attached too

Node drag and connection drag are not on the host; they are attached to the views that should start them.

```xml
<!-- the draggable part of a node card -->
<Grid behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />

<!-- the port view -->
<UserControl behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

`WorkflowNodeDragBehavior.CoordinateHostName` is the canvas whose coordinates the drag delta is measured in. Without it the behavior falls back to the nearest ancestor `Canvas`.

## If the parts appear later

`WorkflowSurfaceBehavior.Refresh(host)` re-resolves the named parts and re-applies the layout. Call it after replacing the surface's content or after a tree swap that does not rebuild the control; the demo calls it after an auto-layout pass.

## Expected result

- The named parts resolve when the control loads; no binding error is reported for `PART_ScrollViewer` or `PART_Canvas`.
- Dragging a node moves it; dragging blank canvas pans.
- `Ctrl` + wheel changes `Layout.Scale` and the status text that binds it.
- Rotating the wheel without `Ctrl` scrolls vertically.

## Next

[Route input](../02_route-input/index.md) shows how to subscribe to the events this surface forwards.
