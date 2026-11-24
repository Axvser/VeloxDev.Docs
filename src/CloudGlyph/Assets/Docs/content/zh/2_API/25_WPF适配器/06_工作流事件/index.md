# 工作流事件

`WorkflowEvents` 通过三个附着属性把模型事件接收器装到元素上。它是 Core 接收器契约的 WPF 写法；接口定义位于平台适配器契约，而不在此程序集。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WPF`。

## WorkflowEvents

**签名：** `static class WorkflowEvents`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `Node` | `INodeEventSink?` | `null` | 接收所绑定节点的移动、缩放与删除事件。 |
| `Slot` | `ISlotEventSink?` | `null` | 接收所绑定插槽的通道事件。 |
| `Tree` | `ITreeEventSink?` | `null` | 接收所绑定树的连接事件。 |

访问器：`GetNode` / `SetNode`、`GetSlot` / `SetSlot`、`GetTree` / `SetTree`，均接收 `DependencyObject` 并返回或接收对应接收器接口。

该行为观察元素的 `DataContext`：当它成为 `INodeComponent`、`ISlotComponent` 或 `ITreeComponent` 时，对应 Helper 的事件被转发给接收器。接收器方法收到与 Helper 相同的参数对象（含 `WorkflowEventHandle`），因此 `On…ing` 方法可拒绝一次动作。

```xml
<Grid behaviors:WorkflowEvents.Node="{Binding NodeSink}"
      behaviors:WorkflowEvents.Slot="{Binding SlotSink}"
      behaviors:WorkflowEvents.Tree="{Binding TreeSink}" />
```

**预期结果：** 命名了 `Node` 接收器的节点视图会在节点被放置前收到 `OnMoving`，之后收到 `OnMoved`；在 `OnMoving` 中设置 `e.Handle.PreventDefault` 可钉住节点。
