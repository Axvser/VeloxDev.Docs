# Surface

A WPF surface is a `UserControl` whose root element carries the attached properties, plus a `DataTemplate` per workflow item. The `ViewPool` attached to the canvas materializes one view for each visible item; the surface writes the viewport from the `ScrollViewer`.

## Project file

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="VeloxDev.WPF" Version="12.3.0" />
  </ItemGroup>
</Project>
```

**Expected result:** `dotnet build` restores `VeloxDev.WPF` and `VeloxDev.Core` and exits `0`.

## ViewModels

The generator turns these attributes into the tree/node/slot/link implementations, including `InitializeWorkflow()` and the standard commands.

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace MyApp;

internal sealed class VirtualizeHelper() : TreeHelper(200)
{
}

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

`TreeHelper(200)` is the cell-size constructor; it enables virtualization. A default `TreeHelper()` has virtualization off, and a surface writes `Viewport` unconditionally, so the cell-size form is the one a rendered tree needs.

**Expected result:** the generated `TreeViewModel` exposes `Helper`, `Nodes`, `Links` and `CreateNodeCommand`; the generated `NodeViewModel` exposes `Name`, `InputSlot` and `OutputSlots`.

## The surface

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:MyApp"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Grid Width="{Binding Size.Width}"
                  Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}"
                  Canvas.Top="{Binding Anchor.Vertical}"
                  Panel.ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                                            Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                  behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                  behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Grid.RowDefinitions>
                    <RowDefinition Height="32" />
                    <RowDefinition Height="*" />
                </Grid.RowDefinitions>

                <Border Grid.RowSpan="2" Background="#FFFFFFFF" BorderBrush="#331E1E1E"
                        BorderThickness="1" CornerRadius="6" />

                <Grid Grid.Row="0" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" VerticalAlignment="Center" Margin="10,0" />
                </Grid>

                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
                         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
                         HorizontalAlignment="Left" VerticalAlignment="Center" />

                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}"
                              Grid.Row="1" Margin="10,6">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" HorizontalAlignment="Left" />
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
                          PanningMode="Both">
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

The template selector only has to answer for the item types the pool sees:

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }

    public override DataTemplate SelectTemplate(object item, DependencyObject container)
        => item is INodeComponent
            ? NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set.")
            : throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}");
}
```

**Expected result:** the node template resolves `NodeTemplate`; a missing selector template throws at materialization instead of leaving a blank canvas.

## Code-behind

```csharp
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class WorkflowSurface : UserControl
{
    public WorkflowSurface()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        LoadTree(tree);
        DataContext = tree;
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

`Width`/`Height`/`Canvas.Left`/`Canvas.Top` bind to the **collapsed** `Size` and `Anchor`, so the template never applies zoom itself. The `RenderTransform` binding must sit on the `DataTemplate` root; an ancestor lookup made from inside a nested view resolves against the item's own tree and finds nothing.

**Expected result:** three node cards appear on a dark canvas. Dragging a card's header moves that node, and the minimap shows its thumbnail. The wheel scrolls; Ctrl+wheel zooms.

## Where the grid comes from

The WPF adapter does **not** ship a grid decorator. It resolves an element named by `GridDecoratorName`, casts it to `IWorkflowGridDecorator`, and pushes the scroll/content offsets. The demo's `WorkflowGridDecorator.cs` is the host-side implementation. Without one, the surface still works; you simply have no grid or ruler. The `RulerBand` it reports is forwarded to the virtualizer, so a decorator that covers the top/left with a band must return that thickness or nodes under it are culled.
