# 连接规则与预览

一次连接尝试有两种截然不同的代价。合法性检查与拖拽预览都是常数时间的标志位与引用比较。真正的工作在提交连接时：它可能要清理冲突连线，而某些清理模式会扫描映射中的每个发送方，或比较两个节点上的每一对插槽。

记号：`LinksMap` 中的 $U$ 个不同发送方插槽，单插槽度 $d$，发送方与接收方节点上的插槽数 $S_s$ 与 $S_r$，连线数 $L$。

## 代价模型

| 操作 | 时间 | 出处 |
|---|---|---|
| `StandardCheckConnection` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:202` |
| `StandardSetPreviewReceiver`，候选未变 | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:157` |
| `StandardRefreshConnectionPreview` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:169` |
| `StandardSendConnection` | $O(U + d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:111` |
| `StandardReceiveConnection` | $O(S_s S_r + U + d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:271` |
| `StandardResetVirtualLink` | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:317` |
| `StandardSetChannel` | $O(d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSlotEx.cs:19` |

检查确实是常数：两次标志位判断、一次父节点引用比较、一次宿主规则调用。

```csharp
if (checkSender && !sender.StandardCanBeSender())
    return ConnectionCheck.Rejected(ConnectionRejectReason.SenderCannotSend);
...
if (ReferenceEquals(sender.Parent, receiver.Parent))
    return ConnectionCheck.Rejected(ConnectionRejectReason.SameNode);
...
return component.GetHelper().ValidateConnection(sender, receiver)
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:222-231`

默认 `ValidateConnection` 以常数时间返回 `true`，所以除非宿主覆写它，规则本身不改变上界。该覆写是本页唯一*推断*的代价。

## 预览按指针移动去重

拖拽时每次指针移动都会触发一次预览更新。候选未变时实现直接短路，因此常见路径只是一次引用比较：

```csharp
if (!force && ReferenceEquals(input.PreviewReceiver, slot)) return;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:255`

只有候选改变时才写插槽状态标志、重算预览状态并触发事件。这让拖拽保持每次移动 $O(1)$。

## 提交可能对插槽呈二次

昂贵路径是"同方向"清理，它把发送方节点的每个插槽与接收方节点的每个插槽比较：

```csharp
foreach (var potentialSender in senderNode.Slots)
{
    if (component.LinksMap.TryGetValue(potentialSender, out var targetLinks))
    {
        foreach (var potentialReceiver in receiverNode.Slots)
        {
            if (targetLinks.TryGetValue(potentialReceiver, out var existingLink))
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:494-500`

这就是 $S_s S_r$ 项。`OneBoth` 清理模式改为扫描外层 `LinksMap`，即 $U$ 项。完整上界为：

$$
T_{\text{receive}} = O(S_s S_r + U + d)
$$

发送更便宜，只围绕发送方清理：$O(U + d)$。在度有界的图中——每节点只有几个插槽——各项都退化为常数，嵌套乘积也很小。二次形态只出现在端口很多的节点上。

## 内存

每个树的实时预览状态是固定几个字段，通过 `ConditionalWeakTable` 惰性创建。一次清理批次只在其调用期间分配一个按 $d$ 或 $U$ 大小的 `List<(ISlotComponent, ISlotComponent, ILinkComponent)>`；每次预览变化分配一个 `ConnectionCheck` 值和一个事件参数对象。跨多次尝试不累积任何东西。
