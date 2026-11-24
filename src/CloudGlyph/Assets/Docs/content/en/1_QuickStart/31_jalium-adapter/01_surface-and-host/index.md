# Surface and host

The surface is markup plus attached behaviours. The tree template names its parts; `WorkflowSurfaceBehavior` drives them. The host only supplies the tree as the `DataContext` and puts the tree view in a window.

## 1. Define the ViewModels

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

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

    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
internal partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

internal sealed class VirtualizeHelper() : TreeHelper(200)
{
}
```

**Expected result:** the generated members resolve, including `Name`, `InputSlot`, `OutputSlots` and `CreateNodeCommand`.

## 2. Generate the seven roles

```powershell
dotnet new jalium-v-tree      -n TreeView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-node      -n NodeView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-slot      -n SlotView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-link      -n LinkView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-selector  -n TemplateSelector      -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
```

Four items produce `.jalxaml` + `.jalxaml.cs` (tree, node, slot, link); three produce a single `.cs` (selector, decorator, minimap). All seven share one markup namespace.

**Expected result:** eleven files in `Views/Workflow/`.

## 3. The tree surface

The generated tree carries the attached properties on its root and names the parts:

```xml
<UserControl xmlns="http://schemas.jalium.com/jalxaml"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:MyWorkflowApp.Views.Workflow"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.Jalium"
             x:Class="MyWorkflowApp.Views.Workflow.TreeView"
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
      <local:NodeView Width="{Binding Size.Width}" Height="{Binding Size.Height}"
                      Canvas.Left="{Binding Anchor.Horizontal}"
                      Canvas.Top="{Binding Anchor.Vertical}"
                      RenderTransform="{Binding CanvasTransform, RelativeSource={RelativeSource AncestorType=UserControl}}" />
    </DataTemplate>
    <DataTemplate x:Key="LinkTemplate">
      <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                      StartTop="{Binding Sender.Anchor.Vertical}"
                      EndLeft="{Binding Receiver.Anchor.Horizontal}"
                      EndTop="{Binding Receiver.Anchor.Vertical}"
                      RenderTransform="{Binding CanvasTransform, RelativeSource={RelativeSource AncestorType=UserControl}}" />
    </DataTemplate>
    <local:TemplateSelector x:Key="WorkflowTemplateSelector"
                            NodeTemplate="{StaticResource NodeTemplate}"
                            LinkTemplate="{StaticResource LinkTemplate}" />
    <!-- The template ships this resource empty; add MenuItem entries, each bound to the pressed link. -->
    <ContextMenu x:Key="LinkContextMenu" />
  </UserControl.Resources>
  <Grid>
    <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E"
            BorderBrush="#33FFFFFF" BorderThickness="1" CornerRadius="3">
      <local:GridDecorator x:Name="PART_GridDecorator">
        <ScrollViewer x:Name="PART_ScrollViewer">
          <Canvas x:Name="PART_Canvas" Background="Transparent"
                  behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                  behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
        </ScrollViewer>
      </local:GridDecorator>
    </Border>
    <local:MinimapOverlay x:Name="PART_MinimapOverlay"
                          HorizontalAlignment="Stretch" VerticalAlignment="Stretch"
                          ScrollViewerName="PART_ScrollViewer" />
  </Grid>
</UserControl>
```

The tree's code-behind re-exposes the canvas transform under a plain name. **Keep this mirror**: Jalium's binding engine cannot address `(behaviors:WorkflowSurfaceBehavior.CanvasTransform)`, and without it every card stays at the world origin after a pan, with no error.

```csharp
using Jalium.UI;
using Jalium.UI.Controls;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

namespace MyWorkflowApp.Views.Workflow;

public partial class TreeView : UserControl
{
    public static readonly DependencyProperty CanvasTransformProperty =
        WorkflowSurfaceBehavior.CanvasTransformProperty;

    public Transform? CanvasTransform => GetValue(CanvasTransformProperty) as Transform;

