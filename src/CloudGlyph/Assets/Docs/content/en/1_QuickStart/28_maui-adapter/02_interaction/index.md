# Interaction

MAUI's interaction shape is the most different of the four adapters: the pointer surface is the host itself, links are not views, and the overlay needs an **interaction source** because it is input-transparent.

## Node drag and slot connection

Both are attached behaviors on the node template, shown on the previous page. The drag runs from the whole card; the connection runs from the two `Ellipse` ports:

```xml
<Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}"
         WidthRequest="14" HeightRequest="14" Fill="#FF1E1E1E" Stroke="White"
         HorizontalOptions="Start" VerticalOptions="Center"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

On Windows the adapter captures the pointer; on the other platforms it lets the MAUI pan gesture own the drag once it starts, because native pointer capture may not be available there. The two standard commands are unchanged.

**Expected result:** drag a card and it moves; press a port and release on another to connect; release on empty canvas to cancel.

## The shared link overlay

The tree declares **no** `LinkTemplate`. `WorkflowLinkOverlay` is a `GraphicsView` that draws every link in the visible set plus the virtual preview, in one viewport-sized layer. It must live outside the growing world canvas: a canvas-sized `GraphicsView` exceeds Win2D's roughly 16k device-pixel texture limit at deep zoom and the whole layer disappears silently.

The overlay's `InputTransparent` stays `true`; `InteractionSource` is what makes links hoverable and deletable:

```xml
<behaviors:WorkflowLinkOverlay x:Name="PART_LinkLayer"
                               WorkflowTree="{Binding BindingContext, Source={x:Reference Root}}"
                               InteractionSource="{x:Reference Root}"
                               ScrollOffsetX="{Binding ScrollOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ScrollOffsetY="{Binding ScrollOffsetY, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetX="{Binding ContentOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetY="{Binding ContentOffsetY, Source={x:Reference PART_GridDecorator}}"
                               RulerThickness="0" StrokeWidth="2" />
```

Leave `InteractionSource` unset and links paint but never answer a pointer — the overlay itself cannot receive one.

The overlay draws **resting** links only. A hover highlight is the host's: subscribe the tree's `IInputEvents`, read the curve the link publishes (`ILinkHitTestable.Curve`), and draw your own layer above. The trimmed demo does not add one.

**Expected result:** a link appears when both slot anchors are measured; hovering its painted body (six units either side) reaches the link; Delete removes the hovered link through its `DeleteCommand`.

## Create the link in code

```csharp
private static void Connect(TreeViewModel tree, NodeViewModel sender, NodeViewModel receiver)
{
    sender.OutputSlots.SetSelector(typeof(Kind));
    if (sender.OutputSlots.Items.Count == 0) return;

    tree.GetHelper().SendConnection(sender.OutputSlots.Items[0].Slot);
    tree.GetHelper().ReceiveConnection(receiver.InputSlot);
}
```

```csharp
public enum Kind { A, B, C }
```

**Expected result:** one link joins the first output slot to the second node's input.

## Gestures

- **Pan** uses a `PanGestureRecognizer`, plus native pointer handling on Windows.
- **Zoom** uses a `PinchGestureRecognizer` for touch and a `#if WINDOWS` wheel hook. The adapter sets the Windows `ScrollViewer.ManipulationMode` to `None` so its programmatic `ChangeView` is the only scroll driver; leave that value alone or the platform will fight the pan.
- **The wheel** is routed and then scrolled through the registered `IWorkflowSurfaceScroller` unless a subscriber refuses it. Ctrl+wheel is the zoom path.
- **The candidate receiver** during a connection drag is reported by the slot-connection behavior, not the surface, because a viewport-sized overlay cannot answer "which slot" by visual hit-testing.

**Expected result:** on Windows, Shift+wheel scrolls horizontally, Ctrl+wheel zooms, Ctrl+Z/Ctrl+Y undo and redo, and the pointer stays over the same world point while panning and zooming.

## The link menu

```xml
<MenuFlyout x:Key="LinkContextMenu">
    <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
</MenuFlyout>
```

Add `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"` to the root. On Windows the adapter turns the flyout into a native one; on the other platforms it materializes its own overlay layer positioned by `Margin`. Each item is bound to the pressed link.

The minimap uses the always-center rule: a press anywhere in the thumbnail recentres the viewport.

**Expected result:** right-clicking (or long-pressing, off Windows) a link opens the menu and its `Delete` entry acts on that link.
