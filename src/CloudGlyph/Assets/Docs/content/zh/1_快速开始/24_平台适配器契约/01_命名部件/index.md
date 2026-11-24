# 命名部件

一个工作流表面由**七个视图角色**拼成。其中六个由适配器提供；网格装饰器与小地图实现 Core 接口，由宿主编写或由模板生成。表面按名字找它们，所以 `PART_*` 是契约的一部分，不是 demo 的随手约定。

| 角色 | 适配器里的类 | 职责 |
|---|---|---|
| 画布宿主 | `WorkflowSurfaceBehavior` | 解析命名子控件、喂视口、起平移、挂缩放、转发指针/按键、打开连线菜单、注册 `WorkflowInput.Scroller` 与 `Navigator` |
| 画布变换 | `WorkflowCanvasTransformBehavior` | 一个值载体，节点与连线视图把 `RenderTransform` 绑到它上面 |
| 视图池 | `ViewPool` | 在可见项集合上做对象池化视图 |
| 节点拖拽 | `WorkflowNodeDragBehavior` | 把节点上的拖动变成 `MoveCommand` |
| 插槽连接 | `WorkflowSlotConnectionBehavior` | 按下一个端口、在另一个端口松开，连接两者 |
| 插槽布局 | `WorkflowSlotLayoutBehavior` | 测量每个端口并写回它的 `Anchor` |
| 网格装饰器 / 小地图 | `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | 网格、标尺与缩略图；XAML 适配器不自带装饰器 |

## 附着点

下面是 `WorkflowSurfaceBehavior` 的公共附着属性。WPF、Avalonia、WinUI 与 MAUI 四家使用同一组名字。

| 附着属性 | 含义 | 默认值 |
|---|---|---|
| `IsEnabled` | 总开关；只有为 `true` 时才读取其余属性 | `false` |
| `ScrollViewerName` | 定义被测视口的滚动容器 | `null` |
| `CanvasName` | 视图池填充的画布/面板 | `null` |
| `GridDecoratorName` | 实现 `IWorkflowGridDecorator` 的元素 | `null` |
| `MinimapOverlayName` | 实现 `IWorkflowMinimapOverlay` 的元素 | `null` |
| `PointerPressSourceName` | 空白处按下开始平移的元素 | `null` |
| `ZoomEnabled` | 启用 Ctrl+滚轮缩放 | `false` |
| `LinkMenuKey` | 连线右键菜单的资源键，在资源字典存在之后解析 | `null` |

支撑角色各自带附着点：`WorkflowCanvasTransformBehavior.Transform`、`ViewPool.ItemsSource` / `TemplateSelector`、`WorkflowNodeDragBehavior.IsEnabled` / `CoordinateHostName` / `CoordinateHostType`、`WorkflowSlotConnectionBehavior.IsEnabled`，以及 `WorkflowSlotLayoutBehavior.IsEnabled` / `SlotNames` / `SlotEnumeratorNames` / `CoordinateHostName` / `CoordinateHostType`。

## 表面骨架

下面是 WPF 的写法。其他 XAML 适配器只改命名空间声明，不改名字。

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder">
    <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
        <ScrollViewer x:Name="PART_ScrollViewer">
            <Canvas x:Name="PART_Canvas"
                    Width="{Binding Layout.ActualSize.Width}"
                    Height="{Binding Layout.ActualSize.Height}"
                    Background="Transparent" />
        </ScrollViewer>
    </Border>
</UserControl>
```

**预期结果：** 表面解析出四个名字。缺少某个名字只会让对应部分静默失效 —— 不抛异常、不写日志，所以「表面什么都不做」通常是名字拼错了。

## 表面用代码搭建时

XAML 名字活在 `UserControl` 的 `NameScope` 里，不在可视树上。代码搭建的表面必须显式注册名字，再让表面解析：

```csharp
var scope = new NameScope();
NameScope.SetNameScope(host, scope);
scope.RegisterName("PART_ScrollViewer", scrollViewer);
scope.RegisterName("PART_Canvas", canvas);
scope.RegisterName("PART_SurfaceBorder", border);

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetPointerPressSourceName(host, "PART_SurfaceBorder");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

`Refresh(UserControl)` 是 WPF 与 WinUI 的公共入口；其他适配器靠各自的生命周期事件重新解析。换模板或换宿主之后要调用它。

**预期结果：** `WorkflowSurfaceBehavior.Refresh(host)` 返回时命名部件已绑定；滚动 `ScrollViewer` 会把位置写进 `tree.GetHelper().Viewport`。

## 树是表面的数据上下文

四家适配器都从宿主的数据上下文读树 —— WPF/Avalonia/WinUI 是 `DataContext`，MAUI 是 `BindingContext`。把它设成一个 `ITreeComponent`，表面会订阅变化并重新绑定。

**预期结果：** 赋入一棵树之后，表面在下一轮布局发布视口，并填充 `tree.GetHelper().VisibleItems`。
