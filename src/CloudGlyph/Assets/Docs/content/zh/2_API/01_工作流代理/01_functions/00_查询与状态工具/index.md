# 函数 · 查询与状态工具

命名空间 `VeloxDev.AI.Workflow.Functions`。以下每个签名即该工具的参数列表（模型看到的是参数名与 `[Description]` 文本）。除注明外都返回带 `status` 的紧凑 JSON。**23 个工具：`Query`（20）+ `State`（3）。**

## Query —— 只读检查（20）

节点几何（`x` / `y` / `l` / `w` / `h`）按**世界坐标**报告 —— 也就是 `CreateNode`、`SetNodePosition` 与存档写入所用的同一坐标系，不受画布缩放影响。直接读 `Anchor` / `Size` 拿到的是**折叠后**的值（它们的 getter 会除以 `Layout.Scale`），所以查询工具统一走 `WorldAnchor` / `WorldSize`（`WorkflowAgentToolkit.cs:2844-2879`）—— 模型读回来的与它写进去的才是同一个数。

| 工具 | 签名 | 用途 |
|---|---|---|
| `ListNodes` | `ListNodes()` | 紧凑节点列表 `[{i,id,t,x,y,l,w,h,slots,...props}]` —— `i` 零基索引、`id` 运行时 id、`t` 类型简名、`x`/`y` 世界左右、`l` 图层 z-order、`w`/`h` 世界尺寸、`slots` 槽数量；完整信息用 `GetNodeDetail`。 |
| `GetNodeDetail` | `GetNodeDetail(int nodeIndex)` | 按零基索引的完整节点详情：同样的世界几何，外加 `fullType`；`slots` 是**对象数组**（`si` 索引、`id`、`ch` 通道、`st` 状态、`prop`，以及可选的 `tgt`/`src` 连接）而不是计数。 |
| `GetNodeDetailById` | `GetNodeDetailById(string runtimeId)` | 按运行时 ID 的完整节点详情（跨增删稳定）。 |
| `ListConnections` | `ListConnections()` | 仅可见连接（紧凑，含 link id）。要整个图优先用 `GetFullTopology`。 |
| `GetTypeSchema` | `GetTypeSchema(string fullTypeName)` | 按全名返回 .NET 类型的 JSON schema（`TypeIntrospector`）。 |
| `GetWorkflowSummary` | `GetWorkflowSummary()` | 高层摘要：树 id/类型、节点/链接数、不同节点类型。先调它定位。 |
| `GetComponentContext` | `GetComponentContext(string fullTypeName, string language = "English")` | 类型的 `[AgentContext]` 文档（`"English"` / `"Chinese"`）。 |
| `ListComponentCommands` | `ListComponentCommands(int nodeIndex)` | 节点上的命令：名 + 参数类型。 |
| `FindNodes` | `FindNodes(string typeName = "", string? propertyName = null, string? propertyValue = null)` | 按类型名子串和/或属性取值筛选节点。 |
| `ResolveSlotId` | `ResolveSlotId(int nodeIndex, string propertyName, int collectionIndex = 0)` | 由其属性名解析槽运行时 ID（集合加索引）。 |
| `ListSlotProperties` | `ListSlotProperties(int nodeIndex)` | 命名单槽、槽集合、`SlotEnumerator` 属性，含 id/选择器/`allowedSelectorTypes`。 |
| `GetEnumSlotByValue` | `GetEnumSlotByValue(int nodeIndex, string propertyName, string conditionValue)` | 按枚举/bool 条件值取 `SlotEnumerator` 槽的运行时 ID。 |
| `GetLinkDetail` | `GetLinkDetail(string linkId)` | 按运行时 ID 的完整链接详情（发送/接收槽 + 父节点）。 |
| `ListCreatableTypes` | `ListCreatableTypes()` | 可创建的节点/槽类型（扫描已注册 + 树所在程序集）。 |
| `ValidateWorkflow` | `ValidateWorkflow()` | 警告：零尺寸、孤立（有槽无连接）、无槽节点、重复链接。 |
| `GetFullTopology` | `GetFullTopology()` | 一次调用取整图：节点 + 槽（属性名/id）+ 连接。 |
| `CompileWorkflow` | `CompileWorkflow(int startNodeIndex)` | 从起始节点可达子图的编译计划（Root 角色）。 |
| `CompileNodeResult` | `CompileNodeResult(int nodeIndex)` | 某节点祖先锥的编译计划（Terminal 角色）。 |
| `GetCompileStatus` | `GetCompileStatus()` | 每个编译感知节点的当前编译身份（`Order`/`ChainIndex`/`Offset`/`isStopped`），无需重新编译。 |
| `GetExecutionLog` | `GetExecutionLog()` | 树的聚合直接执行日志（约定命名的 `ExecutionLog` 属性）。 |

**槽的发现有一条运行期兜底。** 按属性名解析槽被 `ResolveSlotId`、`ListSlotProperties`、`ConnectEnumSlot`（以及两个私有辅助）使用。一条属性算作单槽的条件是：编译期标志说是**或者**该属性**当前持有的值**是 `IWorkflowSlotViewModel` —— 即 `TreeProperty.HoldsASingleSlot`，`WorkflowAgentToolkit.cs:2780`。第二个判据是给「装了旧版生成器的消费方」用的：`[WorkflowBuilder.Slot<T>]` 注入的槽组件接口，与上下文生成器跑在**同一个编译趟**里，而源生成器看不见另一个生成器的产物（`AIContextModel.cs:917-935`）—— 所以在修复之前发布的包里，根本没有标志可读。

注意 `CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`、`GetExecutionLog` 是 **Query 工具**，但从不运行节点代码 —— 它们不受 `WithAllowNodeExecution` 闸控。

## State / 差异 / 脏标记（3）

| 工具 | 签名 | 用途 |
|---|---|---|
| `TakeSnapshot` | `TakeSnapshot()` | 取状态快照；只返回 `version` + 摘要计数。 |
| `GetChangesSinceSnapshot` | `GetChangesSinceSnapshot()` | 自上一快照的差异（新增/移除/修改的节点与链接）。 |
| `MarkDirty` | `MarkDirty()` | 把树标为脏 —— 自动标脏关闭时，在变更任务末尾调用一次。 |

`TakeSnapshot` / `GetChangesSinceSnapshot` 读自 `WorkflowStateTracker`；见 `VeloxDev.AI.Workflow` 页。`MarkDirty` 是**写**（计入 `MaxWriteToolCalls`，且与只读不同，会把树标脏）。

## 示例

```text
// Source: Test — ComposedProvidersTests
ListNodes()                                  → [{"i":0,"id":"...","t":"NodeDefaultViewModel",...}]
GetChangesSinceSnapshot()                    → {"status":"diff","version":2,"changes":{"addedNodes":[...]}}
MarkDirty()                                  → {"status":"ok"}
```

**预期结果：** 先 `AddSlotToCollection` 再 `Undo`（见变更工具页），会使 `GetChangesSinceSnapshot` 在 `changes` 中报告该槽的移除。
