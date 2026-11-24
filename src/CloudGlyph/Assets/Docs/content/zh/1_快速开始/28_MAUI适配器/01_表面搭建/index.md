# 表面搭建

MAUI 的宿主是 `ContentView`。树就是它的 `BindingContext`，没有 `SetWorkflowTree` 调用。表面按名字解析 `PART_*`，在画布上池化节点视图，并用一个视口尺寸的覆盖层画所有连线。

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

**预期结果：** 生成的树暴露 `Helper`、`Nodes`、`Links` 与 `CreateNodeCommand`。

## 宿主

```xml
<ContentView xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             xmlns:local="clr-namespace:MyApp"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.MAUI"
             x:Class="MyApp.TreeView"
             x:Name="Root"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <ContentView.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Border BackgroundColor="#FFFFFFFF" Stroke="#331E1E1E" StrokeThickness="1"
                    StrokeShape="RoundRectangle 6"
                    WidthRequest="{Binding Size.Width}" HeightRequest="{Binding Size.Height}"
                    behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                    behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                    behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                    behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Grid RowDefinitions="32,*">
                    <Grid Grid.Row="0" BackgroundColor="Transparent"
                          behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                          behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                        <Label Text="{Binding Name}" Margin="10,0" VerticalTextAlignment="Center" />
                    </Grid>
                    <Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}"
                             WidthRequest="14" HeightRequest="14" Fill="#FF1E1E1E" Stroke="White"
                             HorizontalOptions="Start" VerticalOptions="Center"
                             behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                    <VerticalStackLayout x:Name="PART_OutputSlots" Grid.Row="1" Margin="10" Spacing="4"
                                         BindableLayout.ItemsSource="{Binding OutputSlots.Items}">
                        <BindableLayout.ItemTemplate>
                            <DataTemplate>
                                <Grid ColumnDefinitions="*,Auto">
                                    <Label Text="{Binding Name}" />
                                    <Ellipse Grid.Column="1" BindingContext="{Binding Slot}"
                                             WidthRequest="12" HeightRequest="12" Fill="#FF1E1E1E" Stroke="White"
                                             behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                                </Grid>
                            </DataTemplate>
                        </BindableLayout.ItemTemplate>
                    </VerticalStackLayout>
                </Grid>
            </Border>
        </DataTemplate>

        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}" />
        <MenuFlyout x:Key="LinkContextMenu">
            <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
        </MenuFlyout>
    </ContentView.Resources>

    <Grid>
        <Border x:Name="PART_SurfaceBorder" Stroke="#33FFFFFF" StrokeThickness="1"
                StrokeShape="RoundRectangle 3" BackgroundColor="#1E1E1E">
            <local:PlainGridDecorator x:Name="PART_GridDecorator">
                <behaviors:WorkflowLinkOverlay x:Name="PART_LinkLayer"
                                               WorkflowTree="{Binding BindingContext, Source={x:Reference Root}}"
                                               InteractionSource="{x:Reference Root}"
                                               ScrollOffsetX="{Binding ScrollOffsetX, Source={x:Reference PART_GridDecorator}}"
                                               ScrollOffsetY="{Binding ScrollOffsetY, Source={x:Reference PART_GridDecorator}}"
                                               ContentOffsetX="{Binding ContentOffsetX, Source={x:Reference PART_GridDecorator}}"
                                               ContentOffsetY="{Binding ContentOffsetY, Source={x:Reference PART_GridDecorator}}"
                                               RulerThickness="0" StrokeWidth="2" />
                <ScrollView x:Name="PART_ScrollViewer" Orientation="Both">
                    <AbsoluteLayout x:Name="PART_Canvas" BackgroundColor="Transparent"
                                    behaviors:ViewPool.ItemsSource="{Binding BindingContext.Helper.VisibleItems, Source={x:Reference Root}}"
                                    behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
                </ScrollView>
            </local:PlainGridDecorator>
        </Border>

        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                          HorizontalOptions="Fill" VerticalOptions="Fill"
                                          ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</ContentView>
```

