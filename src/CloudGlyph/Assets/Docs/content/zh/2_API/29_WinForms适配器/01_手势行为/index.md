# 手势行为

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

这三个附着行为承担节点拖动、插槽连线与槽测量的平台半边。Core 中的共享流水线负责顺序、去重与重测调度。

## 类：WorkflowNodeDragBehavior

`public sealed class WorkflowNodeDragBehavior`

把标记元素上的按下转成 `INodeComponent.MoveCommand`，约按 60 Hz 合并位移。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`、`SetCoordinateHostName` |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | 读取拖动开关。 |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | 写入拖动开关。 |
| `GetCoordinateHostName(VisualElement element)` | `string?` | 读取坐标宿主名。 |
| `SetCoordinateHostName(VisualElement element, string? value)` | `void` | 写入坐标宿主名。 |
| `Ensure(VisualElement element)` | `void` | 启用时订阅，否则退订。 |

位移在坐标宿主的局部空间测量 —— 命名元素，或最近的视觉画布。节点通过向上遍历视觉祖先的 `INodeComponent` 数据上下文找到。若 `WorkflowSurfaceBehavior.GetPressHandle(...).PreventDefault` 否决了这次按下，则不开始拖动。

### 示例

```xml
<Border x:Name="PART_TitleRow"
        behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
        behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas" />
```

## 类：WorkflowSlotConnectionBehavior

`public sealed class WorkflowSlotConnectionBehavior`

左键按下开始一次连线，松开完成它。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | 读取连线开关。 |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | 写入连线开关。 |
| `Ensure(VisualElement element)` | `void` | 启用时订阅，否则退订。 |

按下执行 `ISlotComponent.SendConnectionCommand`。松开时解析指针下的插槽并执行它的 `ReceiveConnectionCommand`；松回发送口不会连上。连线是否合法由模型判断。

### 示例

```xml
<local:SlotView behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

## 类：WorkflowSlotLayoutBehavior

`public sealed class WorkflowSlotLayoutBehavior`

测量声明的槽部件，并把它们的世界锚点写回模型。

### 附着属性

| 属性字段 | CLR 类型 | 默认值 | 访问器 |
| --- | --- | --- | --- |
| `IsEnabledProperty` | `bool` | `false` | `GetIsEnabled`、`SetIsEnabled` |
| `SlotNamesProperty` | `string?` | `null` | `GetSlotNames`、`SetSlotNames` |
| `SlotEnumeratorNamesProperty` | `string?` | `null` | `GetSlotEnumeratorNames`、`SetSlotEnumeratorNames` |
| `CoordinateHostNameProperty` | `string?` | `null` | `GetCoordinateHostName`、`SetCoordinateHostName` |

`SlotNames` 与 `SlotEnumeratorNames` 是逗号分隔的 `x:Name` 列表。枚举器必须是可视化项控件，且已实现的项是槽。

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `GetIsEnabled(VisualElement element)` | `bool` | 读取布局开关。 |
| `SetIsEnabled(VisualElement element, bool value)` | `void` | 写入布局开关。 |
| `GetSlotNames(VisualElement element)` | `string?` | 读取命名槽部件。 |
| `SetSlotNames(VisualElement element, string? value)` | `void` | 写入命名槽部件。 |
| `GetSlotEnumeratorNames(VisualElement element)` | `string?` | 读取命名枚举器部件。 |
| `SetSlotEnumeratorNames(VisualElement element, string? value)` | `void` | 写入命名枚举器部件。 |
| `GetCoordinateHostName(VisualElement element)` | `string?` | 读取坐标宿主名。 |
| `SetCoordinateHostName(VisualElement element, string? value)` | `void` | 写入坐标宿主名。 |
| `Ensure(VisualElement element)` | `void` | 启用时附着，否则分离。 |

每次表面排版后测量。定位器报告 `SlotCoordinateSpace.CanvasLocal`，因为 `PointFromSurface` 已经反转了相机。流水线抑制亚像素变化，并保留槽的层号。

### 示例

```xml
<local:NodeView behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                 behaviors:WorkflowSlotLayoutBehavior.SlotNames="InputSlot"
                 behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="OutputSlots"
                 behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas" />
```

### 备注

- 重命名 `PART_*` 或槽名时必须在同一次改动里改这里；没有任何东西会枚举 `node.Slots`。
- `Ensure` 是幂等的，表面在池刷新时会对每个视觉元素调用它。
