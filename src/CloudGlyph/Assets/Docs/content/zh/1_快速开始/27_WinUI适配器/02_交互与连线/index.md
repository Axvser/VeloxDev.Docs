# 交互与连线

WinUI 没有预览/隧道指针阶段，所以适配器的手势接线与 WPF 不同：滚轮在**画布**上以 `handledEventsToo: true` 接管，组件在起手势前自己路由那一笔按下。宿主面对的仍是 Core 输入路由。

## 连接端口

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />

<Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

适配器用一次指针捕获释放来模拟缺失的隧道阶段；两条标准命令不变。

**预期结果：** 按下一个端口、在另一个端口松开就建成连线；在空白画布松开则取消。

## 连线模板

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

这里**不要**把 `Width`/`Height` 绑到画布。连线视图自己从 `ActualSize` 驱动盒子尺寸；画布尺寸的框会把偏移帧本来要避免的裁剪重新引回来。

## 偏移帧

WinUI 会把保留式元素的内容裁到它的边界。深缩放下几何伸进负坐标的连线会被切掉。适配器的解法是把画布平移烘进几何，并把元素放在负偏移处：

```csharp
var offset = layout.ActualOffset;
Canvas.SetLeft(this, -offset.Horizontal);
Canvas.SetTop(this, -offset.Vertical);
Width = layout.ActualSize.Width;
Height = layout.ActualSize.Height;

// 发布给命中的曲线保持原始画布局部坐标；只有绘制几何加上 +offset。
link.PublishCurve(curve, this);
```

要让这套成立，三处 `Clip` 都得清空：根 XAML、容器 `Grid`、`Path`。完整连线视图见[完整代码](../03_验证与完整代码/02_连线视图/index.md)。

这家适配器的插槽锚点按**画布局部**测量，并通过 `SlotAnchorFromCanvasLocal` 写回；用视觉中心形式会二次减去 `ActualOffset`，让每条连线整体偏一个常量。

**预期结果：** 连线在 100% 与 40% 下都接在端口上，不会在大的负偏移附近消失。

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

**预期结果：** 一条连线把第一个输出槽接到第二个节点的输入。

## 滚轮与按键

适配器在画布上接管普通滚轮，路由 `PointerWheelChanged`，除非订阅者否决这一格，否则通过注册的 `IWorkflowSurfaceScroller` 滚动。Ctrl+滚轮是缩放手势，且先被路由。

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

**预期结果：** Shift+滚轮横向滚动，Ctrl+滚轮缩放，Ctrl+Z/Ctrl+Y 撤销/重做，Delete 删除悬停的连线。

## 连线菜单

```xml
<MenuFlyout x:Key="LinkContextMenu">
    <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
</MenuFlyout>
```

根元素上加 `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"`。`MenuFlyout` 没有 `DataContext`，所以适配器把被按下的连线逐个喂给 `MenuFlyoutItem.DataContext`；条目照常绑定 `DeleteCommand`。

小地图遵循 always-center：在缩略图任意处按下，就把视口重新居中。

**预期结果：** 右键连线弹出原生浮出菜单，`Delete` 条目作用于被按下的那条线。
