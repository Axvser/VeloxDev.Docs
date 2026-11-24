# 表面与宿主

三样东西让窗口跑起来：ViewModel、七个生成的视图角色，以及一个把树放进 `VisualHost` 并把 `WorkflowSurfaceBehavior` 指向具名部件的 `MainForm`。

## 1. 定义 ViewModel

每个组件都是一个 `partial` 类，拆成 ViewModel 与 helper。特性生成 ViewModel 那一半；helper 类型提供行为。

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

`InitializeWorkflow()` 由生成器产出，但构造函数不会；要自己调用。`TreeHelper(200)` 打开空间索引，`Helper.VisibleItems` 依赖它；无参 `TreeHelper` 不启用虚拟化。

**预期结果：** 工程通过编译，生成的 `Name`、`InputSlot`、`OutputSlots`、`CreateNodeCommand` 与 `InitializeWorkflow` 都能解析。

## 2. 生成七个视图

```powershell
dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views
```

七个必须落在同一个命名空间：树按类型名解析兄弟。改其中一个名字，必须在同一次改动里改树的标记。生成的树的 code-behind 只有 `InitializeComponent()`。

**预期结果：** `Views/` 下出现七个条目 —— 四对 `.xaml` + `.xaml.cs` 与三个 `.cs`。

## 3. 生成的树声明了什么

树就是部件布局。宿主不创建画布、滚动容器或装饰器，只给它们命名。

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

生成文件还会在 `TreeView.Resources` 里声明三个 `DataTemplate`（`NodeTemplate`、`SlotTemplate`、`LinkTemplate`）、一个空的 `VisualContextMenu x:Key="LinkContextMenu"`，以及 `CustomTemplateSelector x:Key="WorkflowTemplateSelector"`。

- `x:Name` 就是视觉 `Name`；`WorkflowSurfaceBehavior` 通过它解析 `PART_*`。
- `ViewPool` 从 `Helper.VisibleItems` 喂 `PART_Canvas`；选择器决定每个条目用哪个视图。
- 连线视图每条线一个，自己发布曲线。它设置 `UnboundedHitTest`，避免 Easel 按包围盒做的 damage cull 把负象限里的整棵视图剔除。

**预期结果：** 七个文件齐全后，生成的代码通过编译。

## 4. 承载表面

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

`SetIsEnabled` 启动表面生命周期；`SetWorkflowTree` 显式绑定模型。树不是通过 `DataContext` 进来的。

`Layout.NegativeOffset` 把可见世界原点移位，使负象限里的节点也可达。相机把 `Viewport = (-(pan + content) / zoom, size / zoom)` 回报给树，因此 `Helper.VisibleItems` 跟随平移与缩放。

**预期结果：** 窗口打开为深色表面，世界网格与浮动标尺可见，两个 260×180 的卡片连同端口、以及它们之间的连线出现在画面里。

## 各部件在哪

| 部件 | 文件 |
| --- | --- |
| `WorkflowSurfaceBehavior`、`ViewPool`、`WorkflowSlotLayoutBehavior`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowMinimapOverlay` | `Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/` |
| 生成的视图角色 | WinForms 条目模板包，镜像在 `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/` |
| 宿主组合 | `Examples/Workflow/WinForms Trimmed/Demo/MainForm.cs` |
