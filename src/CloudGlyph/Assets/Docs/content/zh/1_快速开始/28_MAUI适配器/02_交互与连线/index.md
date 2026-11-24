# 交互与连线

MAUI 的交互形态在四家里差别最大：指针表面就是宿主本身，连线不是视图，覆盖层因为是输入透明的，需要显式的**交互源**。

## 节点拖拽与插槽连接

两者都是节点模板上的附着行为，上一页已经给出。拖动从整张卡片开始；连接从两个 `Ellipse` 端口开始：

```xml
<Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}"
         WidthRequest="14" HeightRequest="14" Fill="#FF1E1E1E" Stroke="White"
         HorizontalOptions="Start" VerticalOptions="Center"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

Windows 上适配器捕获指针；其他平台上，MAUI 的 pan 手势一开始就让它独占这次拖拽，因为原生指针捕获在那可能不可用。两条标准命令不变。

**预期结果：** 拖动卡片会移动节点；按下一个端口、在另一个端口松开就连接；在空白画布松开则取消。

## 共享连线层

树**不声明** `LinkTemplate`。`WorkflowLinkOverlay` 是一个 `GraphicsView`，在一次绘制里画可见集里的所有连线与虚拟预览，作为视口尺寸的一层。它必须住在不断长大的世界画布之外：画布尺寸的 `GraphicsView` 在深缩放下超过 Win2D 约 16k 设备像素的纹理上限，整层会静默消失。

覆盖层的 `InputTransparent` 保持 `true`；是 `InteractionSource` 让连线可以被悬停与删除：

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

不设 `InteractionSource`，连线会画出来，但永远不回应指针 —— 覆盖层自己收不到。

覆盖层只画**静息**连线。悬停高亮是宿主的：订阅树的 `IInputEvents`，读连线发布的曲线（`ILinkHitTestable.Curve`），在它上面画自己的一层。裁剪版 demo 没有加这一层。

**预期结果：** 两个插槽锚点测量完之后出现连线；悬停画出来的线体（两侧各 6 个单位）能到达连线；Delete 通过 `DeleteCommand` 删除悬停的那条。

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

## 手势

- **平移**用 `PanGestureRecognizer`，Windows 上另有原生指针处理。
- **缩放**触摸用 `PinchGestureRecognizer`，Windows 用 `#if WINDOWS` 的滚轮钩子。适配器把 Windows `ScrollViewer.ManipulationMode` 设成 `None`，让它的程序化 `ChangeView` 成为唯一滚动驱动；不要改这个值，否则平台会和平移抢。
- **滚轮**先路由，再通过注册的 `IWorkflowSurfaceScroller` 滚动，除非订阅者否决。Ctrl+滚轮是缩放路径。
- **连接拖拽中的候选接收者**由插槽连接行为报告，不是表面 —— 因为视口尺寸的覆盖层无法靠可视命中测试回答「哪个插槽」。

**预期结果：** Windows 上 Shift+滚轮横向滚动，Ctrl+滚轮缩放，Ctrl+Z/Ctrl+Y 撤销/重做，平移与缩放时指针始终停在同一个世界点上。

## 连线菜单

```xml
<MenuFlyout x:Key="LinkContextMenu">
    <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
</MenuFlyout>
```

根元素上加 `behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu"`。Windows 上适配器把浮出菜单变成原生菜单；其他平台上它按 `Margin` 自己物化一层覆盖层。每个条目绑定被按下的连线。

小地图遵循 always-center：在缩略图任意处按下，就把视口重新居中。

**预期结果：** 右键（非 Windows 上是长按）连线弹出菜单，`Delete` 条目作用于那条线。
