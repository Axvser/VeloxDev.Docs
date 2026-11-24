# 表面与视图池

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 类：WorkflowSurfaceBehavior

`public static class WorkflowSurfaceBehavior`

Jalium 表面的附着配置。它托管命名部件，不是可派生的控件。树来自宿主的 `DataContext`。

### 常量

| 成员 | 类型 | 值 |
| --- | --- | --- |
| `TemplateSelectorKey` | `string` | `"WorkflowTemplateSelector"` |
| `CanvasWidth` | `double` | `2000` |
| `CanvasHeight` | `double` | `2000` |

`CanvasWidth` 与 `CanvasHeight` 是下限，近似空树也有可平移的表面。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `ScrollViewerNameProperty` | `string?` | `null` | `GetScrollViewerName`、`SetScrollViewerName` |
| `CanvasNameProperty` | `string?` | `null` | `GetCanvasName`、`SetCanvasName` |
| `GridDecoratorNameProperty` | `string?` | `null` | `GetGridDecoratorName`、`SetGridDecoratorName` |
| `PointerPressSourceNameProperty` | `string?` | `null` | `GetPointerPressSourceName`、`SetPointerPressSourceName` |
| `MinimapOverlayNameProperty` | `string?` | `null` | `GetMinimapOverlayName`、`SetMinimapOverlayName` |
| `ZoomEnabledProperty` | `bool` | `false` | `GetZoomEnabled`、`SetZoomEnabled` |
| `CanvasTransformProperty` | `Transform?` | `null` | `GetCanvasTransform`、`SetCanvasTransform` |
| `LinkMenuKeyProperty` | `string?` | `null` | `GetLinkMenuKey`、`SetLinkMenuKey` |

所有访问器接收 `DependencyObject`，都不抛异常。

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Refresh(FrameworkElement host)` | `void` | 重新解析命名部件、画布尺寸、布局、视口恢复与覆盖层。 |
| `NavigateToCanvasLocal(FrameworkElement host, double localX, double localY)` | `void` | 把视图居中到画布局部点，到边缘时扩画布。 |
| `NotifyZoomCommitted(FrameworkElement host)` | `void` | 用查看器当前偏移重跑虚拟化。 |
| `NotifyZoomCommitted(FrameworkElement host, double horizontalOffset, double verticalOffset)` | `void` | 按已提交的滚动目标重跑虚拟化。用 `double.NaN` 读查看器值。 |
| `TreeOf(DependencyObject element)` | `ITreeComponent?` | 返回绑定到表面宿主的树。 |

未声明异常。

### 示例

```xml
<UserControl xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.Jalium"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu" />
```

### 备注

- 保留树上的普通 `CanvasTransform` 镜像。没有它，平移后所有卡片都停在世界原点，且不报错。
- `NotifyZoomCommitted` 会装一个短时缩放钉，防止提交前的陈旧 `ScrollChanged` 覆盖目标视口，然后内联重测槽锚点。
- 整个网格渲染器归模板所有：`GridDecorator` 实现 `IWorkflowGridDecorator`；适配器不提供网格类。

## 类：ViewPool

`public static class ViewPool`

架在 Jalium `Panel` 上的附着视图池。Core 流水线是 `ViewSourcePipeline`。

### 属性

| 成员 | 类型 | 访问器 |
| --- | --- | --- |
| `ItemsSourceProperty` | `DependencyProperty`（`INotifyCollectionChanged`） | `GetItemsSource` / `SetItemsSource` |
| `TemplateSelectorProperty` | `DependencyProperty`（`DataTemplateSelector`） | `GetTemplateSelector` / `SetTemplateSelector` |

所有访问器接收 `Panel`。任一属性变化都会释放正在运行的系统并重建；没有增量换模板路径。

### 示例

```xml
<Canvas x:Name="PART_Canvas" Background="Transparent"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

### 备注

- 面板的 `Unloaded` 事件会释放系统，移除的表面不会把树钉住。
- 源为 `null` 时释放系统，直到再次设置源才物化。
