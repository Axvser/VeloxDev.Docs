# 表面搭建

Avalonia 表面与 WPF 一样是 `UserControl`。附着属性与 `PART_*` 名字完全相同；差别在 XML 命名空间写法、编译绑定，以及没有 `PreviewMouseWheel` 阶段（适配器自己注册隧道处理器）。

## ViewModel

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace MyApp;

internal sealed class VirtualizeHelper() : TreeHelper(200) { }

[WorkflowBuilder.Tree<VirtualizeHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class NodeViewModel
{
    public NodeViewModel() => InitializeWorkflow();

    [VeloxProperty] private string _name = string.Empty;

    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}
```

`VirtualizeHelper` 派生自 `TreeHelper(200)`；单元格尺寸构造函数才是打开虚拟化的那个，表面的无条件 `Viewport` 写入需要它。

**预期结果：** 生成的树暴露 `Helper`、`Nodes`、`Links` 与标准命令；节点暴露 `Name`、`InputSlot` 与 `OutputSlots`。

## 表面

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp"
             xmlns:vm="using:MyApp"
             xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
             x:DataType="vm:TreeViewModel"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate" DataType="vm:NodeViewModel">
            <Grid Width="{Binding Size.Width}"
                  Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}"
                  Canvas.Top="{Binding Anchor.Vertical}"
                  ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                  behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                  behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Border Background="#FFFFFFFF" BorderBrush="#331E1E1E" BorderThickness="1" CornerRadius="6" />
                <Grid Height="32" VerticalAlignment="Top" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" Margin="10,8" />
                </Grid>
                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
                         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
                         HorizontalAlignment="Left" VerticalAlignment="Center" />
                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}"
                              Margin="10" VerticalAlignment="Bottom">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" />
                                <Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
                                         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right" />
                            </Grid>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>
            </Grid>
        </DataTemplate>

        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}" />
    </UserControl.Resources>

    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto"
                          IsScrollInertiaEnabled="False">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>

        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                          HorizontalAlignment="Stretch"
                                          VerticalAlignment="Stretch"
                                          ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

Avalonia 的模板选择器是 `IDataTemplate`：它既选又建。`ViewPool.TemplateSelector` 的类型就是 `IDataTemplate?`。

```csharp
using System;
using Avalonia.Controls;
using Avalonia.Controls.Templates;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : IDataTemplate
{
    public IDataTemplate? NodeTemplate { get; set; }
    public IDataTemplate? LinkTemplate { get; set; }

    public Control Build(object? parameter)
        => Select(parameter).Build(parameter)
           ?? throw new InvalidOperationException($"The selected template could not build {parameter?.GetType().FullName}.");

    public bool Match(object? data) => data is INodeComponent or ILinkComponent;

    private IDataTemplate Select(object? item) => item switch
    {
        ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
        INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
}
```

**预期结果：** `WorkflowTemplateSelector.Match` 接受节点，`Build` 返回节点视图，`ViewPool` 为每个可见节点物化一个视图。

## 代码后置

```csharp
using Avalonia.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class WorkflowSurface : UserControl
{
    public WorkflowSurface()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        LoadTree(tree);
        DataContext = tree;
    }

    private static void LoadTree(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);

        for (var i = 0; i < 3; i++)
        {
            tree.CreateNodeCommand.Execute(new NodeViewModel
            {
                Name = $"Node {i + 1}",
                Size = new VeloxDev.WorkflowSystem.Size(220, 120),
                Anchor = new Anchor(120 + (i * 280), 140, 0)
            });
        }
    }
}
```

**预期结果：** 画布上出现三张卡，整张卡都能拖动。Ctrl+滚轮缩放，普通滚轮由适配器滚动，而不是走 `ScrollViewer` 的惯性。

## 编译绑定

- `AvaloniaUseCompiledBindingsByDefault=true` 是 `x:DataType` 成为必需项的原因。没有它，每个绑定作用域都要自己标注，否则报 `AVLN2100`。
- `DataTemplate` 需要**具体**类型，不能是接口。树的 `x:DataType` 写 `TreeViewModel`，因为 `ITreeComponent` 上没有可绑的 `Helper` 属性。
- 祖先绑定写成 `$parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)`。当前缀出现在绑定路径里、模板构建时解析失败，视图管理器会吞掉异常，画布就只是空着；遇到这种情况改用程序集限定的 `clr-namespace:MyApp;assembly=MyApp`。
- 模板包里的节点视图带着 `x:CompileBindings="False"` 和一行「换成具体 `x:DataType`」的注释；本页直接从具体形式起步。
