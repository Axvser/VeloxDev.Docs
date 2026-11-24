# 表面搭建

WinUI 的宿主是 `UserControl`；附着属性名与 WPF 相同，但 XML 命名空间用 `using:` 写法，且**不带** `;assembly=` 后缀。

## ViewModel

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace MyApp;

internal sealed class VirtualizeHelper() : TreeHelper(200) { }

[WorkflowBuilder.Tree<VirtualizeHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class NodeViewModel
{
    public NodeViewModel() => InitializeWorkflow();

    [VeloxProperty] private string _name = string.Empty;

    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}
```

**预期结果：** 生成的树暴露 `Helper`、`Nodes`、`Links` 与 `CreateNodeCommand`。

## 表面

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp"
             xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Grid Width="{Binding Size.Width}" Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}" Canvas.Top="{Binding Anchor.Vertical}"
                  Canvas.ZIndex="{Binding Anchor.Layer}" Clip="{x:Null}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                  behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                  behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Border Background="#FFFFFFFF" BorderBrush="#331E1E1E" BorderThickness="1" CornerRadius="6" />
                <Grid Height="32" VerticalAlignment="Top" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" Margin="10,8" />
                </Grid>
                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
                         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
                         HorizontalAlignment="Left" VerticalAlignment="Center" />
                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}"
                              Margin="10" VerticalAlignment="Bottom">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" />
                                <Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
                                         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right" />
                            </Grid>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>
            </Grid>
        </DataTemplate>

        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}" />
    </UserControl.Resources>

    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E" BorderBrush="#33FFFFFF" BorderThickness="1">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto"
                          ZoomMode="Disabled">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>

        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                          HorizontalAlignment="Stretch"
                                          VerticalAlignment="Stretch"
                                          ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

选择器与 WPF 一样是 `DataTemplateSelector`：

```csharp
using System;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    protected override DataTemplate SelectTemplateCore(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
            INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
            _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
        };
}
```

**预期结果：** 节点模板解析成功，池为每个可见节点物化一个视图。

## 代码后置

```csharp
using Microsoft.UI.Xaml.Controls;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

namespace MyApp;

public sealed partial class WorkflowSurface : UserControl
{
    public WorkflowSurface()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        LoadTree(tree);
        DataContext = tree;

        // WinUI 通过 UserControl 的名字域解析 PART_*；宿主加载后或换模板后要再跑一次。
        Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
    }

    private static void LoadTree(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);

        for (var i = 0; i < 3; i++)
        {
            tree.CreateNodeCommand.Execute(new NodeViewModel
            {
                Name = $"Node {i + 1}",
                Size = new Size(220, 120),
                Anchor = new Anchor(120 + (i * 280), 140, 0)
            });
        }
    }
}
```

## 为什么画布不绑定变换

在 WPF 与 Avalonia 上，平移偏移是一个附着值，节点与连线模板把 `RenderTransform` 绑到它。WinUI 的子元素不做这个绑定，所以表面用合成平移（`state.Canvas.Translation`）移动画布。

对自定义视图的推论是：平移**已经作用在画布上**，连线视图必须把同一份 `ActualOffset` 烘进几何，并把自身放在负偏移处。下一页展示这个偏移帧。

**预期结果：** 三张卡渲染并可拖动；平移与缩放移动整块画布，小地图跟随。
