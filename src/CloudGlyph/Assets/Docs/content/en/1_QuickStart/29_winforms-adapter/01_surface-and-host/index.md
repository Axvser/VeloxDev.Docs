# Surface and host

Three things make the window work: the ViewModels, the seven generated view roles, and a `MainForm` that hosts the tree in a `VisualHost` and points `WorkflowSurfaceBehavior` at the named parts.

## 1. Define the ViewModels

Every component is a `partial` class split into a ViewModel and a helper. The attributes generate the ViewModel half; the helper type supplies the behaviour.

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

`InitializeWorkflow()` is generated but no constructor is, so call it yourself. `TreeHelper(200)` enables the spatial map behind `Helper.VisibleItems`; the parameterless `TreeHelper` leaves virtualization off.

**Expected result:** the project compiles, and the generated members `Name`, `InputSlot`, `OutputSlots`, `CreateNodeCommand` and `InitializeWorkflow` resolve.

## 2. Generate the seven views

```powershell
dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views
```

All seven must share one namespace: the tree resolves its siblings by type name. Renaming one means editing the tree markup in the same change. The generated tree's code-behind is only `InitializeComponent()`.

**Expected result:** seven items in `Views/` — four `.xaml` + `.xaml.cs` pairs and three `.cs` files.

## 3. What the generated tree declares

The tree is the part layout. The host does not create the canvas, the scroll viewer or the decorator; it names them.

```xml
<local:TreeView xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WinForms"
                xmlns:local="clr-namespace:MyWorkflowApp.Views"
                x:Class="MyWorkflowApp.Views.TreeView"
                ClipToBounds="False">
  <Grid ClipToBounds="False">
    <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E"
            BorderBrush="#33FFFFFF" BorderThickness="1" CornerRadius="0">
      <local:GridDecorator x:Name="PART_GridDecorator"
                           GridSpacing="40" MajorLineEvery="5"
                           RulerThickness="28" DrawSurface="False">
        <ScrollViewer x:Name="PART_ScrollViewer" IsScrollInputEnabled="False">
          <Canvas x:Name="PART_Canvas" UnboundedHitTest="True" ClipToBounds="False"
                  behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                  behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
        </ScrollViewer>
      </local:GridDecorator>
    </Border>
    <local:MinimapOverlay x:Name="PART_MinimapOverlay"
                          HorizontalAlignment="Stretch" VerticalAlignment="Stretch" />
  </Grid>
</local:TreeView>
```

The generated file also declares three `DataTemplate`s (`NodeTemplate`, `SlotTemplate`, `LinkTemplate`), an empty `VisualContextMenu x:Key="LinkContextMenu"`, and `CustomTemplateSelector x:Key="WorkflowTemplateSelector"` in `TreeView.Resources`.

- `x:Name` is the visual `Name`; `WorkflowSurfaceBehavior` resolves `PART_*` through it.
- `ViewPool` feeds `PART_Canvas` from `Helper.VisibleItems`; the selector picks the view for each item.
- A link view is created per link and publishes its own curve. It sets `UnboundedHitTest` so Easel's damage cull does not drop it in negative world quadrants.

**Expected result:** the generated files compile after all seven are present.

## 4. Host the surface

```csharp
using System.Windows.Forms;
using Easel;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

internal sealed class MainForm : Form
{
    public MainForm()
    {
        Text = "VeloxDev WinForms";
        ClientSize = new System.Drawing.Size(1085, 683);
        BackColor = System.Drawing.Color.FromArgb(30, 30, 30);

        var host = new VisualHost
        {
            Dock = DockStyle.Fill,
            Root = new MyWorkflowApp.Views.TreeView()
        };
        Controls.Add(host);

        WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
        WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
        WorkflowSurfaceBehavior.SetGridDecoratorName(host, "PART_GridDecorator");
        WorkflowSurfaceBehavior.SetMinimapOverlayName(host, "PART_MinimapOverlay");
        WorkflowSurfaceBehavior.SetLinkMenuBuilder(host, BuildLinkMenu);
        WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
        WorkflowSurfaceBehavior.SetIsEnabled(host, true);

        var tree = new TreeViewModel();
        LoadSample(tree);
        WorkflowSurfaceBehavior.SetWorkflowTree(host, tree);
        WireInput(tree);
    }

    private ITreeComponent? _tree;

    private void WireInput(ITreeComponent tree)
    {
        _tree = tree;
        if (tree.GetHelper() is not IInputEvents events) return;
        events.Input.KeyDown += OnKeyDown;
    }

    private void OnKeyDown(object? sender, KeyDownEventArgs e)
    {
        if (_tree is not { } tree) return;

        if (e.Key == InputKey.Delete
            && WorkflowInput.For(tree).HoveredLink is { } link
            && link.DeleteCommand.CanExecute(null))
        {
            link.DeleteCommand.Execute(null);
            e.Handle.PreventDefault = true;
            return;
        }

        if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;

        var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
        if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
        else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
        else return;

        e.Handle.PreventDefault = true;
    }

    private static void BuildLinkMenu(ContextMenuStrip menu, ILinkComponent link)
        => menu.Items.Add("Delete", null, (_, _) =>
        {
            if (link.DeleteCommand.CanExecute(null))
            {
                link.DeleteCommand.Execute(null);
            }
        });

    private static void LoadSample(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);
        var size = new VeloxDev.WorkflowSystem.Size(260, 180);

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

`SetIsEnabled` starts the surface lifecycle; `SetWorkflowTree` binds the model explicitly. The tree does not arrive through a `DataContext`.

`Layout.NegativeOffset` shifts the visible world origin so nodes in negative quadrants are reachable. The camera reports `Viewport = (-(pan + content) / zoom, size / zoom)` back to the tree, so `Helper.VisibleItems` follows pan and zoom.

**Expected result:** the window opens to a dark surface with a world grid and floating rulers, and two 260×180 cards with their ports and the link between them are visible.

## Where the pieces come from

| Piece | File |
| --- | --- |
| `WorkflowSurfaceBehavior`, `ViewPool`, `WorkflowSlotLayoutBehavior`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowMinimapOverlay` | `Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/` |
| Generated view roles | the WinForms item-template pack, mirrored in `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/` |
| Host composition | `Examples/Workflow/WinForms Trimmed/Demo/MainForm.cs` |
