# 表面与视图池

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 类：WorkflowSurfaceBehavior

`public sealed class WorkflowSurfaceBehavior`

Easel 表面的静态附着配置。宿主必须是 `VisualHost`；启用该行为会接上相机、解析命名部件、绑定树并启动输入路由。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `ZoomEnabledProperty` | `bool` | `false` | `GetZoomEnabled`、`SetZoomEnabled` |
| `ScrollViewerNameProperty` | `string?` | `null` | `GetScrollViewerName`、`SetScrollViewerName` |
| `CanvasNameProperty` | `string?` | `null` | `GetCanvasName`、`SetCanvasName` |
| `GridDecoratorNameProperty` | `string?` | `null` | `GetGridDecoratorName`、`SetGridDecoratorName` |
| `MinimapOverlayNameProperty` | `string?` | `null` | `GetMinimapOverlayName`、`SetMinimapOverlayName` |
| `SurfaceNameProperty` | `string?` | `null` | `GetSurfaceName`、`SetSurfaceName` |
| `PointerPressSourceNameProperty` | `string?` | `null` | `GetPointerPressSourceName`、`SetPointerPressSourceName` |
| `VisualTemplateSelectorProperty` | `VisualTemplateSelector?` | `null` | `GetVisualTemplateSelector`、`SetVisualTemplateSelector` |
| `VisualTemplateSelectorKeyProperty` | `string?` | `"WorkflowTemplateSelector"` | `GetVisualTemplateSelectorKey`、`SetVisualTemplateSelectorKey` |
| `VisualLinkColorProperty` | `System.Drawing.Color` | `#DDFFFFFF` | `GetVisualLinkColor`、`SetVisualLinkColor` |
| `VisualLinkThicknessProperty` | `float` | `2` | `GetVisualLinkThickness`、`SetVisualLinkThickness` |
| `VisualLinkHoverColorProperty` | `System.Drawing.Color` | `White` | `GetVisualLinkHoverColor`、`SetVisualLinkHoverColor` |
| `VisualLinkHoverThicknessProperty` | `float` | `3.5` | `GetVisualLinkHoverThickness`、`SetVisualLinkHoverThickness` |
| `VisualLinkVirtualColorProperty` | `System.Drawing.Color` | `#DDFFFFFF` | `GetVisualLinkVirtualColor`、`SetVisualLinkVirtualColor` |
| `VisualLinkGlowProperty` | `bool` | `false` | `GetVisualLinkGlow`、`SetVisualLinkGlow` |
| `WorkflowTreeProperty` | `ITreeComponent?` | `null` | `GetWorkflowTree`、`SetWorkflowTree` |
| `LinkMenuBuilderProperty` | `Action<ContextMenuStrip, ILinkComponent>?` | `null` | `GetLinkMenuBuilder`、`SetLinkMenuBuilder` |
| `LinkMenuKeyProperty` | `string?` | `null` | `GetLinkMenuKey`、`SetLinkMenuKey` |

