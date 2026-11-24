# 交互与连线

Avalonia 表面使用与 WPF 相同的 Core 输入路由。适配器用 `RoutingStrategies.Tunnel` 注册滚轮处理器，因为这家的 Avalonia 没有 `PreviewMouseWheel`；宿主只提供它想改变的决定。

## 连接端口

给两个 `Ellipse` 加上连接行为：

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />

<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

Avalonia 适配器在按下时主动释放指针捕获，好让松开事件到达接收端口；行为仍然只执行两条标准命令，不判断合法性。

**预期结果：** 按下一个端口、在另一个端口松开就建成连线；在空白画布松开则清掉预览。

## 画一条连线

连线视图是一个保留式 `Control`；Avalonia 的绘制入口是 `Render(DrawingContext)`，不是 `OnRender`。发布你画出的曲线。

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

加上模板并扩展选择器：

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

`framework` 前缀是 `xmlns:framework="using:VeloxDev.WorkflowSystem"`。选择器的 `Match` 已经接受 `ILinkComponent`；在资源实例上设置 `LinkTemplate` 即可。

**预期结果：** 两个插槽锚点都测量完之后出现连线；命中面是画出来的描边（两侧各 6 个单位），不是控件的整块框。

## 用代码建连线

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

helper 路由同步执行，也是无头套件走的路径；上面的鼠标路径走同两条命令。

**预期结果：** 一条连线把第一个输出槽接到第二个节点的输入。

## 滚轮与按键

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

Avalonia 的 `ScrollViewer` **不会**把滚轮标成已处理，所以适配器注册隧道处理器并自己应用滚动。普通滚轮照常滚动；Shift+滚轮是宿主改向的机会，符号要取反 —— 因为「远离用户」的竖向一格，一旦驱动横轴在画面上就是向左。

**预期结果：** Shift+滚轮横向滚动，Ctrl+滚轮缩放，Ctrl+Z/Ctrl+Y 撤销/重做，Delete 删除悬停的连线。

## 连线菜单

```xml
<ContextMenu x:Key="LinkContextMenu">
    <MenuItem Header="Delete" Command="{ReflectionBinding DeleteCommand}" />
</ContextMenu>
```

根元素上加 `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"`。必须用 `{ReflectionBinding}`，因为资源没有 `x:DataType` 作用域，而工程默认编译绑定；那里写 `{Binding}` 构建不过。

小地图与其他几家一样是 always-center：在缩略图任意处按下，就把视口重新居中到那一点。

**预期结果：** 右键连线弹出菜单，`Delete` 条目作用于被按下的那条线。
