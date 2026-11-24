# Interaction

With the surface rendering nodes, three things turn it into an editor: ports can be connected, links have to be drawn, and the host has to decide what the routed input means. The adapter supplies the gestures; the host supplies the commands and the appearance.

## Make the ports connectable

Add the connection behavior to both kinds of port. On the input `Ellipse`:

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

and on the output `Ellipse` inside the `ItemsControl`:

```xml
<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

The behavior executes `SendConnectionCommand` on press and `ReceiveConnectionCommand` on release. It never decides whether the connection is legal — that is the tree's `ValidateConnection` and the `Connecting` veto.

**Expected result:** pressing one port and releasing on another creates a link; releasing on empty canvas cancels.

## Render a link

A link view draws the shared cubic Bézier and **publishes the curve it drew**, which is what makes the link hit-testable. The render-ready gate comes first.

```csharp
using System.Windows;
using System.Windows.Media;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class LinkView : FrameworkElement
{
    private const double PullMinimum = 40;

    public static readonly DependencyProperty StartLeftProperty = DependencyProperty.Register(
        nameof(StartLeft), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty StartTopProperty = DependencyProperty.Register(
        nameof(StartTop), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty EndLeftProperty = DependencyProperty.Register(
        nameof(EndLeft), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty EndTopProperty = DependencyProperty.Register(
        nameof(EndTop), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty CanRenderProperty = DependencyProperty.Register(
        nameof(CanRender), typeof(bool), typeof(LinkView), new FrameworkPropertyMetadata(true, OnGeometryChanged));

    public double StartLeft { get => (double)GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => (double)GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => (double)GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => (double)GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => (bool)GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    public LinkView()
    {
        DataContextChanged += (_, e) =>
        {
            if (e.OldValue is ILinkComponent old) old.PublishCurve(null);
            InvalidateVisual();
        };
    }

    private static void OnGeometryChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        => ((LinkView)d).InvalidateVisual();

    protected override void OnRender(DrawingContext dc)
    {
        if (!CanRender) return;
        if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

        var curve = LinkCurve.BuildLinkCubic(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        if (DataContext is ILinkComponent bound) bound.PublishCurve(curve, this);

        var p = LinkCurve.LinkCurvePoints(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        var geometry = new StreamGeometry();
        using (var context = geometry.Open())
        {
            context.BeginFigure(new Point(p[0].X, p[0].Y), false, false);
            context.BezierTo(
                new Point(p[1].X, p[1].Y),
                new Point(p[2].X, p[2].Y),
                new Point(p[3].X, p[3].Y),
                true, false);
        }

        dc.DrawGeometry(null, new Pen(Brushes.WhiteSmoke, 2), geometry);
    }
}
```

Add the link template and extend the selector:

```xml
<DataTemplate x:Key="LinkTemplate">
    <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                    StartTop="{Binding Sender.Anchor.Vertical}"
                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                    EndTop="{Binding Receiver.Anchor.Vertical}"
                    CanRender="{Binding IsVisible}"
                    Width="{Binding ElementName=PART_Canvas, Path=ActualWidth}"
                    Height="{Binding ElementName=PART_Canvas, Path=ActualHeight}"
                    Panel.ZIndex="-1"
                    IsHitTestVisible="False"
                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
</DataTemplate>
```

```csharp
public DataTemplate? LinkTemplate { get; set; }

public override DataTemplate SelectTemplate(object item, DependencyObject container)
    => item switch
    {
        ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
        INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
```

Call `PublishCurve(null)` on the paths that draw nothing (hidden, unmeasured endpoints, a pooled view rebound to another link). A stale published curve keeps answering for a link that is no longer painted.

**Expected result:** a link appears between two measured ports; hovering near it is answered only over the painted stroke (six units either side), not over the whole canvas box.

## Create the same link in code

For a deterministic start-up, build the link through the helpers instead of the mouse. This is the path the headless tests use and it runs synchronously.

```csharp
private static void Connect(TreeViewModel tree, NodeViewModel sender, NodeViewModel receiver)
{
    sender.OutputSlots.SetSelector(typeof(Kind));
    if (sender.OutputSlots.Items.Count == 0) return;

    tree.GetHelper().SendConnection(sender.OutputSlots.Items[0].Slot);
    tree.GetHelper().ReceiveConnection(receiver.InputSlot);
}
```

Define the selector type beside the ViewModels:

```csharp
public enum Kind { A, B, C }
```

`SetSelector(typeof(Kind))` materializes one output slot per enum member; each `ConditionalSlot<SlotViewModel>` exposes `Slot`.

**Expected result:** one link exists between the first node's first output and the second node's input, and the link view draws it once both slot anchors are measured.

## Route the wheel and the keys

The adapter already handles pan, zoom and the plain wheel. A host subscribes the tree's `IInputEvents` only for the decisions it wants to change.

```csharp
private ITreeComponent? _tree;
private IInputEvents? _events;

private void BindTree(ITreeComponent tree)
{
    Unbind();
    if (tree.GetHelper() is not IInputEvents events) return;

    _tree = tree;
    _events = events;
    events.Input.KeyDown += OnKeyDown;
    events.Input.PointerWheelChanged += OnWheel;
}

private void Unbind()
{
    if (_events is not null)
    {
        _events.Input.KeyDown -= OnKeyDown;
        _events.Input.PointerWheelChanged -= OnWheel;
    }

    _events = null;
    _tree = null;
}

private void OnWheel(object? sender, PointerWheelEventArgs e)
{
    if (_tree is not { } tree) return;
    if (!e.Modifiers.HasFlag(InputModifiers.Shift)) return;   // otherwise let the adapter scroll

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

Call `BindTree((ITreeComponent)DataContext)` when the data context changes. The two wheel axes do not share a positive direction: `DeltaY` positive is away from the user, while `ScrollBy`'s X positive is towards the content on the right, so a vertical notch driven into the horizontal axis takes a negation.

**Expected result:** Shift+wheel scrolls sideways, Ctrl+wheel zooms, Ctrl+Z/Ctrl+Y undo and redo structural changes, and Delete removes the link under the pointer. `Move`/`SetAnchor`/`SetSize` are not pushed, so dragging a node is not undoable by default.

## The link menu and the minimap

The adapter owns the right-press wiring; the host declares the menu and its entries.

```xml
<UserControl.Resources>
    <ContextMenu x:Key="LinkContextMenu">
        <MenuItem Header="Delete" Command="{Binding DeleteCommand}" />
    </ContextMenu>
</UserControl.Resources>
```

Point the root at the key with `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"`. The menu's `DataContext` is set to the pressed link before it opens, so an entry is one bound command. Keep it a **keyed resource**, not `<Border.ContextMenu>`; the latter lets WPF's `ContextMenuService` open it without the adapter, which loses the link identity.

The minimap follows the always-center rule: pressing anywhere in the thumbnail puts that point at the viewport centre. It shares the adapter's `ScrollViewerName` resolution, which is why `PART_MinimapOverlay` needs `ScrollViewerName="PART_ScrollViewer"`.

**Expected result:** right-clicking a link opens a menu with one working `Delete` entry; clicking in the minimap recentres the surface.