每个 `Get`/`Set` 都接收 `System.Windows.Forms.Control`，控件为 `null` 时抛 `ArgumentNullException`。

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Refresh(Control host)` | `void` | 重新读取部件、树、选择器与相机，并重新确保附着行为。 |
| `GetZoom(Control host)` | `double` | 当前相机缩放；`1` 表示世界单位等于表面单位。 |
| `GetPan(Control host)` | `PointF` | 缩放之后施加的带符号平移。 |
| `SetPan(Control host, PointF pan)` | `void` | 设置平移并重新应用相机。 |
| `SurfaceToWorld(Control host, PointF surfacePoint)` | `PointF` | 表面坐标转世界坐标。 |
| `WorldToSurface(Control host, PointF worldPoint)` | `PointF` | 世界坐标转表面坐标。 |
| `GetWorldViewport(Control host)` | `Offset` | 可见区域左上角的世界坐标。 |
| `SetWorldViewport(Control host, Offset worldOffset)` | `void` | 把相机移到让可见区域从 `worldOffset` 开始。 |
| `ZoomAt(Control host, PointF surfacePoint, double factor)` | `void` | 围绕表面点缩放，范围夹在 `0.1`–`10`，该世界点保持不动。 |
| `ProcessWheel(Control host, PointF surfacePoint, int delta, Keys modifiers)` | `bool` | 路由一次滚轮；未绑定树时返回 `false`。 |

未声明其他异常。`ProcessWheel` 接收原始滚轮增量（一格 = 120）。设置 `ZoomEnabled` 时 Ctrl+滚轮缩放；否则滚轮交给 `WorkflowInput.Scroller`。

### 示例

```csharp
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
WorkflowSurfaceBehavior.SetWorkflowTree(host, tree);
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
// Source: Demo
```

### 备注

- 在被验证的目标上，树不通过 `DataContext` 到达；用 `SetWorkflowTree` 显式绑定。`net8.0-windows` 及更高目标仍会读取 `DataContext`，更老的目标框架读取 `Tag`。
- 设置 `SurfaceName` 后，部件查找被限制在子树内，适用于视觉根还带工作台外壳的宿主。
- `PointerPressSourceName` 为 WPF 对齐而存在。输入由视觉宿主路由，不使用命名按下源。

## 类：ViewPool

`public sealed class ViewPool`

架在 `INotifyCollectionChanged` 源上的附着视图池。池的记账在 Core；`ViewSourcePipeline` 闭合 Easel 层。

### 属性与事件

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ItemsSourceProperty` | `DependencyProperty` | 附着源；通常是 `Helper.VisibleItems`。 |
| `TemplateSelectorProperty` | `DependencyProperty` | 附着的 `VisualTemplateSelector`。 |
| `Changed` | `event EventHandler<ViewPoolChangedEventArgs>?` | 某个宿主完成一批物化后触发一次。 |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `GetItemsSource(VisualElement element)` | `INotifyCollectionChanged?` | 读取附着源。 |
| `SetItemsSource(VisualElement element, INotifyCollectionChanged? value)` | `void` | 设置源。`null` 释放正在运行的系统；替换则就地重建。 |
| `GetTemplateSelector(VisualElement element)` | `VisualTemplateSelector?` | 读取附着选择器。 |
| `SetTemplateSelector(VisualElement element, VisualTemplateSelector? value)` | `void` | 设置选择器并重建正在运行的系统。 |
| `GetActiveViewCount(VisualElement host)` | `int` | 已绑定视图的项数。 |
| `GetPendingCount(VisualElement host)` | `int` | 等待调度批次的项数。 |
| `Refresh(VisualElement host)` | `void` | 释放前一个系统并物化当前源。 |

`Refresh` 在宿主为 `null` 时抛 `ArgumentNullException`。附着 setter 不抛异常；非面板元素只存储值。

### 示例

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

## 类：ViewPoolChangedEventArgs

`public sealed class ViewPoolChangedEventArgs(VisualElement host) : EventArgs`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Host` | `VisualElement` | 池化视图发生变化的画布。 |

## 类：WorkflowEvents

`public sealed class WorkflowEvents`

附着事件接收器。值是 `INodeEventSink`、`ISlotEventSink` 或 `ITreeEventSink`；转发由共享的 `WorkflowEventRelay` 完成。

| 成员 | 类型 | 访问器 |
| --- | --- | --- |
| `NodeProperty` | `DependencyProperty`（`INodeEventSink`） | `GetNode` / `SetNode` |
| `SlotProperty` | `DependencyProperty`（`ISlotEventSink`） | `GetSlot` / `SetSlot` |
| `TreeProperty` | `DependencyProperty`（`ITreeEventSink`） | `GetTree` / `SetTree` |

`Get*`/`Set*` 接收 `VisualElement`。`Ensure(VisualElement element)` 接上中继，并把当前接收器接到当前数据上下文。

### 示例

```xml
<local:NodeView behaviors:WorkflowEvents.Node="{Binding NodeEvents}" />
```

### 备注

- 订阅跟随 `DataContext`，所以复用的池化视图会退订旧组件、接上新组件。
- 元素的接收器与数据上下文都没变时，`Ensure` 不会重订。
