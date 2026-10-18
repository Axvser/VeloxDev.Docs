# Workflow System — 命名空间：`VeloxDev.WorkflowSystem.StandardEx`

实现生成命令所调用标准行为的静态扩展类。`GetStandardCommands()` 返回组件的命令列表，用于生命周期锁定/清理。

| 类 | 关键成员 |
|---|---|
| `WorkflowTreeEx` | `GetStandardCommands`、`StandardCreateNode`、`StandardSetPointer`、`StandardSendConnection`、`StandardSetPreviewReceiver`、`StandardRefreshConnectionPreview`、`StandardCheckConnection`、`StandardReceiveConnection`、`StandardResetVirtualLink`、`StandardSubmit`、`StandardUndo`、`StandardRedo`、`StandardClearHistory`、`StandardCloseAsync`；度/拓扑查询 `GetNodeInDegree`、`GetNodeOutDegree`、`FindEntryNodeIndices`、`FindExitNodeIndices`、`FindNodesByInDegree`、`FindNodesByOutDegree` |
| `WorkflowNodeEx` | `GetStandardCommands`、`StandardCreateSlot`、`StandardMove`、`StandardSetAnchor`、`StandardSetLayer`、`StandardSetSize`、`StandardDelete`、`StandardBroadcastAsync`、`StandardReverseBroadcastAsync`；图遍历 `SearchForwardNodes`、`SearchReverseNodes`、`SearchAllRelativeNodes` |
| `WorkflowSlotEx` | `GetStandardCommands`、`StandardSetChannel`、`StandardUpdateState`、`StandardApplyConnection`、`StandardReceiveConnection`、`StandardCanBeSender`、`StandardCanBeReceiver`、`StandardDelete` |
| `WorkflowLinkEx` | `GetStandardCommands`、`StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`、`StandardClosingAsync`、`StandardClose`、`StandardCloseAsync`、`StandardClosed`、`StandardClosedAsync` |
| `WorkflowSpatialEx` | 见上文空间系统。它与其余类同属 `StandardEx` 命名空间，但文件位于 `WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`（不在 `StandardEx/` 下） |

### 连接预览成员详解

| 成员 | 签名 | 行为 |
|---|---|---|
| `StandardSetPreviewReceiver` | `void StandardSetPreviewReceiver(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel? slot)` | 上报指针下的候选。它计算 `StandardCheckConnection`、标记 `SlotState.PreviewReceiver`，并把阶段发布到虚拟连线。重复同一候选很便宜：候选不变时不会再次询问宿主的 `PreviewValidating`。传入发送端自身视作「无候选」。 |
| `StandardRefreshConnectionPreview` | `void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)` | 对指针下已有的候选重跑检查，绕过同候选短路。这是异步宿主校验的入口：在 `PreviewValidating` 里启动工作，判定落地时调用它。没有拖拽进行时是空操作。 |
| `StandardCheckConnection` | `ConnectionCheck StandardCheckConnection(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | 纯检查：发送能力、接收能力、同节点规则，然后 `IWorkflowTreeViewModelHelper.ValidateConnection`。无事件、无状态变更。任一参数为 `null` 抛 `ArgumentNullException`。 |
| `StandardUpdateState`（`WorkflowSlotEx`） | `void StandardUpdateState(this IWorkflowSlotViewModel component)` | 从连接列表重算 `Sender`/`Receiver`/`StandBy`，同时**保留** `PreviewSender` 与 `PreviewReceiver` —— 这两个位属于拖拽，不属于连接列表。 |

`StandardCheckConnection` 的规则顺序是「第一个拒绝者胜出」：`SenderCannotSend` → `ReceiverCannotReceive` → `SameNode` → `RejectedByRule`。通道容量不算拒绝，因为完成连接会先按通道清理既有连接。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/`（`WorkflowSpatialEx` 除外，位于 `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`）。预览行为由 `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs` 钉住。*
