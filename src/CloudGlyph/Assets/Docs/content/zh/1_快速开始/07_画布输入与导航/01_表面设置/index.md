# 表面设置

WPF 表面行为挂在一个 `UserControl` 上，并按名字解析它要驱动的部件。它不会按类型遍历可视树去找：下面的名字就是标记与适配器之间的契约。

## 标记契约

```xml
<UserControl x:Class="Demo.TreeView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">

    <Border x:Name="PART_SurfaceBorder" BorderBrush="#33FFFFFF" BorderThickness="1">
        <local:WorkflowGridDecorator x:Name="PART_GridDecorator">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent">
                    <Canvas.RenderTransform>
                        <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                            Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                    </Canvas.RenderTransform>
                </Canvas>
            </ScrollViewer>
        </local:WorkflowGridDecorator>
    </Border>

    <local:MinimapOverlay x:Name="PART_MinimapOverlay"
                          HorizontalAlignment="Stretch"
                          VerticalAlignment="Stretch"
                          ScrollViewerName="PART_ScrollViewer" />
</UserControl>
```

除了平移与缩放必需的滚动容器和画布，每个命名部件都是可选的。`GridDecoratorName` 与 `MinimapOverlayName` 是后续功能挂接的钩子；不用那些能力就不写。

## 名字的含义

| 附着属性 | 命名元素必须是 | 适配器拿它做什么 |
|---|---|---|
| `ScrollViewerName` | `ScrollViewer` | 读写滚动偏移、测量视口、越界时撑大 extent。 |
| `CanvasName` | `Canvas` | 指针位置的参考系、渲染变换的目标。 |
| `GridDecoratorName` | 一个 `IWorkflowGridDecorator` | 推入滚动/内容偏移与标尺带 inset。 |
| `PointerPressSourceName` | 接收按下的元素 | 按下从这里路由，空白画布平移才起得来。 |
| `MinimapOverlayName` | 一个 `IWorkflowMinimapOverlay` | 推入树、偏移、视口尺寸与可用角落。 |
| `ZoomEnabled` | `bool`（默认 `false`） | 打开 Ctrl+滚轮缩放手势。 |
| `LinkMenuKey` | 一个 `ContextMenu` 资源键 | 右键按在连线上时打开该菜单，并在菜单开着期间挂起路由。 |

行为会自己把宿主的 `Focusable` 设为 `true`。这样悬停的连线才能把键盘焦点交给表面，`Delete` 与 `Ctrl+Z` 才到得了树的路由。

## 模板绑定渲染变换

节点或连线视图必须把 `RenderTransform` 绑到行为写出的变换上。这个变换以附着属性的形式发布，不直接应用到宿主。

```xml
<DataTemplate x:Key="NodeTemplate">
    <local:NodeView Width="{Binding Size.Width}"
                    Height="{Binding Size.Height}"
                    Canvas.Left="{Binding Anchor.Horizontal}"
                    Canvas.Top="{Binding Anchor.Vertical}"
                    Panel.ZIndex="{Binding Anchor.Layer}"
                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
</DataTemplate>
```

如果不绑这个变换，节点会停在它的世界坐标上，不跟随平移与缩放——表面仍然在滚，但没有任何东西跟着它动。

## 逐视图手势也是挂上去的

节点拖动与连线拖动不在宿主上，而是挂到应该发起它们的视图上。

```xml
<!-- 节点卡的可拖动部分 -->
<Grid behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />

<!-- 端口视图 -->
<UserControl behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

`WorkflowNodeDragBehavior.CoordinateHostName` 是拖动增量所参照的画布。不写时行为会退回最近的祖先 `Canvas`。

## 部件稍后才出现

`WorkflowSurfaceBehavior.Refresh(host)` 会重新解析命名部件并重新应用布局。替换表面内容、或换树但没有重建控件之后调用它；示例在自动布局之后也会调用。

## 预期结果

- 控件加载时命名部件都能解析，`PART_ScrollViewer` 与 `PART_Canvas` 没有绑定错误。
- 拖动节点时节点移动；拖动空白画布时画面平移。
- `Ctrl` + 滚轮改变 `Layout.Scale`，绑定它的状态文本随之变化。
- 不按 `Ctrl` 转动滚轮时画面纵向滚动。

## 下一页

[路由输入](../02_路由输入/index.md)说明如何订阅这个表面转发出来的事件。