装饰器是宿主写的 `Grid`，实现 Core 契约；适配器不自带。连线覆盖层读取它的偏移，表面每一轮写入这些偏移。

```csharp
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class PlainGridDecorator : Grid, IWorkflowGridDecorator
{
    public static readonly BindableProperty ScrollOffsetXProperty = BindableProperty.Create(nameof(ScrollOffsetX), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ScrollOffsetYProperty = BindableProperty.Create(nameof(ScrollOffsetY), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ContentOffsetXProperty = BindableProperty.Create(nameof(ContentOffsetX), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ContentOffsetYProperty = BindableProperty.Create(nameof(ContentOffsetY), typeof(double), typeof(PlainGridDecorator), 0d);

    public double ScrollOffsetX { get => (double)GetValue(ScrollOffsetXProperty); set => SetValue(ScrollOffsetXProperty, value); }
    public double ScrollOffsetY { get => (double)GetValue(ScrollOffsetYProperty); set => SetValue(ScrollOffsetYProperty, value); }
    public double ContentOffsetX { get => (double)GetValue(ContentOffsetXProperty); set => SetValue(ContentOffsetXProperty, value); }
    public double ContentOffsetY { get => (double)GetValue(ContentOffsetYProperty); set => SetValue(ContentOffsetYProperty, value); }
    public double RulerBand => 0d;
}
```

选择器只回答节点；池把连线交给共享覆盖层，工厂会跳过选择器抛异常的类型。

```csharp
using System;
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }

    protected override DataTemplate OnSelectTemplate(object item, BindableObject container)
        => item is INodeComponent
            ? NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set.")
            : throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}");
}
```

## 代码后置

```csharp
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class TreeView : ContentView
{
    private ITreeComponent? _tree;
    private IInputEvents? _events;

    public TreeView()
    {
        InitializeComponent();
        BindingContextChanged += (_, _) => BindTree(BindingContext as ITreeComponent);
    }

    private void BindTree(ITreeComponent? tree)
    {
        if (_events is not null)
        {
            _events.Input.KeyDown -= OnKeyDown;
            _events.Input.PointerWheelChanged -= OnWheel;
        }

        _events = null;
        _tree = tree;
        if (tree?.GetHelper() is not IInputEvents events) return;

        _events = events;
        events.Input.KeyDown += OnKeyDown;
        events.Input.PointerWheelChanged += OnWheel;
    }

    private void OnWheel(object? sender, PointerWheelEventArgs e)
    {
        if (_tree is not { } tree || !e.Modifiers.HasFlag(InputModifiers.Shift)) return;

        e.Handle.PreventDefault = true;
        WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
    }

    private void OnKeyDown(object? sender, KeyDownEventArgs e)
    {
        if (e.Handle.PreventDefault || _tree is not { } tree) return;

        if (e.Key == InputKey.Delete && e.Target is ILinkComponent link && link.DeleteCommand.CanExecute(null))
        {
            link.DeleteCommand.Execute(null);
            return;
        }

        if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;

        var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
        if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
        else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
        else return;

        e.Handle.PreventDefault = true;
    }
}
```

**预期结果：** 页面把 `TreeView.BindingContext` 设成树；表面在 `BindingContextChanged` 上订阅、池化节点视图，覆盖层绘制连线。

## 缩放节点

MAUI 没有 `Viewbox`，适配器也刻意不使用渲染变换：变换会改变插槽布局行为读到的坐标。demo 在代码里按 `k = 折叠宽度 / 260` 缩放节点标题行高、字体、插槽字形、边距与间距。

最小表面把 `WidthRequest`/`HeightRequest` 绑到折叠后的 `Size` 就足以看到图。加入自己的内容时，扩展节点视图的 `OnSizeAllocated`，**位置与尺寸都要缩放**；把某个 margin 留在设计值，就会把端口挤出折叠卡片，连线随之锚到错误的点。

完整 demo 的节点视图在 `Examples/Workflow/MAUI/Demo/Controls/Workflow/NodeView.xaml.cs`。
