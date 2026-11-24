# 事件与小地图

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 类：WorkflowEvents

`public static class WorkflowEvents`

附着事件接收器。值是 `INodeEventSink`、`ISlotEventSink` 或 `ITreeEventSink`；转发由共享的 `WorkflowEventRelay` 完成。

### 附着属性

| 属性字段 | CLR 类型 | 访问器 |
| --- | --- | --- |
| `NodeProperty` | `INodeEventSink?` | `GetNode`、`SetNode` |
| `SlotProperty` | `ISlotEventSink?` | `GetSlot`、`SetSlot` |
| `TreeProperty` | `ITreeEventSink?` | `GetTree`、`SetTree` |

所有访问器接收 `DependencyObject`，不抛异常。

### 示例

```xml
<local:NodeView behaviors:WorkflowEvents.Node="{Binding NodeEvents}" />
```

### 备注

- 订阅跟随 `DataContext`。复用的视图交给另一个节点时，旧订阅被摘掉，接上新的。
- `Unloaded` 会断开三条线，元素不会把组件钉住。

## 类：WorkflowMinimapOverlay

`public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay`

自包含小地图。它把所有节点卡片的包围盒映射进小地图，画一个夹在小地图内的半透明视口矩形，并复用表面的边缘感知导航做拖拽平移。树订阅、映射、放置与拖拽数学在 Core 的 `MinimapPipeline`。

### 属性

| 属性字段 / 属性 | CLR 类型 | 默认值 |
| --- | --- | --- |
| `ScrollOffsetX` | `double` | `0` |
| `ScrollOffsetY` | `double` | `0` |
| `ContentOffsetX` | `double` | `0` |
| `ContentOffsetY` | `double` | `0` |
| `ViewportWidth` | `double` | `0` |
| `ViewportHeight` | `double` | `0` |
| `IsMinimapVisible` | `bool` | `true` |
| `MinimapMargin` | `double` | `12` |
| `AvailableRight` | `double` | `0` |
| `AvailableTop` | `double` | `0` |
| `AvailableBottom` | `double` | `0` |
| `WorkflowTree` | `ITreeComponent?` | `null` |
| `MinimapWidth` | `double` | `200` |
| `MinimapHeight` | `double` | `140` |
| `MinimapMinSize` | `double` | `1` |
| `ContentPadding` | `double` | `8` |
| `MinimapBackground` | `Brush` | 半透明深色填充 |
| `MinimapBorderBrush` | `Brush` | `#DC94A3B8` |
| `MinimapBorderThickness` | `double` | `1` |
| `MinimapCornerRadius` | `double` | `4` |
| `NodeBrush` | `Brush` | `#DC38BDF8` |
| `NodeCornerRadius` | `double` | `2` |
| `ViewportFill` | `Brush` | `#30FFFFFF` |
| `ViewportStroke` | `Brush` | `#F0FFFFFF` |
| `ViewportStrokeThickness` | `double` | `1` |
| `ScrollViewerName` | `string?` | `null` |
| `ScrollViewer` | `ScrollViewer?` | `null` |
| `RulerBand` | `double`（get） | 恒为 `0` |

大多数属性都有对应的 `...Property` 字段。`ScrollViewer` 是普通 CLR 属性，由组合控件为拖拽平移赋值；`ScrollViewerName` 在模板名称作用域里命名查看器。

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `NavigateToCanvasLocal(double wx, double wy)` | `void` | 把表面居中到画布局部点。 |

### 扩展点

`protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context)` 绘制默认节点与视口块。重写并调用 `base` 可在其上追加。

### 备注

- 只有小地图矩形可命中；覆盖层其余部分让指针输入穿过。
- 拖过边缘会增长 `CanvasLayout.PositiveOffset` / `NegativeOffset`，与表面导航一致。
