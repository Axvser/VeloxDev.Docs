# Verification

The runnable reference for this feature is the WPF Trimmed demo. Its `TreeView` is the whole surface contract; `MainView` creates four nodes so pan and zoom have something to move.

## Run it

```powershell
dotnet run --project "Examples/Workflow/WPF Trimmed/Demo/Demo.csproj"
```

## Check each behaviour

1. **Pan.** Press the left button on empty canvas and drag. All four cards follow; the scrollbars move.
2. **Zoom.** Hold `Ctrl` and turn the wheel. The cards grow or shrink around the point under the viewport centre. The zoom is clamped between `0.1` and `10`.
3. **Plain wheel.** Release `Ctrl` and turn the wheel. The surface scrolls vertically by 48 px per notch at the default WPF line setting.
4. **Keyboard.** Press `Ctrl+Z` after creating or deleting a node. The structural edit is undone. Press `Ctrl+Z` after dragging a node: the drag is not undone, because `Move` is not submitted to the history.
5. **Take a wheel over.** Add the `Shift` clause from [Route input](../02_route-input/index.md); `Shift` + wheel now scrolls horizontally.
6. **Locate.** Call `node.Locate()` from a button or a list; the node is centred and the zoom is unchanged.

The WPF headless suite asserts the same surface behaviours without a window: named parts resolve, the canvas transform is written, viewport writes persist, virtualization excludes off-screen nodes, `Locate` works at any zoom, and a wheel over a sibling control does not scroll the canvas (`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/WorkflowSurfaceHeadlessTests.cs`).

## Complete code

The complete project is `Examples/Workflow/WPF Trimmed/Demo`. The two files below are everything this feature adds to a workflow host. `NodeView`, `SlotView`, `LinkView`, `WorkflowGridDecorator` and `MinimapOverlay` are the demo's view classes in the same folder; they supply the visuals, not the input wiring.

### `Views/Workflow/TreeView.xaml`

```xml
<UserControl x:Class="Demo.Views.TreeView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo.Views"
             xmlns:workflowViews="clr-namespace:Demo.Views.Workflow"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <workflowViews:NodeView Width="{Binding Size.Width}"
                                    Height="{Binding Size.Height}"
                                    Canvas.Left="{Binding Anchor.Horizontal}"
                                    Canvas.Top="{Binding Anchor.Vertical}"
                                    Panel.ZIndex="{Binding Anchor.Layer}"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <DataTemplate x:Key="LinkTemplate">
            <workflowViews:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                                    StartTop="{Binding Sender.Anchor.Vertical}"
                                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                                    EndTop="{Binding Receiver.Anchor.Vertical}"
                                    CanRender="{Binding IsVisible}"
                                    LineColor="#DDFFFFFF"
                                    Width="{Binding ElementName=PART_Canvas, Path=ActualWidth}"
                                    Height="{Binding ElementName=PART_Canvas, Path=ActualHeight}"
                                    Panel.ZIndex="-1"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <workflowViews:CustomTemplateSelector x:Key="WorkflowTemplateSelector"
                                              NodeTemplate="{StaticResource NodeTemplate}"
                                              LinkTemplate="{StaticResource LinkTemplate}" />
        <ContextMenu x:Key="LinkContextMenu">
            <MenuItem Header="Delete" Command="{Binding DeleteCommand}" />
        </ContextMenu>
    </UserControl.Resources>

    <Grid>
        <Border x:Name="PART_SurfaceBorder" BorderBrush="#33FFFFFF" BorderThickness="1" Background="#1E1E1E">
            <workflowViews:WorkflowGridDecorator x:Name="PART_GridDecorator">
                <ScrollViewer x:Name="PART_ScrollViewer"
                              HorizontalScrollBarVisibility="Auto"
                              VerticalScrollBarVisibility="Auto"
                              PanningMode="Both">
                    <Canvas x:Name="PART_Canvas"
                            Width="{Binding Layout.ActualSize.Width}"
                            Height="{Binding Layout.ActualSize.Height}"
                            Background="Transparent"
                            behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                            behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}">
                        <Canvas.RenderTransform>
                            <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                                Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                        </Canvas.RenderTransform>
                    </Canvas>
                </ScrollViewer>
            </workflowViews:WorkflowGridDecorator>
        </Border>
        <workflowViews:MinimapOverlay x:Name="PART_MinimapOverlay"
                                      HorizontalAlignment="Stretch"
                                      VerticalAlignment="Stretch"
                                      ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

### `Views/Workflow/TreeView.xaml.cs`

```csharp
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace Demo.Views;

public partial class TreeView : UserControl
{
    private ITreeComponent? _tree;
    private IInputEvents? _events;

    public TreeView()
    {
        InitializeComponent();
        DataContextChanged += OnDataContextChanged;
    }

    private void OnDataContextChanged(object sender, DependencyPropertyChangedEventArgs e)
    {
        Unwire();

        if (DataContext is not ITreeComponent tree) return;
        if (tree.GetHelper() is not IInputEvents events) return;

        _tree = tree;
        _events = events;
        events.Input.KeyDown += OnKeyDown;
        events.Input.PointerWheelChanged += OnWheel;
    }

    private void Unwire()
    {
        if (_events is not null)
        {
            _events.Input.KeyDown -= OnKeyDown;
            _events.Input.PointerWheelChanged -= OnWheel;
            _events = null;
        }

        _tree = null;
    }

    private void OnKeyDown(object? sender, KeyDownEventArgs e)
    {
        if (!e.Modifiers.HasFlag(InputModifiers.Control) || _tree is not { } tree) return;

        var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
        if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
        else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
        else return;

        e.Handle.PreventDefault = true;
    }

    private void OnWheel(object? sender, PointerWheelEventArgs e)
    {
        if (!e.Modifiers.HasFlag(InputModifiers.Shift) || _tree is not { } tree) return;

        e.Handle.PreventDefault = true;
        WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
    }

    // Navigation: model data is enough; the node does not need a view.
    public void LocateFirstNode()
    {
        if (_tree is { Nodes.Count: > 0 } tree) tree.Nodes[0].Locate();
    }
}
```

## Run declaration

⚠️ Not actually run — statically verified only. The two files above match the demo's `TreeView.xaml` and `TreeView.xaml.cs` except for the added `LocateFirstNode` helper; the behaviours listed under "Check each behaviour" are what the demo and the WPF headless suite assert. No window was launched while writing this page.
