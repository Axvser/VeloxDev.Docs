# Surface

WinUI's host is a `UserControl`; the attached property names are the same as WPF, but the XML namespace uses the `using:` dialect with **no** `;assembly=` suffix.

## ViewModels

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

**Expected result:** the generated tree exposes `Helper`, `Nodes`, `Links` and `CreateNodeCommand`.

## The surface

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

The selector is a `DataTemplateSelector`, as on WPF:

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

**Expected result:** the node template resolves and the pool materializes one view per visible node.

## Code-behind

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

        // WinUI resolves PART_* through the UserControl's name scope; re-run after the host is loaded
        // or after a template change.
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

## Why the canvas does not bind a transform

On WPF and Avalonia the pan offset is an attached value the node and link templates bind their `RenderTransform` to. WinUI's children do not make that binding, so the surface moves the canvas with a composition translation (`state.Canvas.Translation`) instead.

The consequence for a custom view is that the pan is **already applied to the canvas**, so a link view must bake the same `ActualOffset` into its geometry and position itself at the negative offset. The next page shows that offset frame.

**Expected result:** three cards render and drag; pan and zoom move the whole canvas, and the minimap follows.
