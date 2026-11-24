# 表面与宿主

表面是标记加附着行为。树模板给部件命名；`WorkflowSurfaceBehavior` 驱动它们。宿主只负责把树作为 `DataContext` 交出去，并把树视图放进窗口。

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

**预期结果：** 生成的成员都能解析，包括 `Name`、`InputSlot`、`OutputSlots` 与 `CreateNodeCommand`。

## 2. 生成七个角色

```powershell
dotnet new jalium-v-tree      -n TreeView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-node      -n NodeView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-slot      -n SlotView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-link      -n LinkView              -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-selector  -n TemplateSelector      -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
dotnet new jalium-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views.Workflow -o Views/Workflow
```

四个条目产出 `.jalxaml` + `.jalxaml.cs`（树、节点、插槽、连线）；三个只产出一个 `.cs`（选择器、装饰器、小地图）。七个共用同一个标记命名空间。

**预期结果：** `Views/Workflow/` 下十一个文件。

## 3. 树表面

生成的树把附着属性挂在根上，并给部件命名：

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
    <!-- 模板把这个资源留空；自行添加 MenuItem 条目，每个条目绑定被右键的连线。 -->
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

树的 code-behind 把画布变换以普通名字再暴露一次。**保留这个镜像**：Jalium 的绑定引擎无法寻址 `(behaviors:WorkflowSurfaceBehavior.CanvasTransform)`，缺了它，平移后每张卡片都停在世界原点，且不报错。

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

生成的 `LinkView` 从 `Sender.Anchor` 到 `Receiver.Anchor` 画三次曲线，并在绘制前调用 `WorkflowLinkBounds.Apply`，把自己的布局盒挪到曲线上。这个调用不是可选的：Jalium 会丢弃画到盒外的子元素，症状是深缩放时连线消失。命中测试用的是 `link.PublishCurve(...)` 发布的曲线，不是盒子。

## 4. 把树放进窗口

`MainView.jalxaml`：

```xml
<UserControl xmlns="http://schemas.jalium.com/jalxaml"
             xmlns:local="clr-namespace:MyWorkflowApp.Views.Workflow"
             x:Class="MyWorkflowApp.Views.MainView">
    <local:TreeView Background="#1E1E1E" />
</UserControl>
```

`MainView.jalxaml.cs` 造模型并交出去。把四个 ViewModel 类放进 `MyWorkflowApp.ViewModels`。

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

`MainWindow.jalxaml` 承载它：

```xml
<Window xmlns="http://schemas.jalium.com/jalxaml"
        xmlns:views="clr-namespace:MyWorkflowApp.Views"
        x:Class="MyWorkflowApp.MainWindow"
        Title="VeloxDev Jalium" Width="1100" Height="720" Background="#1E1E1E">
    <views:MainView />
</Window>
```

`MainWindow.jalxaml.cs` 是生成器的薄半边：

```csharp
using Jalium.UI;
using Jalium.UI.Controls;

namespace MyWorkflowApp;

public partial class MainWindow : Window
{
    public MainWindow() => InitializeComponent();
}
```

**预期结果：** 窗口打开后可见网格与浮动标尺、两个 260×180 的卡片以及它们之间的连线。

## 5. 适配器负责什么

- `WorkflowSurfaceBehavior` 负责相机、命中、输入路由、虚拟化、连线菜单，以及缩放提交后立即重新虚拟化的 `ZoomPin` 守卫。
- `WorkflowSlotLayoutBehavior` 测量具名端口控件并把 `slot.Anchor` 写回；`WorkflowNodeDragBehavior` 把标题条拖动变成 `MoveCommand`；`WorkflowSlotConnectionBehavior` 驱动连线手势。
- `ViewPool` 从 `Helper.VisibleItems` 填充 `PART_Canvas`；池的 selector 就是 `WorkflowTemplateSelector` 资源。
- 整个网格渲染器归模板：`GridDecorator : Grid, IWorkflowGridDecorator`。适配器不提供网格类。Jalium 包默认标尺厚度是 36，不是其他包的 28；同步虚拟化 inset 时读 `RulerBand`。

## 各部件在哪

| 部件 | 文件 |
| --- | --- |
| 附着行为、`WorkflowLinkBounds`、`WorkflowMinimapOverlay`、`ViewPool` | `Src/Adapters/VeloxDev.Jalium/WorkflowSystem/AttachedBehaviors/` |
| 视图承载（`ViewSourcePipeline`、容器、调度器） | `Src/Adapters/VeloxDev.Jalium/WorkflowSystem/ViewHosting/` |
| 生成的角色 | Jalium 条目模板包，镜像在 `Examples/Workflow/Jalium Trimmed/Demo/Views/Workflow/` |
| 宿主组合 | `Examples/Workflow/Jalium Trimmed/Demo/Views/MainView.jalxaml.cs` |