    public TreeView() => InitializeComponent();
}
```

The generated `LinkView` draws a cubic from `Sender.Anchor` to `Receiver.Anchor` and calls `WorkflowLinkBounds.Apply` before drawing, moving its own layout box onto the curve. That call is not optional: Jalium drops a child that draws outside its box, and the symptom is links vanishing at deep zoom. Hit testing uses the curve published with `link.PublishCurve(...)`, not the box.

## 4. Put the tree in a window

`MainView.jalxaml`:

```xml
<UserControl xmlns="http://schemas.jalium.com/jalxaml"
             xmlns:local="clr-namespace:MyWorkflowApp.Views.Workflow"
             x:Class="MyWorkflowApp.Views.MainView">
    <local:TreeView Background="#1E1E1E" />
</UserControl>
```

`MainView.jalxaml.cs` builds the model and hands it over. Place the four ViewModel classes in `MyWorkflowApp.ViewModels`.

```csharp
using Jalium.UI.Controls;
using MyWorkflowApp.ViewModels;
using VeloxDev.WorkflowSystem;
using Size = VeloxDev.WorkflowSystem.Size;

namespace MyWorkflowApp.Views;

public partial class MainView : UserControl
{
    public MainView()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        LoadSample(tree);
        DataContext = tree;
    }

    private static void LoadSample(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);
        var size = new Size(260, 180);

        var source = new NodeViewModel
        {
            Name = "Source",
            Size = size,
            Anchor = new Anchor { Horizontal = 0, Vertical = 0 }
        };
        var sink = new NodeViewModel
        {
            Name = "Sink",
            Size = size,
            Anchor = new Anchor { Horizontal = 360, Vertical = 0 }
        };

        tree.CreateNodeCommand.Execute(source);
        tree.CreateNodeCommand.Execute(sink);

        source.OutputSlots.SetSelector(typeof(bool));
        source.InputSlot.SetChannelCommand.Execute(SlotChannel.OneSource);
        sink.InputSlot.SetChannelCommand.Execute(SlotChannel.MultipleSources);

        if (source.OutputSlots.Items.FirstOrDefault()?.Slot is { } sender)
        {
            tree.Links.Add(new LinkDefaultViewModel
            {
                Sender = sender,
                Receiver = sink.InputSlot,
                IsVisible = true
            });
        }
    }
}
```

`MainWindow.jalxaml` hosts it:

```xml
<Window xmlns="http://schemas.jalium.com/jalxaml"
        xmlns:views="clr-namespace:MyWorkflowApp.Views"
        x:Class="MyWorkflowApp.MainWindow"
        Title="VeloxDev Jalium" Width="1100" Height="720" Background="#1E1E1E">
    <views:MainView />
</Window>
```

`MainWindow.jalxaml.cs` is the generator's thin half:

```csharp
using Jalium.UI;
using Jalium.UI.Controls;

namespace MyWorkflowApp;

public partial class MainWindow : Window
{
    public MainWindow() => InitializeComponent();
}
```

**Expected result:** the window opens to a grid with floating rulers, two 260×180 cards and the link between them.

## 5. What the adapter owns

- `WorkflowSurfaceBehavior` handles the camera, hit testing, input routing, virtualisation, the link menu and the `ZoomPin` guard that re-virtualises immediately after a zoom commit.
- `WorkflowSlotLayoutBehavior` measures the named port controls and writes `slot.Anchor`; `WorkflowNodeDragBehavior` turns a title-bar drag into `MoveCommand`; `WorkflowSlotConnectionBehavior` drives the connection gesture.
- `ViewPool` fills `PART_Canvas` from `Helper.VisibleItems`. The pool's selector is the `WorkflowTemplateSelector` resource.
- The whole grid renderer is template-owned: `GridDecorator : Grid, IWorkflowGridDecorator`. The adapter ships no grid class. The Jalium pack's default ruler thickness is 36, not the 28 used by the other packs; read `RulerBand` when syncing the virtualise inset.

## Where the pieces come from

| Piece | File |
| --- | --- |
| Attached behaviours, `WorkflowLinkBounds`, `WorkflowMinimapOverlay`, `ViewPool` | `Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/` |
| View hosting (`ViewSourcePipeline`, containers, scheduler) | `Src/Adapters/VeloxDev.Jalium/WorkflowSystem/ViewHosting/` |
| Generated roles | the Jalium item-template pack, mirrored in `Examples/Workflow/Jalium Trimmed/Demo/Views/Workflow/` |
| Host composition | `Examples/Workflow/Jalium Trimmed/Demo/Views/MainView.jalxaml.cs` |
