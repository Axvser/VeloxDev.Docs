# Workflow System — 命名空间：`VeloxDev.WorkflowSystem.StandardEx`

实现生成命令所调用标准行为的静态扩展类。`GetStandardCommands()` 返回组件的命令列表，用于生命周期锁定/清理。

| 类 | 关键成员 |
|---|---|
| `WorkflowTreeEx` | `GetStandardCommands`、`StandardCreateNode`、`StandardSetPointer`、`StandardSendConnection`、`StandardReceiveConnection`、`StandardResetVirtualLink`、`StandardSubmit`、`StandardUndo`、`StandardRedo`、`StandardClearHistory`、`StandardCloseAsync`；度/拓扑查询 `GetNodeInDegree`、`GetNodeOutDegree`、`FindEntryNodeIndices`、`FindExitNodeIndices`、`FindNodesByInDegree`、`FindNodesByOutDegree` |
| `WorkflowNodeEx` | `GetStandardCommands`、`StandardCreateSlot`、`StandardMove`、`StandardSetAnchor`、`StandardSetLayer`、`StandardSetSize`、`StandardDelete`、`StandardBroadcastAsync`、`StandardReverseBroadcastAsync`；图遍历 `SearchForwardNodes`、`SearchReverseNodes`、`SearchAllRelativeNodes` |
| `WorkflowSlotEx` | `GetStandardCommands`、`StandardSetChannel`、`StandardUpdateState`、`StandardApplyConnection`、`StandardReceiveConnection`、`StandardCanBeSender`、`StandardCanBeReceiver`、`StandardDelete` |
| `WorkflowLinkEx` | `GetStandardCommands`、`StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`、`StandardClosingAsync`、`StandardClose`、`StandardCloseAsync`、`StandardClosed`、`StandardClosedAsync` |
| `WorkflowSpatialEx` | 见上文空间系统 |

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/`。*
