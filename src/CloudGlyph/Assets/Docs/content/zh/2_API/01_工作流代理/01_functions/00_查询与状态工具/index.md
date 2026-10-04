# 函数 · 查询与状态工具

命名空间 `VeloxDev.AI.Workflow.Functions`。以下每个签名即该工具的参数列表（模型看到的是参数名与 `[Description]` 文本）。除注明外都返回带 `status` 的紧凑 JSON。**23 个工具：`Query`（20）+ `State`（3）。**

## Query —— 只读检查（20）

| 工具 | 签名 | 用途 |
|---|---|---|
| `ListNodes` | `ListNodes()` | 紧凑节点列表 `[{i,id,t,x,y,l,w,h,slots,...props}]`；完整信息用 `GetNodeDetail`。 |
| `GetNodeDetail` | `GetNodeDetail(int nodeIndex)` | 按零基索引的完整节点详情：属性、带连接的槽。 |
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
