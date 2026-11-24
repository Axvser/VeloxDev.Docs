# 表面与宿主

四个 ViewModel、七个生成的组件和一个页面组成表面。页面持有树；生成的 `TreeView` 负责所有部件名与绑定。

## 1. 定义 ViewModel

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

把四个类放进 `MyWorkflowApp.ViewModels`；下面的 `_Imports.razor` 导入该命名空间。

`InitializeWorkflow()` 由生成器产出，要在自己的构造函数里调用。`TreeHelper(200)` 打开 `Helper.VisibleItems` 背后的空间索引，生成的页面就在它上面池化。

**预期结果：** `Name`、`InputSlot`、`OutputSlots`、`CreateNodeCommand` 与 `InitializeWorkflow` 都能解析。

## 2. 生成七个组件

```powershell
dotnet new razor-v-tree      -n TreeView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-node      -n NodeView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-slot      -n SlotView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-link      -n LinkView              -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-selector  -n TemplateSelector      -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-decorator -n GridDecorator         -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
dotnet new razor-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Components.Workflow -o Components/Workflow
```

七个共用一个命名空间；树通过 `@namespace` + `@using` 按裸类型名解析兄弟。每个条目都生成 `.razor` + `.razor.cs` 一对，选择器、装饰器与小地图也不例外。

**预期结果：** `Components/Workflow/` 下十四个文件。

## 3. 添加 using

`Components/_Imports.razor`：

```razor
@using MyWorkflowApp.Components.Workflow
@using MyWorkflowApp.ViewModels
@using static Microsoft.AspNetCore.Components.Web.RenderMode
```

## 4. 承载表面

`Components/Pages/Home.razor`：

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

表面需要一个有真实高度的父容器。`100vh` 给滚动元素一个视口；`height: auto` 的父级会把它压塌，画布量到 0。

## 5. 生成的树做了什么

- `WorkflowSurfaceBehavior` 接收 `Tree`、`IsEnabled`、`ZoomEnabled`、`ScrollViewerId`、`CanvasId` 与 `GridSpacing`。它渲染滚动/画布 DOM，并路由滚轮、指针与按键事件。
- 池的来源是 `Tree.GetHelper().VisibleItems`。生成的 `TemplateSelector` 把每个条目分派给 `NodeView` 或 `LinkView`；虚拟连线本来就在这个集合里，不需要额外分支。
- 生成的 `RenderGenericLink` 把连线视图包进 `display:contents;pointer-events:none`。保留这个 wrapper：SVG 铺满画布，没有 `pointer-events:none` 会吞掉画布手势。
- 节点卡是设计尺寸的内容加 CSS `transform: scale(...)`。浏览器负责缩放，所以 `getBoundingClientRect()` 包含该变换，插槽锚点在缩放中仍然正确。
- `DrawMinimap` 是一个 render fragment，不是虚方法 —— Razor 组件不能覆写另一个组件的渲染树。这个 fragment 就是定制点。

**预期结果：** 页面编译通过，表面框架、网格、两个节点卡片以及它们之间的连线渲染在页面根部。

## 各部件在哪

| 部件 | 文件 |
| --- | --- |
| `WorkflowSurfaceBehavior`、`ViewPool`、`WorkflowGridDecorator`、`WorkflowMinimapOverlay`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`、`WorkflowPresentation` | `Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/` |
| JS 与 CSS | `Src/Adapters/VeloxDev.Razor/wwwroot/veloxdev.workflow.js` 与 `.css` |
| 生成的组件 | Razor 条目模板包，镜像在 `Examples/Workflow/Blazor Trimmed/Demo/Components/Workflow/` |
| 宿主页面 | `Examples/Workflow/Blazor Trimmed/Demo/Components/Pages/Home.razor` |
