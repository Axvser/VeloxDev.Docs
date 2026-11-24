# Surface and host

Four ViewModels, seven generated components and one page make the surface. The page owns the tree; the generated `TreeView` owns every part name and every binding.

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

Place the four classes in `MyWorkflowApp.ViewModels`; the `_Imports.razor` below imports that namespace.

`InitializeWorkflow()` is generated; call it from your constructor. `TreeHelper(200)` enables the spatial map behind `Helper.VisibleItems`, which the generated page pools over.

**Expected result:** `Name`, `InputSlot`, `OutputSlots`, `CreateNodeCommand` and `InitializeWorkflow` resolve.

## 2. Generate the seven components

```powershell
dotnet new razor-v-tree      -n TreeView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-node      -n NodeView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-slot      -n SlotView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-link      -n LinkView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-selector  -n TemplateSelector      -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-decorator -n GridDecorator         -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
```

All seven share one namespace; the tree resolves its siblings by bare type name through `@namespace` + `@using`. Every item generates a `.razor` + `.razor.cs` pair, including the selector, decorator and minimap.

**Expected result:** fourteen files in `Components/Workflow/`.

## 3. Add the usings

`Components/_Imports.razor`:

```razor
@using MyWorkflowApp.Components.Workflow
@using MyWorkflowApp.ViewModels
@using static Microsoft.AspNetCore.Components.Web.RenderMode
```

## 4. Host the surface

`Components/Pages/Home.razor`:

```razor
@page "/"
@rendermode RenderMode.InteractiveServer
@using VeloxDev.WorkflowSystem

<PageTitle>VeloxDev Workflow</PageTitle>

<div style="position:relative;width:100vw;height:100vh;">
    @if (_tree is not null)
    {
        <TreeView Tree="_tree" />
    }
</div>

@code {
    private TreeViewModel? _tree;

    protected override void OnInitialized()
    {
        _tree = new TreeViewModel();
        LoadSample(_tree);
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

The surface needs a parent with a real height. `100vh` gives the scroll element a viewport; a `height: auto` parent collapses it and the canvas measures zero.

## 5. What the generated tree does

- `WorkflowSurfaceBehavior` receives `Tree`, `IsEnabled`, `ZoomEnabled`, `ScrollViewerId`, `CanvasId` and `GridSpacing`. It renders the scroll/canvas DOM and routes the wheel, pointer and key events.
- `Tree.GetHelper().VisibleItems` is the pool source. The generated `TemplateSelector` dispatches each item to `NodeView` or `LinkView`; the virtual link is already in that collection, so no extra branch is needed.
- The generated `RenderGenericLink` wraps the link view in `display:contents;pointer-events:none`. Keep the wrapper: the SVG spans the canvas, and without `pointer-events:none` it would swallow every canvas gesture.
- The node card is design-size content with a CSS `transform: scale(...)`. The browser scales it, so `getBoundingClientRect()` includes the transform and slot anchors stay correct through zoom.
- `DrawMinimap` is a render fragment, not a virtual method — Razor components cannot override another component's render tree. The fragment is the customisation point.

**Expected result:** the page builds, and the surface frame, grid, two node cards and the link between them render at the page root.

## Where the pieces come from

| Piece | File |
| --- | --- |
| `WorkflowSurfaceBehavior`, `ViewPool`, `WorkflowGridDecorator`, `WorkflowMinimapOverlay`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowPresentation` | `Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/` |
| JS and CSS | `Src/Adapters/VeloxDev.Razor/wwwroot/veloxdev.workflow.js` and `.css` |
| Generated components | the Razor item-template pack, mirrored in `Examples/Workflow/Blazor Trimmed/Demo/Components/Workflow/` |
| Host page | `Examples/Workflow/Blazor Trimmed/Demo/Components/Pages/Home.razor` |
