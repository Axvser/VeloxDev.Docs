# Interaction

WinUI has no preview/tunnel pointer phase, so the adapter's gestures are wired differently from WPF: the wheel is taken on the **canvas** with `handledEventsToo: true`, and a component routes its own press before a gesture starts. The host-facing API is still the Core input route.

## Connect the ports

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />

<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

The adapter uses a pointer-capture release to emulate the missing tunnel phase; the two standard commands are unchanged.

**Expected result:** press one port and release on another to create a link; release on empty canvas to cancel.

## The link template

```xml
<DataTemplate x:Key="LinkTemplate">
    <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                    StartTop="{Binding Sender.Anchor.Vertical}"
                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                    EndTop="{Binding Receiver.Anchor.Vertical}"
                    CanRender="{Binding IsVisible}"
                    Canvas.ZIndex="-1" />
</DataTemplate>
```

Do **not** bind `Width`/`Height` to the canvas here. The link view drives its own box from `ActualSize`; a canvas-sized box reintroduces the clipping the offset frame exists to avoid.

## The offset frame

WinUI clips a retained element's content to its bounds. A link whose geometry extends into negative coordinates at deep zoom would be cut. The adapter's solution is to bake the canvas pan into the geometry and place the element at the negative offset:

```csharp
var offset = layout.ActualOffset;
Canvas.SetLeft(this, -offset.Horizontal);
Canvas.SetTop(this, -offset.Vertical);
Width = layout.ActualSize.Width;
Height = layout.ActualSize.Height;

// The curve's published coordinates stay raw canvas-local; the drawn geometry adds +offset.
link.PublishCurve(curve, this);
```

Three `Clip` values must be cleared for this to work: the root XAML, the container `Grid`, and the `Path`. The full link view is in [Complete Code](../03_verification/02_link-view/index.md).

Slot anchors on this adapter are measured **canvas-local** and written through `SlotAnchorFromCanvasLocal`; using the visual-centre form subtracts `ActualOffset` a second time and shifts every link by a constant.

**Expected result:** a link meets its ports at 100% and at 40%, and does not disappear near a large negative offset.

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

## Wheel and keys

The adapter takes a plain wheel on the canvas, routes `PointerWheelChanged`, and scrolls through its registered `IWorkflowSurfaceScroller` unless a subscriber refuses the notch. Ctrl+wheel is the zoom gesture and is routed first.

```csharp
private ITreeComponent? _tree;
private IInputEvents? _events;

private void BindTree(ITreeComponent tree)
{
    if (tree.GetHelper() is not IInputEvents events) return;
    _tree = tree;
    _events = events;
    events.Input.KeyDown += OnKeyDown;
    events.Input.PointerWheelChanged += OnWheel;
}

private void OnWheel(object? sender, PointerWheelEventArgs e)
{
    if (_tree is not { } tree || !e.Modifiers.HasFlag(InputModifiers.Shift)) return;

    e.Handle.PreventDefault = true;
    WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
}

private void OnKeyDown(object? sender, KeyDownEventArgs e)
{
    if (_tree is not { } tree) return;

    if (e.Key == InputKey.Delete && e.Target is ILinkComponent link && link.DeleteCommand.CanExecute(null))
    {
        link.DeleteCommand.Execute(null);
        return;
    }

    if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;

    var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
    if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
    else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
    else return;

    e.Handle.PreventDefault = true;
}
```

**Expected result:** Shift+wheel scrolls horizontally, Ctrl+wheel zooms, Ctrl+Z/Ctrl+Y undo and redo, and Delete removes the hovered link.

## The link menu

```xml
<MenuFlyout x:Key="LinkContextMenu">
    <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
</MenuFlyout>
```

Add `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"` to the root. `MenuFlyout` has no `DataContext`, so the adapter feeds each `MenuFlyoutItem.DataContext` the pressed link; an entry binds `DeleteCommand` like any other item.

The minimap follows the always-center rule: a press anywhere in the thumbnail recentres the viewport.

**Expected result:** right-clicking a link opens a native flyout, and its `Delete` entry acts on the pressed link.
