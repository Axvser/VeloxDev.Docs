# Workflow System — Namespace: `VeloxDev.WorkflowSystem.StandardEx`

Static extension classes implementing the standard behavior invoked by generated commands. `GetStandardCommands()` returns the component's command list for lifecycle lock/clear.

| Class | Key members |
|---|---|
| `WorkflowTreeEx` | `GetStandardCommands`, `StandardCreateNode`, `StandardSetPointer`, `StandardSendConnection`, `StandardReceiveConnection`, `StandardResetVirtualLink`, `StandardSubmit`, `StandardUndo`, `StandardRedo`, `StandardClearHistory`, `StandardCloseAsync`; degree/topology queries `GetNodeInDegree`, `GetNodeOutDegree`, `FindEntryNodeIndices`, `FindExitNodeIndices`, `FindNodesByInDegree`, `FindNodesByOutDegree` |
| `WorkflowNodeEx` | `GetStandardCommands`, `StandardCreateSlot`, `StandardMove`, `StandardSetAnchor`, `StandardSetLayer`, `StandardSetSize`, `StandardDelete`, `StandardBroadcastAsync`, `StandardReverseBroadcastAsync`; graph traversal `SearchForwardNodes`, `SearchReverseNodes`, `SearchAllRelativeNodes` |
| `WorkflowSlotEx` | `GetStandardCommands`, `StandardSetChannel`, `StandardUpdateState`, `StandardApplyConnection`, `StandardReceiveConnection`, `StandardCanBeSender`, `StandardCanBeReceiver`, `StandardDelete` |
| `WorkflowLinkEx` | `GetStandardCommands`, `StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`, `StandardClosingAsync`, `StandardClose`, `StandardCloseAsync`, `StandardClosed`, `StandardClosedAsync` |
| `WorkflowSpatialEx` | See Spatial System above |

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/`.*
