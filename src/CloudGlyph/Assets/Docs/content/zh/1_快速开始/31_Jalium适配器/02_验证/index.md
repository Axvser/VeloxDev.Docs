# 验证与完整代码

## 接上入口

桌面宿主需要一个 `AppBuilder`。`Program.cs`：

```csharp
using Jalium.UI;

namespace MyWorkflowApp;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        var builder = AppBuilder.CreateBuilder(new AppBuilderSettings
        {
            Args = args,
            DisableDefaults = true
        });

        builder.ConfigureApplication(app => app.MainWindow = new MainWindow());

        using var host = builder.Build();
        return host.Run();
    }
}
```

`DisableDefaults` 跳过 demo 不需要的宿主默认项；你的应用要用它们时去掉这一行。

## 运行

```powershell
dotnet run
```

**预期结果**，按顺序：

1. 窗口打开为世界网格与上/左浮动标尺带。
2. 两个 260×180 的卡片以及它们之间的连线可见。
3. 拖动卡片标题栏会移动卡片；拖动空白表面会平移。
4. Ctrl+滚轮绕视口中心缩放；放大时 `Scale` 反而变小（`Scale *= 1 / 1.1`）。
5. 从端口拖出橡皮筋；在另一张卡片的合法端口上释放会再创建一条连线。
6. 右键点击连线会打开 `LinkContextMenu`；模板把它留空，要看到 Delete 需自行加一个绑定 `DeleteCommand` 的 `MenuItem`。
7. 缩到 40% 时连线仍连着两端，并且仍被画出。

## 先查这两个 Jalium 坑

- **平移后卡片停在世界原点。** 树 code-behind 少了 `CanvasTransform` 镜像，或节点/连线模板绑了附着属性而不是普通 `CanvasTransform`。平移从未应用，且什么都不报。
- **深缩放时连线消失。** `LinkView` 不再调用 `WorkflowLinkBounds.Apply`；布局盒盖不住曲线，Jalium 渲染器把它丢弃。命中测试也会退化，因为视图在同一趟里发布曲线。

普通滚轮经 `WorkflowInput.Scroller` 路由；只有 Ctrl+滚轮是缩放手势。平移从 `PART_SurfaceBorder` 上的左键按下开始，所以落在卡片或端口上的按下会移动节点或开始连线。

## 完整代码

`Views/MainView.jalxaml.cs`。四个 ViewModel 与七个生成角色定义在[表面与宿主](../01_表面与宿主/index.md)。

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

符号来源：

- `TreeViewModel`、`NodeViewModel`、`SlotViewModel`、`VirtualizeHelper` —— [表面与宿主](../01_表面与宿主/index.md)。
- `TreeView`、`NodeView`、`SlotView`、`LinkView`、`TemplateSelector`、`GridDecorator`、`MinimapOverlay` —— 由 `jalium-v-*` 生成；镜像在 `Examples/Workflow/Jalium Trimmed/Demo/Views/Workflow/`。
- `AppBuilder`、`AppBuilderSettings`、`UserControl` —— `Jalium.UI`。
- `WorkflowLinkBounds`、`WorkflowSurfaceBehavior` —— `Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/`。

## 运行声明

⚠️ 未实际运行 —— 2026-11-25 仅对照当前源码与 `Examples/Workflow/Jalium Trimmed/Demo/` 静态核验。运行需要 .NET 10 SDK 与 Jalium 原生运行时；这里没有记录窗口输出。
