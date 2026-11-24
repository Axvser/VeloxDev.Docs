# 手势与连线边界

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

Jalium 的手势行为是以附着属性形式挂在实例 `DependencyObject` 类型上的。共享 Core 流水线仍负责顺序、去重与重测调度；这些类负责可视树遍历、坐标与 UI 线程交接。

## 类：WorkflowNodeDragBehavior

`public sealed class WorkflowNodeDragBehavior : DependencyObject`

把标记元素上的按下转成 `INodeComponent.MoveCommand`。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`、`SetCoordinateHostName` |
| `CoordinateHostTypeProperty` | `Type?` | `null` | `GetCoordinateHostType`、`SetCoordinateHostType` |

所有访问器接收 `DependencyObject`，不抛异常。坐标宿主先按名字解析，再按类型（默认 `Canvas`）沿可视树向上找。

### 示例

```xml
<Border x:Name="PART_TitleRow"
        behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
        behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />
```

挂在卡片的标题栏而不是整张卡片上，拖端口才不会同时拖节点。

## 类：WorkflowSlotConnectionBehavior

`public sealed class WorkflowSlotConnectionBehavior : DependencyObject`

拥有完整连线手势，包括失败收尾。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |

### 备注

- 左键按下执行 `SendConnectionCommand`；对应的左键松开完成或重置手势。
- 插槽从元素的 `DataContext` 读取，所以复用的插槽视图总是接到它当前显示的插槽。
- 松开没有落在愿意接收的插槽上时都会重置虚拟连线。松回发送口是最常见的情形，不能留下悬着的橡皮筋。

## 类：WorkflowSlotLayoutBehavior

`public sealed class WorkflowSlotLayoutBehavior : DependencyObject`

测量节点卡片的插槽控件，并把每个中心写回插槽的 `Anchor`。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `SlotNamesProperty` | `string?` | `null` | `GetSlotNames`、`SetSlotNames` |
| `SlotEnumeratorNamesProperty` | `string?` | `null` | `GetSlotEnumeratorNames`、`SetSlotEnumeratorNames` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`、`SetCoordinateHostName` |
| `CoordinateHostTypeProperty` | `Type?` | `null` | `GetCoordinateHostType`、`SetCoordinateHostType` |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Refresh(FrameworkElement control)` | `void` | 为只改变换/缩放的情况调度重测。 |
| `SyncNow(FrameworkElement control)` | `void` | 立即测量，供已经跑过排版的调用方使用。 |

未声明异常。

### 备注

- 定位器报告 `SlotCoordinateSpace.ScrollSpace`；流水线减去 `CanvasLayout.ActualOffset`。坐标宿主选错是静默的整体偏移 bug，每个端口和连线端点会一起移。
- 复用模式的 `ItemsControl` 惰性提供容器；枚举器分支通过 `ItemContainerGenerator.ContainerFromIndex` 取容器，再向下找到带插槽的元素。

## 类：WorkflowLinkBounds

`public static class WorkflowLinkBounds`

放大并移动自绘元素的布局盒，让它覆盖自己画出的全部内容。

### 成员

| 签名 / 成员 | 类型 | 说明 |
| --- | --- | --- |
| `BoxPad` | `double`（const `6`） | 盒子超出绘制范围多少画布单位。 |
| `Apply(FrameworkElement view, IReadOnlyList<Point> canvasLocalPoints, out double originX, out double originY)` | `bool` | 把盒子挪到点集包围盒上；无内容可覆盖时返回 `false`。 |

`originX`/`originY` 接收盒子的左/上边。绘制时从同一组画布局部点里减掉它们。盒子不是命中目标；命中用视图发给 Core 的曲线。

### 示例

```csharp
if (WorkflowLinkBounds.Apply(this, points, out var ox, out var oy))
{
    DrawCurve(graphics, points, ox, oy);
}
// Source: source
```

### 备注

- Jalium 渲染器在布局盒错过裁剪区时直接剔掉子元素，从不检查绘制内容。画到盒外的曲线会被静默丢弃；症状是深缩放时连线消失。
- 因为盒子会移动，绘制坐标必须以它为原点表达。
