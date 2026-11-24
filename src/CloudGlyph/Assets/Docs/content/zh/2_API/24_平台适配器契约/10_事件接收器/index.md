# 事件接收器

输入是指针与键盘的路由；**接收器**是另一个方向——宿主对象因标记无法直接订阅事件处理器而改由它接收组件的模型事件。适配器暴露 `WorkflowEvents` 附着属性，把接收器装到节点、插槽或树上。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。附着属性位于各适配器的 `VeloxDev.WorkflowSystem.AttachedBehaviors`。

## INodeEventSink

**签名：** `interface INodeEventSink`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `OnMoving` / `OnMoved` | `void (NodeMoveEventArgs e)` | 节点被放置之前与之后。 |
| `OnResizing` / `OnResized` | `void (NodeResizeEventArgs e)` | 尺寸变化之前与之后。 |
| `OnDeleting` / `OnDeleted` | `void (NodeEventArgs e)` | 节点被拆除之前与之后。 |

## ISlotEventSink

**签名：** `interface ISlotEventSink`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `OnChannelChanging` | `void (SlotChannelEventArgs e)` | 插槽通道变化之前；通过句柄拒绝。 |
| `OnChannelChanged` | `void (SlotChannelEventArgs e)` | 变化之后。 |

## ITreeEventSink

**签名：** `interface ITreeEventSink`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `OnConnecting` | `void (ConnectionEventArgs e)` | 建立连接之前；通过句柄拒绝该次拖拽。 |
| `OnConnected` | `void (ConnectionEventArgs e)` | 连线已存在之后。 |

每个方法收到与 Helper 自身事件相同的参数对象，因此 `WorkflowEventHandle` 随之传递。在 `On…ing` 方法中设置 `PreventDefault` 可拒绝该次动作。方法同步运行；阻塞的接收器会阻塞交互。`OnConnecting` 与 `ITreeHelper.ValidateConnection` 组合：只有两者都不拒绝时连接才发生。

```csharp
sealed class TreeSink : ITreeEventSink
{
    public void OnConnecting(ConnectionEventArgs e)
    {
        if (e.Sender.Parent != e.Receiver.Parent) e.Handle.PreventDefault = true;
    }

    public void OnConnected(ConnectionEventArgs e) { }
}
```

**预期结果：** 把 `WorkflowEvents.SetTree(host, sink)` 附着到图宿主后，`OnConnecting` 在连线创建前被调用；拒绝它会取消该次拖拽。
