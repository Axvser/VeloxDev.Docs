# 表面搭建

WPF 表面是一个 `UserControl`：根元素带附着属性，每种工作流条目一个 `DataTemplate`。挂在画布上的 `ViewPool` 为每个可见项物化一个视图；表面从 `ScrollViewer` 写视口。

## 工程文件

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="VeloxDev.WPF" Version="12.3.0" />
  </ItemGroup>
</Project>
```

**预期结果：** `dotnet build` 还原 `VeloxDev.WPF` 与 `VeloxDev.Core`，退出码 `0`。

## ViewModel

生成器把这些特性变成树/节点/插槽/连线的实现，包括 `InitializeWorkflow()` 与标准命令。

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace MyApp;

internal sealed class VirtualizeHelper() : TreeHelper(200)
{
}

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

`TreeHelper(200)` 是单元格尺寸构造函数，会打开虚拟化。默认 `TreeHelper()` 不带虚拟化，而表面会无条件写 `Viewport`，所以真正渲染的树要用单元格尺寸那个。

**预期结果：** 生成的 `TreeViewModel` 暴露 `Helper`、`Nodes`、`Links` 与 `CreateNodeCommand`；生成的 `NodeViewModel` 暴露 `Name`、`InputSlot` 与 `OutputSlots`。

## 表面

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:MyApp"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Grid Width="{Binding Size.Width}"
                  Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}"
                  Canvas.Top="{Binding Anchor.Vertical}"
                  Panel.ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                                            Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                  behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                  behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Grid.RowDefinitions>
                    <RowDefinition Height="32" />
                    <RowDefinition Height="*" />
                </Grid.RowDefinitions>

                <Border Grid.RowSpan="2" Background="#FFFFFFFF" BorderBrush="#331E1E1E"
                        BorderThickness="1" CornerRadius="6" />

                <Grid Grid.Row="0" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" VerticalAlignment="Center" Margin="10,0" />
                </Grid>

                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
                         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
                         HorizontalAlignment="Left" VerticalAlignment="Center" />

                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}"
                              Grid.Row="1" Margin="10,6">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" HorizontalAlignment="Left" />
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
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E" BorderBrush="#33FFFFFF" BorderThickness="1">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto"
                          PanningMode="Both">
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

模板选择器只需要回答池会看到的条目类型：

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }

    public override DataTemplate SelectTemplate(object item, DependencyObject container)
        => item is INodeComponent
            ? NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set.")
            : throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}");
}
```

**预期结果：** 节点模板解析到 `NodeTemplate`；缺少选择器模板时在物化阶段抛异常，而不是留下一块空白画布。

## 代码后置

```csharp
using System.Windows.Controls;
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
                Size = new Size(220, 120),
                Anchor = new Anchor(120 + (i * 280), 140, 0)
            });
        }
    }
}
```

`Width`/`Height`/`Canvas.Left`/`Canvas.Top` 绑定的是**折叠后**的 `Size` 与 `Anchor`，模板自己不应用缩放。`RenderTransform` 绑定必须放在 `DataTemplate` 根上；从嵌套视图里做祖先查找，会在条目自己的树上解析，什么也找不到。

**预期结果：** 深色画布上出现三张节点卡。拖动卡片标题会移动节点，小地图显示对应缩略图。滚轮滚动，Ctrl+滚轮缩放。

## 网格从哪来

WPF 适配器**不自带**网格装饰器。它按 `GridDecoratorName` 解析元素，cast 成 `IWorkflowGridDecorator`，再把滚动/内容偏移推进去。demo 的 `WorkflowGridDecorator.cs` 是宿主侧实现。没有它表面照常工作，只是没有网格和标尺。它报告的 `RulerBand` 会被转给虚拟化器 —— 一个用标尺带盖住顶/左侧的装饰器必须返回那个厚度，否则下面的节点会被剔除。
