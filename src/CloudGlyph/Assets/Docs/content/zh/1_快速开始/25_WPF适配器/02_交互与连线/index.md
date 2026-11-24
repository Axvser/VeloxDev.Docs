# 交互与连线

表面能画出节点之后，把它变成编辑器需要三件事：端口可以连接、连线要被画出来、宿主决定路由过来的输入意味着什么。适配器提供手势，宿主提供命令与外观。

## 让端口可连接

给两种端口都加上连接行为。输入 `Ellipse` 上：

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

输出 `Ellipse`（在 `ItemsControl` 里）上：

```xml
<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

行为在按下时执行 `SendConnectionCommand`，在松开时执行 `ReceiveConnectionCommand`。它不判断连接是否合法 —— 那是树的 `ValidateConnection` 与 `Connecting` 否决的职责。

**预期结果：** 按下一个端口、在另一个端口松开就建成连线；在空白画布松开则取消。

## 画一条连线

连线视图画共享的三次贝塞尔曲线，并**发布它画出的那条曲线** —— 这才是连线可命中的原因。第一行是渲染就绪门。

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

加上连线模板并扩展选择器：

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

在什么都不画的路径上调用 `PublishCurve(null)`（隐藏、端点未测量、池化视图改绑到另一条线）。一条过期的已发布曲线会让「已经不再画在这里」的连线继续回答指针。

**预期结果：** 两个已测量的端口之间出现连线；只有画出来的描边附近（两侧各 6 个单位）会命中，整块画布框不会。

## 用代码建同一条连线

为了确定的启动状态，用 helper 建连线，而不是靠鼠标。这是无头测试走的路径，且同步执行。

```csharp
private static void Connect(TreeViewModel tree, NodeViewModel sender, NodeViewModel receiver)
{
    sender.OutputSlots.SetSelector(typeof(Kind));
    if (sender.OutputSlots.Items.Count == 0) return;

    tree.GetHelper().SendConnection(sender.OutputSlots.Items[0].Slot);
    tree.GetHelper().ReceiveConnection(receiver.InputSlot);
}
```

选择器类型放在 ViewModel 旁边：

```csharp
public enum Kind { A, B, C }
```

`SetSelector(typeof(Kind))` 为每个枚举成员物化一个输出槽；每个 `ConditionalSlot<SlotViewModel>` 通过 `Slot` 暴露插槽。

**预期结果：** 第一个节点的第一个输出与第二个节点的输入之间有一条连线；两个插槽锚点都测量完之后连线视图把它画出来。

## 路由滚轮与按键

适配器已经处理平移、缩放与普通滚轮。宿主只在想要改变的决定上订阅树的 `IInputEvents`。

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
    if (!e.Modifiers.HasFlag(InputModifiers.Shift)) return;   // 否则交给适配器滚动

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

数据上下文变化时调用 `BindTree((ITreeComponent)DataContext)`。两个滚轮轴的正方向不共享：`DeltaY` 为正表示远离用户，而 `ScrollBy` 的 X 为正表示朝右侧内容移动，所以把竖向一格灌进横轴要取反。

**预期结果：** Shift+滚轮横向滚动，Ctrl+滚轮缩放，Ctrl+Z/Ctrl+Y 撤销/重做结构改动，Delete 删除指针下的连线。`Move`/`SetAnchor`/`SetSize` 不入栈，所以拖动节点默认不可撤销。

## 连线菜单与小地图

适配器负责右键接线；宿主声明菜单与条目。

```xml
<UserControl.Resources>
    <ContextMenu x:Key="LinkContextMenu">
        <MenuItem Header="Delete" Command="{Binding DeleteCommand}" />
    </ContextMenu>
</UserControl.Resources>
```

根元素上写 `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"`。菜单打开前，适配器把它的 `DataContext` 设成被按下的那条线，所以条目只要绑一个命令。保持它是**带键资源**，不要写成 `<Border.ContextMenu>`；后者会让 WPF 的 `ContextMenuService` 绕过适配器自行弹出，丢掉连线身份。

小地图遵循 always-center：在缩略图任意处按下，都把那个点放到视口中心。它与适配器共用 `ScrollViewerName` 解析，所以 `PART_MinimapOverlay` 需要 `ScrollViewerName="PART_ScrollViewer"`。

**预期结果：** 右键连线弹出一项可用的 `Delete` 条目；点击小地图重新居中表面。
