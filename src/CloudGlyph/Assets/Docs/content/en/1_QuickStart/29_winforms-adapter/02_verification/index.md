# Verification and complete code

## Run it

```powershell
dotnet run
```

**Expected result**, in order:

1. The window opens to a dark surface with a world grid and top/left ruler bands.
2. Two 260×180 cards and the link between them are visible.
3. Dragging the card's title strip moves the card; the camera stays put.
4. Dragging blank surface pans; the world point under the pointer stays under it.
5. Ctrl+wheel zooms around the pointer; the card, text, ports and link scale together.
6. Dragging from a port starts a rubber band; releasing on the other card's legal port creates a second link.
7. Right-pressing a link opens the menu with `Delete`; choosing it removes the link.
8. Ctrl+Z and Ctrl+Y undo and redo structural changes.

## Input is routed, not per-control

The surface translates native pointer, wheel and key events and forwards them to `WorkflowInput.For(tree)`. Subscribe on the tree's helper — not on individual cards:

```csharp
if (tree.GetHelper() is IInputEvents events)
{
    events.Input.KeyDown += (_, e) =>
    {
        if (e.Key == InputKey.Delete
            && WorkflowInput.For(tree).HoveredLink is { } link
            && link.DeleteCommand.CanExecute(null))
        {
            link.DeleteCommand.Execute(null);
            e.Handle.PreventDefault = true;
        }
    };
}
```

Undo coverage is structural: create/delete, connect/disconnect and selector changes are undoable; node moves and slot-channel writes are runtime state and deliberately do not enter the history.

## Complete code

One file. The ViewModels and `MainForm` are below; the seven view roles are the generated files from [Surface and host](../01_surface-and-host/index.md), which resolve as `MyWorkflowApp.Views.TreeView`, `NodeView`, `SlotView`, `LinkView`, `GridDecorator`, `MinimapOverlay` and `CustomTemplateSelector`. The same files are in `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/`.

```csharp
using System.Windows.Forms;
using Easel;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
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
        WorkflowSurfaceBehavior.SetLinkMenuBuilder(host, static (menu, link) =>
            menu.Items.Add("Delete", null, (_, _) =>
            {
                if (link.DeleteCommand.CanExecute(null))
                {
                    link.DeleteCommand.Execute(null);
                }
            }));
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

Symbol sources:

- `TreeViewModel`, `NodeViewModel`, `SlotViewModel`, `VirtualizeHelper` — defined in this block.
- `TreeView`, `NodeView`, `SlotView`, `LinkView`, `GridDecorator`, `MinimapOverlay`, `CustomTemplateSelector` — generated by `winforms-v-*` in [Surface and host](../01_surface-and-host/index.md); mirror in `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/`.
- `ApplicationConfiguration` — generated by the WinForms SDK.
- `WorkflowSurfaceBehavior`, `ViewPool` — `Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/`.

## Run declaration

⚠️ Not actually run — statically verified against the current source and `Examples/Workflow/WinForms Trimmed/Demo/` on 2026-11-25. The GUI requires Windows and the Easel generator; the call sequence is reproduced from the demo, but no build output was recorded here.
