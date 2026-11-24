# 验证与完整代码

## 运行

```powershell
dotnet run
```

**预期结果**，按顺序：

1. 窗口打开为深色表面，世界网格与上/左标尺带可见。
2. 两个 260×180 的卡片以及它们之间的连线可见。
3. 拖动卡片标题条会移动卡片；相机不动。
4. 拖动空白表面会平移；指针下的世界点保持不动。
5. Ctrl+滚轮绕指针缩放；卡片、文字、端口与连线一起缩放。
6. 从端口拖出橡皮筋；在另一张卡片的合法端口上释放会再创建一条连线。
7. 右键点击连线会打开含 `Delete` 的菜单；选择后连线被删除。
8. Ctrl+Z 与 Ctrl+Y 撤销、重做结构性改动。

## 输入走路由，不挂在控件上

表面把原生指针、滚轮与按键事件翻译后转发给 `WorkflowInput.For(tree)`。在树的 helper 上订阅，而不是在每张卡片上：

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

撤销覆盖的是结构性改动：创建/删除、连接/断开、选择器变更可撤销；节点移动与槽通道写入属于运行期状态，刻意不入撤销栈。

## 完整代码

单文件。下面是 ViewModel 与 `MainForm`；七个视图角色来自[表面与宿主](../01_表面与宿主/index.md)生成的、位于 `MyWorkflowApp.Views` 的文件：`TreeView`、`NodeView`、`SlotView`、`LinkView`、`GridDecorator`、`MinimapOverlay` 与 `CustomTemplateSelector`。同一批文件在 `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/`。

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

符号来源：

- `TreeViewModel`、`NodeViewModel`、`SlotViewModel`、`VirtualizeHelper` —— 本块内定义。
- `TreeView`、`NodeView`、`SlotView`、`LinkView`、`GridDecorator`、`MinimapOverlay`、`CustomTemplateSelector` —— 由[表面与宿主](../01_表面与宿主/index.md)里的 `winforms-v-*` 生成；镜像在 `Examples/Workflow/WinForms Trimmed/Demo/Views/Workflow/`。
- `ApplicationConfiguration` —— WinForms SDK 生成。
- `WorkflowSurfaceBehavior`、`ViewPool` —— `Src/Adapters/VeloxDev.WinForms/WorkflowSystem/AttachedBehaviors/`。

## 运行声明

⚠️ 未实际运行 —— 2026-11-25 仅对照当前源码与 `Examples/Workflow/WinForms Trimmed/Demo/` 静态核验。GUI 需要 Windows 与 Easel 生成器；本页复刻了 demo 的调用序列，但这里没有记录构建输出。
