# 工作流系统 — 设计模式 — 连接预览

连接拖拽预览是带一个**宿主策略钩子**的小型**规则链**。它不是第二套连接实现：预览与完成的连接运行同一套规则，所以二者对一对槽是否合法不可能给出不同答案。

## 规则链

`StandardCheckConnection` 是纯函数 —— 无事件、无状态变更 —— 返回第一条拒绝规则：

| 顺序 | 规则 | 拒绝原因 |
|---|---|---|
| 1 | `sender.StandardCanBeSender()` —— 通道允许出向 | `SenderCannotSend` |
| 2 | `receiver.StandardCanBeReceiver()` —— 通道允许入向 | `ReceiverCannotReceive` |
| 3 | `sender.Parent != receiver.Parent` | `SameNode` |
| 4 | `IWorkflowTreeViewModelHelper.ValidateConnection(sender, receiver)` | `RejectedByRule` |

通道**容量**被刻意排除：完成连接时会先按通道清理既有连线，所以「已达容量」不是拒绝，而是「清理之后可以接受」。结果是 `ConnectionCheck` —— `IsValid`、`Reason`、可选 `Message`。

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:195-216
public static ConnectionCheck StandardCheckConnection(
    this IWorkflowTreeViewModel component,
    IWorkflowSlotViewModel sender,
    IWorkflowSlotViewModel receiver)
{
    if (component is null) throw new ArgumentNullException(nameof(component));
    if (sender is null) throw new ArgumentNullException(nameof(sender));
    if (receiver is null) throw new ArgumentNullException(nameof(receiver));

    if (!sender.StandardCanBeSender())
        return ConnectionCheck.Rejected(ConnectionRejectReason.SenderCannotSend);

    if (!receiver.StandardCanBeReceiver())
        return ConnectionCheck.Rejected(ConnectionRejectReason.ReceiverCannotReceive);

    if (ReferenceEquals(sender.Parent, receiver.Parent))
        return ConnectionCheck.Rejected(ConnectionRejectReason.SameNode);

    return component.GetHelper().ValidateConnection(sender, receiver)
        ? ConnectionCheck.Valid
        : ConnectionCheck.Rejected(ConnectionRejectReason.RejectedByRule);
}
```

## 宿主钩子只收紧，永不放松

框架检查通过后，`SetPreviewReceiver` 把候选交给 `WorkflowInput.PreviewValidating`。订阅者可以调用 `Reject(message)`，把检查替换为 `RejectedByHost`。框架已经拒绝的候选永远不会被提供 —— 这种不对称就是契约：*预览可以把绿的变红，绝不能把红的变绿。*

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:194-203
internal ConnectionCheck RaisePreviewValidating(
    IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver, ConnectionCheck check)
{
    var handler = PreviewValidating;
    if (handler is null) return check;

    var args = new ConnectionPreviewValidatingEventArgs(sender, receiver, check);
    handler.Invoke(this, args);
    return args.Check;
}
```

释放时的决定仍由 `IWorkflowTreeEvents.Connecting` 加 `ValidateConnection` 做出；预览是建议性的。这也是 `ConnectionCheck` 没有「能熬过拖拽的宿主否决」概念的原因：为预览拒绝一个候选并不会取消连接 —— 它只在指针停在该候选上时把它画成红色。

## 状态归属：拖拽，而不是连接列表

两个预览位是 `SlotState` 的一部分，但它们**不是**从 `Targets` / `Sources` 派生的。`StandardUpdateState` 重算连接位并保留预览位：

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSlotEx.cs:91-106
public static void StandardUpdateState(this IWorkflowSlotViewModel component)
{
    bool hasOutgoingConnections = component.Targets.Count > 0;
    bool hasIncomingConnections = component.Sources.Count > 0;

    var preview = component.State & (SlotState.PreviewSender | SlotState.PreviewReceiver);
    component.State = preview | ((hasOutgoingConnections, hasIncomingConnections) switch
    {
        (true, false) => SlotState.Sender,
        (false, true) => SlotState.Receiver,
        (true, true) => SlotState.Sender | SlotState.Receiver,
        (false, false) => SlotState.StandBy,
    });
}
```

没有这种保留，拖拽期间完成或移除一条无关连接会悄悄清掉发送端/候选的预览标记，渲染器会在手势中途丢失高亮。

## 去重与异步校验

**候选引用**没变时，`StandardSetPreviewReceiver` 会短路（`SetPreviewReceiver` 在重算检查前就返回），因此在同一个槽内移动不会每帧重跑宿主校验；`WorkflowInput.SetConnectionPreview` 另有状态 + 检查的二次空操作守卫。`StandardRefreshConnectionPreview` 绕过候选守卫 —— 它是异步工作的入口：从 `PreviewValidating` 启动检查，让拖拽继续，判定落地时调用刷新。设计让同步路径保持廉价，同时给异步路径一扇显式的「现在重查」之门。

```csharp
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:162-174
public static void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)
{
    if (component is null) return;

    var input = WorkflowInput.For(component);
    if (input.ConnectionSender is null)
    {
        input.ClearConnectionPreview();
        return;
    }

    SetPreviewReceiver(component, input.PreviewReceiver, force: true);
}
```

## 为什么阶段挂在虚拟连线上

`IConnectionPreviewLink` 是可选能力接口，刻意不放在 `IWorkflowLinkViewModel` 上，理由与其他可选事件接口相同：往那里加成员会打断每个实现者。`LinkDefaultViewModel` 实现了它；自定义虚拟连线也可以。`WorkflowInput.SetPreviewState` 通过该接口写入阶段，链接视图因此能绘制 `Started` / `ValidTarget` / `InvalidTarget` 而不必轮询 `WorkflowInput` —— 偏好事件的宿主则订阅 `PreviewChanged`，它携带同一份快照。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`、`StandardEx/WorkflowSlotEx.cs`、`GUI/Events/WorkflowInput.cs`、`Interfaces/WorkflowSystem/ConnectionCheck.cs`、`Interfaces/WorkflowSystem/IConnectionPreviewLink.cs`、`GUI/Events/Tree/ConnectionPreviewEventArgs.cs`、`GUI/Events/Tree/ConnectionPreviewValidatingEventArgs.cs`。测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs`。Demo：`Examples/Workflow/Avalonia/Demo/Views/Workflow/BezierCurveView.axaml.cs` 绘制三个阶段。*
