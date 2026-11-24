# Interaction

The Avalonia surface uses the same Core input route as WPF. The adapter registers its wheel handlers with `RoutingStrategies.Tunnel` because Avalonia has no `PreviewMouseWheel`; the host only supplies the decisions it wants to change.

## Connect the ports

Add the connection behavior to the two `Ellipse` elements:

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />

<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

Avalonia's adapter releases pointer capture on press so the release can reach the receiving port; the behavior still executes the two standard commands and decides nothing about legality.

**Expected result:** press one port, release on another, and a link is created; release on empty canvas and the preview clears.

## Draw a link

The link view is a retained `Control`; Avalonia's drawing entry is `Render(DrawingContext)`, not `OnRender`. Publish the curve you draw.

```csharp
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Immutable;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class LinkView : Control
{
    private const double PullMinimum = 40;

    public static readonly StyledProperty<double> StartLeftProperty =
        AvaloniaProperty.Register<LinkView, double>(nameof(StartLeft));
    public static readonly StyledProperty<double> StartTopProperty =
        AvaloniaProperty.Register<LinkView, double>(nameof(StartTop));
    public static readonly StyledProperty<double> EndLeftProperty =
        AvaloniaProperty.Register<LinkView, double>(nameof(EndLeft));
    public static readonly StyledProperty<double> EndTopProperty =
        AvaloniaProperty.Register<LinkView, double>(nameof(EndTop));
    public static readonly StyledProperty<bool> CanRenderProperty =
        AvaloniaProperty.Register<LinkView, bool>(nameof(CanRender), true);

    public double StartLeft { get => GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    static LinkView()
    {
        AffectsRender<LinkView>(
            StartLeftProperty, StartTopProperty, EndLeftProperty, EndTopProperty, CanRenderProperty);
    }

    protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
    {
        base.OnPropertyChanged(change);
        if (change.Property == DataContextProperty)
        {
            if (change.OldValue is ILinkComponent old && !ReferenceEquals(old, change.NewValue))
                old.PublishCurve(null);
            InvalidateVisual();
        }
    }

    public override void Render(DrawingContext context)
    {
        if (!CanRender) return;
        if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

        var curve = LinkCurve.BuildLinkCubic(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        if (DataContext is ILinkComponent bound) bound.PublishCurve(curve, this);

        var p = LinkCurve.LinkCurvePoints(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        var geometry = new StreamGeometry();
        using (var ctx = geometry.Open())
        {
            ctx.BeginFigure(new Point(p[0].X, p[0].Y), false);
            ctx.CubicBezierTo(new Point(p[1].X, p[1].Y), new Point(p[2].X, p[2].Y),
                new Point(p[3].X, p[3].Y));
        }

        context.DrawGeometry(null, new Pen(new ImmutableSolidColorBrush(Colors.WhiteSmoke), 2), geometry);
    }
}
```

Add the template and extend the selector:

```xml
<DataTemplate x:Key="LinkTemplate" DataType="framework:ILinkComponent">
    <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                    StartTop="{Binding Sender.Anchor.Vertical}"
                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                    EndTop="{Binding Receiver.Anchor.Vertical}"
                    CanRender="{Binding IsVisible}"
                    Width="{Binding $parent[Canvas].Bounds.Width}" Height="{Binding $parent[Canvas].Bounds.Height}"
                    ZIndex="-1"
                    IsHitTestVisible="False"
                    RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
</DataTemplate>
```

The `framework` prefix is `xmlns:framework="using:VeloxDev.WorkflowSystem"`. The selector's `Match` already accepts `ILinkComponent`; set `LinkTemplate` on the resource instance.

**Expected result:** a link appears when both slot anchors are measured; the hit area is the painted stroke (six units either side), not the control's box.

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

The helper route is synchronous and is what the headless suites use; the mouse route above goes through the same two commands.

**Expected result:** one link joins the first output slot to the second node's input.

## Wheel and keys

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

Avalonia's `ScrollViewer` does **not** mark the wheel as handled, which is why the adapter registers a tunnel handler and applies the scroll itself. A plain wheel still scrolls; Shift+wheel is the host's chance to redirect it, and the sign is flipped because a vertical notch "away from the user" is leftwards once it drives the horizontal axis.

**Expected result:** Shift+wheel scrolls horizontally, Ctrl+wheel zooms, Ctrl+Z/Ctrl+Y undo and redo, Delete removes the hovered link.

## The link menu

```xml
<ContextMenu x:Key="LinkContextMenu">
    <MenuItem Header="Delete" Command="{ReflectionBinding DeleteCommand}" />
</ContextMenu>
```

Add `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"` to the root. The `{ReflectionBinding}` spelling is required because the resource has no `x:DataType` scope and the project compiles bindings by default; a plain `{Binding}` fails to build there.

The minimap uses the same always-center rule as the other adapters: a press anywhere in the thumbnail recentres the viewport on that point.

**Expected result:** right-clicking a link opens the menu, and its `Delete` entry acts on the link that was pressed.
