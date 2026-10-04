# Functions · Mutation Tools

Category `Mutation` — **23 tools**. Each executes exactly one component command (single undo entry at most; the framework's undo/redo stack is authoritative). Every mutation counts as a **write** against `MaxWriteToolCalls` and (with `WithAutoMarkDirty(true)`) marks the tree dirty.

## Geometry & lifecycle

| Tool | Signature | Purpose |
|---|---|---|
| `MoveNode` | `MoveNode(int nodeIndex, double offsetX, double offsetY)` | Moves a node by relative offset by dispatching `MoveCommand` with an `Offset` delta. Mirrors GUI drag (delta in view space, scaled to world; `Anchor.Layer` preserved). **Not undoable.** |
| `SetNodePosition` | `SetNodePosition(int nodeIndex, double left, double top, int? layer = null)` | Absolute position via `SetAnchorCommand`. Omit `layer` to keep the current z-order (it is not dropped to 0). **Not undoable.** |
| `ResizeNode` | `ResizeNode(int nodeIndex, double width, double height)` | `SetSizeCommand`. **Not undoable.** |
| `CreateNode` | `CreateNode(string fullTypeName, double left = 0, double top = 0, double width = 0, double height = 0)` | Creates a node via `CreateNodeCommand`; position auto-offsets to avoid overlap; `0` size reads the type's `[DefaultSize]` (fallback 300×260). |
| `DeleteNode` | `DeleteNode(int nodeIndex)` | Deletes a node; cascades child slots + connections atomically (one undo entry). |
| `DeleteSlot` | `DeleteSlot(int nodeIndex, int slotIndex)` | Deletes a slot and its connections. |

Source: `NodeGeometryToolTests` (`MoveNode_LandsWhereADragWould_AtANonUnitScale`, `SetNodePosition_WithoutALayerKeepsTheExistingOne`, `GeometryTools_ReRaiseAnchorAndSize`).

## Connections

| Tool | Signature | Purpose |
|---|---|---|
| `ConnectSlots` | `ConnectSlots(int senderNodeIndex, int senderSlotIndex, int receiverNodeIndex, int receiverSlotIndex)` | Connect by indices. Prefer `ConnectByProperty` — indices shift on `SlotEnumerator` nodes. |
| `ConnectSlotsById` | `ConnectSlotsById(string senderSlotId, string receiverSlotId)` | Connect by slot runtime IDs (stable across redraws, not across `SlotEnumerator` reconfiguration). |
| `ConnectByProperty` | `ConnectByProperty(int senderNodeIndex, string senderProperty, int receiverNodeIndex, string receiverProperty, int senderCollectionIndex = 0, int receiverCollectionIndex = 0)` | Connect by slot property names on the owning nodes — no id resolution needed. The preferred route. |
| `DisconnectSlots` | `DisconnectSlots(int senderNodeIndex, int senderSlotIndex, int receiverNodeIndex, int receiverSlotIndex)` | Removes a connection by indices. |
| `DisconnectSlotsById` | `DisconnectSlotsById(string senderSlotId, string receiverSlotId)` | Removes a connection by slot runtime IDs. |
| `SetSlotChannel` | `SetSlotChannel(int nodeIndex, int slotIndex, string channel)` | Changes a slot's channel. |
| `SetEnumSlotChannel` | `SetEnumSlotChannel(int nodeIndex, string propertyName, string conditionValue, string channel)` | Channel of a `SlotEnumerator` slot, by condition value. |
| `ConnectEnumSlot` | `ConnectEnumSlot(int senderNodeIndex, string senderProperty, string senderCondition, int receiverNodeIndex, string receiverSlot, string? receiverCondition = null)` | Connects a `SlotEnumerator` slot by condition to a plain slot/index or another enumerator slot. |

**Connection rejects.** Connection tools verify the link actually exists in `LinksMap` after dispatching; the framework may silently refuse (channel incompatibility, same-node rule, `ValidateConnection`). On refusal they return `status: "rejected"` with `reasons`, `hint`, and often `preferredAlternative` naming the property-route tool to use next — never blindly retry.

## Properties & slots

| Tool | Signature | Purpose |
|---|---|---|
| `PatchNodeProperties` | `PatchNodeProperties(int nodeIndex, string jsonPatch)` | Patches a node's custom properties (`{"Title":"New"}`). Rejects command-backed props, framework-managed props, and source-gen slot props. |
| `PatchComponentById` | `PatchComponentById(string runtimeId, string jsonPatch)` | Same rejection rules, for any component by runtime ID (node/slot/link). |
| `CreateSlotOnNode` | `CreateSlotOnNode(int nodeIndex, string fullSlotTypeName, string channel = "OneBoth")` | Dynamic slot via `CreateSlotCommand`; only when the node does not already define typed slot properties. |
| `AddSlotToCollection` | `AddSlotToCollection(int nodeIndex, string propertyName, string fullSlotTypeName, string channel = "MultipleBoth")` | Adds a slot to a collection property via the node's `CreateSlotCommand`. |
| `RemoveSlotFromCollection` | `RemoveSlotFromCollection(int nodeIndex, string propertyName, string slotRuntimeId)` | Removes a slot from a collection property by slot runtime ID. |
| `SetEnumSlotCollection` | `SetEnumSlotCollection(int nodeIndex, string propertyName, string selectorTypeOrJson, string nonEnumTypeName = "")` | Sets a `SlotEnumerator` selector (enum/bool type name, or non-enum `ISlotProvider` via JSON + `nonEnumTypeName`). |

Source: `WorkflowLifecycleFidelityTests.AddSlotToCollection_RegistersSlotInNodeSlots_AndIsUndoable`, `SlotEnumerator_RoundTripsSelectorType`.

## History

| Tool | Signature | Purpose |
|---|---|---|
| `Undo` | `Undo()` | Undoes the last action. |
| `Redo` | `Redo()` | Redoes the last undone action. |
| `ClearHistory` | `ClearHistory()` | Clears the entire undo/redo history **without touching the canvas** — only the recorded mutation trail is dropped. |

## Example

```text
// Source: Test — NodeGeometryToolTests / WorkflowLifecycleFidelityTests
SetNodePosition(nodeIndex: 0, left: 200, top: 300)   → {"status":"ok"}   // layer stays 7
AddSlotToCollection(0, "OutputSlots", "Demo.OutSlot") → {"status":"ok"}   // 1 slot, Parent == node
Undo()                                                 → {"status":"ok"}   // slot removed, Parent nulled
Redo()                                                 → {"status":"ok"}   // same slot instance restored
```

**Expected result:** `MoveNode` lands the node where a GUI drag would at the same scale; `SetNodePosition` without `layer` keeps the node's z-order.
