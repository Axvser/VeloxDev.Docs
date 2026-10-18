# Workflow System — Namespace: `VeloxDev.WorkflowSystem.StandardEx`

Static extension classes implementing the standard behavior invoked by generated commands. `GetStandardCommands()` returns the component's command list for lifecycle lock/clear.

| Class | Key members |
|---|---|
| `WorkflowTreeEx` | `GetStandardCommands`, `StandardCreateNode`, `StandardSetPointer`, `StandardSendConnection`, `StandardSetPreviewReceiver`, `StandardRefreshConnectionPreview`, `StandardCheckConnection`, `StandardReceiveConnection`, `StandardResetVirtualLink`, `StandardSubmit`, `StandardUndo`, `StandardRedo`, `StandardClearHistory`, `StandardCloseAsync`; degree/topology queries `GetNodeInDegree`, `GetNodeOutDegree`, `FindEntryNodeIndices`, `FindExitNodeIndices`, `FindNodesByInDegree`, `FindNodesByOutDegree` |
| `WorkflowNodeEx` | `GetStandardCommands`, `StandardCreateSlot`, `StandardMove`, `StandardSetAnchor`, `StandardSetLayer`, `StandardSetSize`, `StandardDelete`, `StandardBroadcastAsync`, `StandardReverseBroadcastAsync`; graph traversal `SearchForwardNodes`, `SearchReverseNodes`, `SearchAllRelativeNodes` |
| `WorkflowSlotEx` | `GetStandardCommands`, `StandardSetChannel`, `StandardUpdateState`, `StandardApplyConnection`, `StandardReceiveConnection`, `StandardCanBeSender`, `StandardCanBeReceiver`, `StandardDelete` |
| `WorkflowLinkEx` | `GetStandardCommands`, `StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`, `StandardClosingAsync`, `StandardClose`, `StandardCloseAsync`, `StandardClosed`, `StandardClosedAsync` |
| `WorkflowSpatialEx` | See Spatial System above. It shares the `StandardEx` namespace, but its file lives in `WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs` (not under `StandardEx/`) |

### Connection-preview members in detail

| Member | Signature | Behavior |
|---|---|---|
| `StandardSetPreviewReceiver` | `void StandardSetPreviewReceiver(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel? slot)` | Reports the candidate under the pointer. It computes `StandardCheckConnection`, marks `SlotState.PreviewReceiver`, and publishes the stage on the virtual link. Repeating the same candidate is cheap: the host's `PreviewValidating` is not consulted again until the candidate changes. Passing the sender itself is treated as "no candidate". |
| `StandardRefreshConnectionPreview` | `void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)` | Re-runs the check for the candidate already under the pointer, bypassing the same-candidate short-circuit. This is the entry for asynchronous host validation: start work in `PreviewValidating`, then call this when the verdict lands. No-op when no drag is in progress. |
| `StandardCheckConnection` | `ConnectionCheck StandardCheckConnection(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | Pure check: sender capability, receiver capability, same-node rule, then `IWorkflowTreeViewModelHelper.ValidateConnection`. No events, no state changes. Throws `ArgumentNullException` for a null argument. |
| `StandardUpdateState` (`WorkflowSlotEx`) | `void StandardUpdateState(this IWorkflowSlotViewModel component)` | Recomputes `Sender`/`Receiver`/`StandBy` from the connection lists while **preserving** `PreviewSender` and `PreviewReceiver` — those two bits belong to the drag, not to the connection lists. |

The rule order in `StandardCheckConnection` is the first refusal wins: `SenderCannotSend` → `ReceiverCannotReceive` → `SameNode` → `RejectedByRule`. Channel capacity is not a rejection because completing a connection cleans up existing connections according to the channel first.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/` (except `WorkflowSpatialEx`, at `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`). Preview behavior is pinned by `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs`.*
