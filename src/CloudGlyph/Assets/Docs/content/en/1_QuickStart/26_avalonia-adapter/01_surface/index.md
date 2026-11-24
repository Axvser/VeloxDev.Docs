# Surface

The Avalonia surface is a `UserControl` like the WPF one. The attached properties and `PART_*` names are identical; the differences are the XML namespace spelling, compiled bindings, and the missing `PreviewMouseWheel` phase (the adapter registers its own tunnel handlers).

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

`VirtualizeHelper` derives from `TreeHelper(200)`; the cell-size constructor is what enables virtualization, which the surface's unconditional `Viewport` write requires.

**Expected result:** the generated tree exposes `Helper`, `Nodes`, `Links` and the standard commands; the node exposes `Name`, `InputSlot` and `OutputSlots`.

## The surface

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp"
             xmlns:vm="using:MyApp"
             xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
             x:DataType="vm:TreeViewModel"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate" DataType="vm:NodeViewModel">
            <Grid Width="{Binding Size.Width}"
                  Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}"
                  Canvas.Top="{Binding Anchor.Vertical}"
                  ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
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
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto"
                          IsScrollInertiaEnabled="False">
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

Avalonia's template selector is an `IDataTemplate`: it both selects and builds. The `ViewPool.TemplateSelector` property is typed `IDataTemplate?`.

```csharp
using System;
using Avalonia.Controls;
using Avalonia.Controls.Templates;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : IDataTemplate
{
    public IDataTemplate? NodeTemplate { get; set; }
    public IDataTemplate? LinkTemplate { get; set; }

    public Control Build(object? parameter)
        => Select(parameter).Build(parameter)
           ?? throw new InvalidOperationException($"The selected template could not build {parameter?.GetType().FullName}.");

    public bool Match(object? data) => data is INodeComponent or ILinkComponent;

    private IDataTemplate Select(object? item) => item switch
    {
        ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
        INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
}
```

**Expected result:** `WorkflowTemplateSelector.Match` accepts a node, `Build` returns the node view, and `ViewPool` materializes one view per visible node.

## Code-behind

```csharp
using Avalonia.Controls;
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
                Size = new VeloxDev.WorkflowSystem.Size(220, 120),
                Anchor = new Anchor(120 + (i * 280), 140, 0)
            });
        }
    }
}
```

**Expected result:** three cards render on the canvas and drag from anywhere on the card. Ctrl+wheel zooms and the plain wheel scrolls through the adapter, not through `ScrollViewer` inertia.

## Compiled bindings

- `AvaloniaUseCompiledBindingsByDefault=true` is what makes `x:DataType` mandatory. Without it, every binding scope needs its own annotation or reports `AVLN2100`.
- A `DataTemplate` needs a **concrete** type, not an interface. The tree's `x:DataType` is `TreeViewModel`, because `ITreeComponent` has no `Helper` property to bind.
- The ancestor binding is written as `$parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)`. When a prefix sits inside a binding path and the lookup fails at template build time, the view manager swallows the exception and the canvas simply stays empty; use an assembly-qualified `clr-namespace:MyApp;assembly=MyApp` if that happens.
- The node view in the shipped template ships `x:CompileBindings="False"` with a note to replace it with the concrete `x:DataType`; this page starts from the concrete form.
