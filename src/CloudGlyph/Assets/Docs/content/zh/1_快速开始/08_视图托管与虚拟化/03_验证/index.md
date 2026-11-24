# 验证

这个示例是同时展示两半的最小宿主：一个开虚拟化的 `TreeHelper(200)`，以及挂在画布上的 `ViewPool`。十二个节点放在比窗口更宽的世界里，所以可见数明显小于节点数。

## 运行

```powershell
dotnet run
```

## 逐项检查

1. **可见集更小。** 浮层显示 `Visible N`；N 小于 12，并随滚动变化。
2. **视图被池化。** 来回滚动：节点卡保持同一身份。曾经隐藏又被复用的卡会收到另一个节点的 `Name`。
3. **只存在可见项。** 检查 `PART_Canvas.Children`：里面是当前可见集的视图，不是十二张卡。
4. **无参 Helper 会关掉它。** 把 `base(200)` 改成 `base()`：`VisibleItems` 保持为空，也不出现卡片，因为画布绑的是可见集。
5. **表面事件驱动它。** 平移或缩放；可见集在滚动/缩放之后才变，拖动节点期间不变。

Core 与无头套件断言了分批、按类型复用、Reset、不支持类型缓存、失败隔离、销毁，以及「一个可见项一个视图」（`ViewPoolTests.cs`、`ViewPoolHeadlessTests.cs`）。

## 完整代码

### `ViewModels.cs`

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace Demo;

internal sealed class VirtualizeHelper : TreeHelper
{
    public VirtualizeHelper() : base(200) { }
}

[WorkflowBuilder.Tree<VirtualizeHelper>]
internal partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper>]
internal partial class NodeViewModel
{
    public NodeViewModel() => InitializeWorkflow();

    [VeloxProperty] private string _name = string.Empty;
}

[WorkflowBuilder.Slot<SlotHelper>]
internal partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
internal partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}
```

### `WorkflowTemplateSelector.cs`

```csharp
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace Demo;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    public override DataTemplate? SelectTemplate(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate,
            INodeComponent => NodeTemplate,
            _ => null,
        };
}
```

### `TreeView.xaml`

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
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder">
    <UserControl.Resources>
        <BooleanToVisibilityConverter x:Key="BoolToVisibility" />

        <DataTemplate x:Key="NodeTemplate">
            <Border Width="{Binding Size.Width}"
                    Height="{Binding Size.Height}"
                    Background="#DD2D2D30"
                    CornerRadius="6"
                    Canvas.Left="{Binding Anchor.Horizontal}"
                    Canvas.Top="{Binding Anchor.Vertical}"
                    Panel.ZIndex="{Binding Anchor.Layer}"
                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}">
                <TextBlock Text="{Binding Name}" Foreground="#DDE7E7E7" Margin="12" />
            </Border>
        </DataTemplate>

        <DataTemplate x:Key="LinkTemplate">
            <Canvas Width="{Binding RelativeSource={RelativeSource AncestorType={x:Type Canvas}}, Path=ActualWidth}"
                    Height="{Binding RelativeSource={RelativeSource AncestorType={x:Type Canvas}}, Path=ActualHeight}"
                    IsHitTestVisible="False"
                    Visibility="{Binding IsVisible, Converter={StaticResource BoolToVisibility}}">
                <Line X1="{Binding Sender.Anchor.Horizontal}" Y1="{Binding Sender.Anchor.Vertical}"
                      X2="{Binding Receiver.Anchor.Horizontal}" Y2="{Binding Receiver.Anchor.Vertical}"
                      Stroke="#CC6E8BFF" StrokeThickness="2" />
            </Canvas>
        </DataTemplate>

        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}"
                                        LinkTemplate="{StaticResource LinkTemplate}" />
    </UserControl.Resources>

    <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
        <ScrollViewer x:Name="PART_ScrollViewer"
                      HorizontalScrollBarVisibility="Auto"
                      VerticalScrollBarVisibility="Auto">
            <Canvas x:Name="PART_Canvas"
                    Width="{Binding Layout.ActualSize.Width}"
                    Height="{Binding Layout.ActualSize.Height}"
                    Background="Transparent"
                    behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                    behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
        </ScrollViewer>
    </Border>
</UserControl>
```

### `TreeView.xaml.cs`

```csharp
using System.Windows.Controls;

namespace Demo;

public partial class TreeView : UserControl
{
    public TreeView() => InitializeComponent();
}
```

### `MainWindow.xaml`

```xml
<Window x:Class="Demo.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:local="clr-namespace:Demo"
        Title="View hosting" Width="1100" Height="700">
    <Grid>
        <local:TreeView />
        <Border HorizontalAlignment="Right" VerticalAlignment="Top"
                Margin="12" Padding="8,4" Background="#B0000000" IsHitTestVisible="False">
            <TextBlock Foreground="White"
                       Text="{Binding Helper.VisibleItems.Count, StringFormat=Visible {0}}" />
        </Border>
    </Grid>
</Window>
```

### `MainWindow.xaml.cs`

```csharp
using System.Windows;
using VeloxDev.WorkflowSystem;

namespace Demo;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        tree.Layout.NegativeOffset = new Offset(320, 260);

        var size = new Size(220, 120);
        for (var i = 0; i < 12; i++)
        {
            tree.CreateNodeCommand.Execute(new NodeViewModel
            {
                Name = $"Node {i}",
                Size = size,
                Anchor = new Anchor
                {
                    Horizontal = (i % 4) * 320 - 480,
                    Vertical = (i / 4) * 200 - 200,
                },
            });
        }

        DataContext = tree;
    }
}
```

## 运行声明

⚠️ 未实际运行——仅静态核对。示例由示例工程使用的同一批声明组成（`[WorkflowBuilder.Tree<VirtualizeHelper>]`、`TreeHelper(200)`、`ViewPool.ItemsSource`）；计数与复用相关的说法是 `ViewPoolTests.cs`、`SpatialIndexFreshnessTests.cs`、`ViewPoolHeadlessTests.cs` 所断言的行为。撰写本页时没有启动窗口。
