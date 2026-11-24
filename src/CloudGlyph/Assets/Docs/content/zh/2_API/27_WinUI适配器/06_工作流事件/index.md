# 工作流事件

`WorkflowEvents` 通过三个附着属性把 Core 模型事件接收器装到 WinUI 元素上。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WinUI`。

## WorkflowEvents

**签名：** `static class WorkflowEvents`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `Node` | `INodeEventSink?` | `null` | 接收所绑定节点的移动、缩放与删除事件。 |
| `Slot` | `ISlotEventSink?` | `null` | 接收所绑定插槽的通道事件。 |
| `Tree` | `ITreeEventSink?` | `null` | 接收所绑定树的连接事件。 |

访问器：`GetNode` / `SetNode`、`GetSlot` / `SetSlot`、`GetTree` / `SetTree`，均接收 `DependencyObject`。

该行为观察 `DataContext`；当它成为 `INodeComponent`、`ISlotComponent` 或 `ITreeComponent` 时，对应 Helper 的事件被转发给接收器。接收器方法收到 Helper 自身的参数（含 `WorkflowEventHandle`）。

```xml
<Grid behaviors:WorkflowEvents.Node="{Binding NodeSink}"
      behaviors:WorkflowEvents.Tree="{Binding TreeSink}" />
```

**预期结果：** 带有 `Node` 接收器的节点视图会在放置前收到 `OnMoving`、之后收到 `OnMoved`；在 `OnMoving` 中设置 `e.Handle.PreventDefault` 可钉住节点。
