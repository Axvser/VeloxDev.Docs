# Verification

This sample is the smallest host that shows both halves: a virtualizing `TreeHelper(200)` and a `ViewPool` attached to the canvas. Twelve nodes are placed in a world wider than the window, so the visible count is demonstrably smaller than the node count.

## Run it

```powershell
dotnet run
```

## Check each behaviour

1. **The visible set is smaller.** The overlay reports `Visible N`; N is less than 12 and changes as you scroll.
2. **Views are pooled.** Scroll back and forth: node cards keep their identity. A card that was hidden and reused receives a different node's `Name`.
3. **Only visible items exist.** Inspect `PART_Canvas.Children`: it holds the views of the current visible set, not twelve cards.
4. **The parameterless helper disables it.** Replace `base(200)` with `base()`: `VisibleItems` stays empty and no card appears, because the canvas binds the visible set.
5. **Surface events drive it.** Pan or zoom; the visible set changes only after the scroll/zoom, not while a node is being dragged.

The Core and headless suites assert batching, per-type reuse, reset, unsupported-type caching, failure isolation, disposal, and one-view-per-visible-item (`ViewPoolTests.cs`, `ViewPoolHeadlessTests.cs`).

## Complete code

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

## Run declaration

⚠️ Not actually run — statically verified only. The sample is assembled from the same declarations the demos use (`[WorkflowBuilder.Tree<VirtualizeHelper>]`, `TreeHelper(200)`, `ViewPool.ItemsSource`); the counts and recycling statements are the behaviours asserted by `ViewPoolTests.cs`, `SpatialIndexFreshnessTests.cs` and `ViewPoolHeadlessTests.cs`. No window was launched while writing this page.
