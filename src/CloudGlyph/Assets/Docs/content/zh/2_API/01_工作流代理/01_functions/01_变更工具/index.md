# 函数 · 变更工具

类别 `Mutation` —— **23 个工具**。每个恰好执行一条组件命令（至多一条撤销记录；框架的撤销/重做栈是权威）。每个变更都计入 `MaxWriteToolCalls` 的**写**，并在 `WithAutoMarkDirty(true)` 时把树标脏。

## 几何与生命周期

| 工具 | 签名 | 用途 |
|---|---|---|
| `MoveNode` | `MoveNode(int nodeIndex, double offsetX, double offsetY)` | 以 `Offset` 增量派发 `MoveCommand` 相对移动节点。镜像 GUI 拖拽（增量在视图空间、按比例转世界；保留 `Anchor.Layer`）。**不可撤销。** |
| `SetNodePosition` | `SetNodePosition(int nodeIndex, double left, double top, int? layer = null)` | 经 `SetAnchorCommand` 绝对定位。省略 `layer` 保留当前 z 序（不会掉到 0）。**不可撤销。** |
| `ResizeNode` | `ResizeNode(int nodeIndex, double width, double height)` | `SetSizeCommand`。**不可撤销。** |
| `CreateNode` | `CreateNode(string fullTypeName, double left = 0, double top = 0, double width = 0, double height = 0)` | 经 `CreateNodeCommand` 创建节点；位置自动偏移避免重叠；尺寸 `0` 读取类型的 `[DefaultSize]`（回退 300×260）。 |
| `DeleteNode` | `DeleteNode(int nodeIndex)` | 删除节点；级联删除子槽与其连接（一条撤销记录）。 |
| `DeleteSlot` | `DeleteSlot(int nodeIndex, int slotIndex)` | 删除槽及其连接。 |

来源：`NodeGeometryToolTests`（`MoveNode_LandsWhereADragWould_AtANonUnitScale`、`SetNodePosition_WithoutALayerKeepsTheExistingOne`、`GeometryTools_ReRaiseAnchorAndSize`）。

## 连接

| 工具 | 签名 | 用途 |
|---|---|---|
| `ConnectSlots` | `ConnectSlots(int senderNodeIndex, int senderSlotIndex, int receiverNodeIndex, int receiverSlotIndex)` | 按索引连接。优先 `ConnectByProperty` —— `SlotEnumerator` 节点的索引会变。 |
| `ConnectSlotsById` | `ConnectSlotsById(string senderSlotId, string receiverSlotId)` | 按槽运行时 ID 连接（跨重绘稳定，不跨 `SlotEnumerator` 重配置）。 |
| `ConnectByProperty` | `ConnectByProperty(int senderNodeIndex, string senderProperty, int receiverNodeIndex, string receiverProperty, int senderCollectionIndex = 0, int receiverCollectionIndex = 0)` | 按所属节点上的槽属性名连接 —— 无需解析 id。首选路径。 |
| `DisconnectSlots` | `DisconnectSlots(int senderNodeIndex, int senderSlotIndex, int receiverNodeIndex, int receiverSlotIndex)` | 按索引移除连接。 |
| `DisconnectSlotsById` | `DisconnectSlotsById(string senderSlotId, string receiverSlotId)` | 按槽运行时 ID 移除连接。 |
| `SetSlotChannel` | `SetSlotChannel(int nodeIndex, int slotIndex, string channel)` | 修改槽的通道。 |
| `SetEnumSlotChannel` | `SetEnumSlotChannel(int nodeIndex, string propertyName, string conditionValue, string channel)` | 按条件值设置 `SlotEnumerator` 槽的通道。 |
| `ConnectEnumSlot` | `ConnectEnumSlot(int senderNodeIndex, string senderProperty, string senderCondition, int receiverNodeIndex, string receiverSlot, string? receiverCondition = null)` | 按条件把 `SlotEnumerator` 槽连接到普通槽/索引或另一枚举器槽。 |

**连接拒绝。** 连接工具在派发后校验链接确实存在于 `LinksMap`；框架可能静默拒绝（通道不兼容、同节点规则、`ValidateConnection`）。被拒时返回 `status: "rejected"`，带 `reasons`、`hint`，通常还有 `preferredAlternative` 指名接下来该用的属性路由工具 —— 绝不要盲目重试。

## 属性与槽

| 工具 | 签名 | 用途 |
|---|---|---|
| `PatchNodeProperties` | `PatchNodeProperties(int nodeIndex, string jsonPatch)` | 补丁节点的自定义属性（`{"Title":"New"}`）。拒绝命令驱动的属性、框架管理的属性、源生成槽属性。 |
| `PatchComponentById` | `PatchComponentById(string runtimeId, string jsonPatch)` | 同样的拒绝规则，作用于按运行时 ID 的任意组件（节点/槽/链接）。 |
| `CreateSlotOnNode` | `CreateSlotOnNode(int nodeIndex, string fullSlotTypeName, string channel = "OneBoth")` | 经 `CreateSlotCommand` 创建动态槽；仅当节点尚未定义类型化槽属性时使用。 |
| `AddSlotToCollection` | `AddSlotToCollection(int nodeIndex, string propertyName, string fullSlotTypeName, string channel = "MultipleBoth")` | 经节点的 `CreateSlotCommand` 向集合属性添加槽。 |
| `RemoveSlotFromCollection` | `RemoveSlotFromCollection(int nodeIndex, string propertyName, string slotRuntimeId)` | 按槽运行时 ID 从集合属性移除槽。 |
| `SetEnumSlotCollection` | `SetEnumSlotCollection(int nodeIndex, string propertyName, string selectorTypeOrJson, string nonEnumTypeName = "")` | 设置 `SlotEnumerator` 选择器（枚举/bool 类型名，或经 JSON + `nonEnumTypeName` 的非枚举 `ISlotProvider`）。 |

来源：`WorkflowLifecycleFidelityTests.AddSlotToCollection_RegistersSlotInNodeSlots_AndIsUndoable`、`SlotEnumerator_RoundTripsSelectorType`。

## 历史

| 工具 | 签名 | 用途 |
|---|---|---|
| `Undo` | `Undo()` | 撤销上一操作。 |
| `Redo` | `Redo()` | 重做上一被撤销的操作。 |
| `ClearHistory` | `ClearHistory()` | 清空整条撤销/重做历史，**不动画布** —— 只丢弃已记录的变更轨迹。 |

## 示例

```text
// Source: Test — NodeGeometryToolTests / WorkflowLifecycleFidelityTests
SetNodePosition(nodeIndex: 0, left: 200, top: 300)   → {"status":"ok"}   // layer 保持 7
AddSlotToCollection(0, "OutputSlots", "Demo.OutSlot") → {"status":"ok"}   // 1 个槽，Parent == node
Undo()                                                 → {"status":"ok"}   // 槽移除，Parent 置空
Redo()                                                 → {"status":"ok"}   // 恢复同一槽实例
```

**预期结果：** 同一缩放比例下 `MoveNode` 的落点与 GUI 拖拽一致；`SetNodePosition` 不传 `layer` 保留节点的 z 序。
