# 验证

这个功能的可运行参考是 WPF Trimmed 示例。它的 `TreeView` 就是整个表面契约；`MainView` 创建四个节点，让平移与缩放有东西可动。

## 运行

```powershell
dotnet run --project "Examples/Workflow/WPF Trimmed/Demo/Demo.csproj"
```

## 逐项检查

1. **平移。** 在空白画布上按住左键拖动。四张卡一起移动，滚动条跟着走。
2. **缩放。** 按住 `Ctrl` 转动滚轮。卡片围绕视口中心下方的点放大或缩小。缩放夹在 `0.1` 到 `10` 之间。
3. **普通滚轮。** 松开 `Ctrl` 转动滚轮。表面按 WPF 默认行设置每格 48 px 纵向滚动。
4. **键盘。** 新建或删除节点后按 `Ctrl+Z`，结构改动被撤销。拖动节点后按 `Ctrl+Z`：拖动不会被撤销，因为 `Move` 不入历史栈。
5. **接管滚轮。** 加上[路由输入](../02_路由输入/index.md)里的 `Shift` 分支；`Shift` + 滚轮改为横向滚动。
6. **定位。** 从按钮或列表调用 `node.Locate()`；节点居中，缩放不变。

WPF 无头测试套件在没有窗口的情况下断言同一批表面行为：命名部件解析、画布变换写入、视口写回持久化、虚拟化排除屏外节点、任意缩放下 `Locate` 有效、滚轮在兄弟控件上不滚画布（`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/WorkflowSurfaceHeadlessTests.cs`）。

## 完整代码

完整工程是 `Examples/Workflow/WPF Trimmed/Demo`。下面两个文件是这个功能给工作流宿主加的全部内容。`NodeView`、`SlotView`、`LinkView`、`WorkflowGridDecorator`、`MinimapOverlay` 是同目录的示例视图类；它们提供外观，不提供输入接线。

### `Views/Workflow/TreeView.xaml`

```xml
<UserControl x:Class="Demo.Views.TreeView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo.Views"
             xmlns:workflowViews="clr-namespace:Demo.Views.Workflow"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
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
            <workflowViews:NodeView Width="{Binding Size.Width}"
                                    Height="{Binding Size.Height}"
                                    Canvas.Left="{Binding Anchor.Horizontal}"
                                    Canvas.Top="{Binding Anchor.Vertical}"
                                    Panel.ZIndex="{Binding Anchor.Layer}"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <DataTemplate x:Key="LinkTemplate">
            <workflowViews:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                                    StartTop="{Binding Sender.Anchor.Vertical}"
                                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                                    EndTop="{Binding Receiver.Anchor.Vertical}"
                                    CanRender="{Binding IsVisible}"
                                    LineColor="#DDFFFFFF"
                                    Width="{Binding ElementName=PART_Canvas, Path=ActualWidth}"
                                    Height="{Binding ElementName=PART_Canvas, Path=ActualHeight}"
                                    Panel.ZIndex="-1"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <workflowViews:CustomTemplateSelector x:Key="WorkflowTemplateSelector"
                                              NodeTemplate="{StaticResource NodeTemplate}"
                                              LinkTemplate="{StaticResource LinkTemplate}" />
        <ContextMenu x:Key="LinkContextMenu">
            <MenuItem Header="Delete" Command="{Binding DeleteCommand}" />
        </ContextMenu>
    </UserControl.Resources>

    <Grid>
        <Border x:Name="PART_SurfaceBorder" BorderBrush="#33FFFFFF" BorderThickness="1" Background="#1E1E1E">
            <workflowViews:WorkflowGridDecorator x:Name="PART_GridDecorator">
                <ScrollViewer x:Name="PART_ScrollViewer"
                              HorizontalScrollBarVisibility="Auto"
                              VerticalScrollBarVisibility="Auto"
                              PanningMode="Both">
                    <Canvas x:Name="PART_Canvas"
                            Width="{Binding Layout.ActualSize.Width}"
                            Height="{Binding Layout.ActualSize.Height}"
                            Background="Transparent"
                            behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                            behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}">
                        <Canvas.RenderTransform>
                            <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                                Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                        </Canvas.RenderTransform>
                    </Canvas>
                </ScrollViewer>
            </workflowViews:WorkflowGridDecorator>
        </Border>
        <workflowViews:MinimapOverlay x:Name="PART_MinimapOverlay"
                                      HorizontalAlignment="Stretch"
                                      VerticalAlignment="Stretch"
                                      ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

### `Views/Workflow/TreeView.xaml.cs`

```csharp
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace Demo.Views;

public partial class TreeView : UserControl
{
    private ITreeComponent? _tree;
    private IInputEvents? _events;

    public TreeView()
    {
        InitializeComponent();
        DataContextChanged += OnDataContextChanged;
    }

    private void OnDataContextChanged(object sender, DependencyPropertyChangedEventArgs e)
    {
        Unwire();

        if (DataContext is not ITreeComponent tree) return;
        if (tree.GetHelper() is not IInputEvents events) return;

        _tree = tree;
        _events = events;
        events.Input.KeyDown += OnKeyDown;
        events.Input.PointerWheelChanged += OnWheel;
    }

    private void Unwire()
    {
        if (_events is not null)
        {
            _events.Input.KeyDown -= OnKeyDown;
            _events.Input.PointerWheelChanged -= OnWheel;
            _events = null;
        }

        _tree = null;
    }

    private void OnKeyDown(object? sender, KeyDownEventArgs e)
    {
        if (!e.Modifiers.HasFlag(InputModifiers.Control) || _tree is not { } tree) return;

        var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
        if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
        else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
        else return;

        e.Handle.PreventDefault = true;
    }

    private void OnWheel(object? sender, PointerWheelEventArgs e)
    {
        if (!e.Modifiers.HasFlag(InputModifiers.Shift) || _tree is not { } tree) return;

        e.Handle.PreventDefault = true;
        WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
    }

    // Navigation: model data is enough; the node does not need a view.
    public void LocateFirstNode()
    {
        if (_tree is { Nodes.Count: > 0 } tree) tree.Nodes[0].Locate();
    }
}
```

## 运行声明

⚠️ 未实际运行——仅静态核对。上面两个文件与示例的 `TreeView.xaml`、`TreeView.xaml.cs` 一致，只额外加了 `LocateFirstNode` 辅助方法；「逐项检查」里列出的行为是示例与 WPF 无头套件所断言的内容。撰写本页时没有启动窗口。
