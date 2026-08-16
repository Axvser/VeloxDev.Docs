# Workflow Agent — 命名空间：`VeloxDev.AI.Workflow.Functions`

### `WorkflowAgentToolkit`

**签名：** `public sealed class WorkflowAgentToolkit(WorkflowAgentScope scope)`
**构造异常：** `scope` 为 null 时抛 `ArgumentNullException`。
**关键成员：** `public IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` —— 构建约 60 个带调用追踪包装的 `AITool`。默认 `CreateTools()` 等于 `CreateTools(All)`（由测试断言）。作用域上注册的自定义工具无论 `categories` 如何都始终包含。

**示例：** `WorkflowAgentToolkit.cs` 的 `CreateTools()` 第 34-161 行；测试 `WorkflowAgentToolkitTests.CreateTools_All_MatchesDefaultAndIncludesEveryCategory`。

### `WorkflowToolCategory`

**签名：** `[Flags] public enum WorkflowToolCategory` —— `Query`、`Mutation`、`Execution`、`Command`、`Graph`、`Layout`、`Analytics`、`State`、`Composite`、`Interaction`、`All`。
**说明：** `Layout` 与 `Composite` 为保留位 —— 不存在捆绑的布局/复合工具（每个操作都是单组件命令步骤，绝不绕过撤销/重做栈）。`Interaction` 工具仅在配置了处理器且安全级别 > 0 时出现。

### 工具分组（按 `CreateTools()` 枚举）

所有 JSON 输出均用 `Formatting.None`（紧凑）以节省 token。每个工具返回 JSON 对象；多数使用 `status: "ok" | "error" | "rejected"`。

#### 查询（只读）—— 19 个工具

| 工具 | 用途（来自 `[Description]`） |
|---|---|
| `ListNodes` | 紧凑列表：`[{i,id,t,x,y,l,w,h,slots,...props}]`。 |
| `GetNodeDetail` | 按索引取节点完整详情：属性、带连接的槽位。 |
| `GetNodeDetailById` | 按运行时 ID 取节点完整详情（增删间稳定）。 |
| `ListConnections` | 仅可见连接（紧凑，带连接 id）。 |
| `GetTypeSchema` | 按全名取 .NET 类型的 JSON schema。 |
| `GetWorkflowSummary` | 高层摘要：计数、节点类型去重列表、树 id。 |
| `GetComponentContext` | 按全名取某类型的 `[AgentContext]` 文档（English/Chinese）。 |
| `ListComponentCommands` | 节点的命令：名称 + 参数类型。 |
| `FindNodes` | 按类型名子串和/或属性值过滤节点。 |
| `ResolveSlotId` | 从槽位所属属性名（+ 集合索引）解析运行时 ID。 |
| `ListSlotProperties` | 命名单槽、集合与 `SlotEnumerator` 属性，含 id/选择器。 |
| `GetEnumSlotByValue` | 按枚举/bool 条件值取 `SlotEnumerator` 槽位的运行时 ID。 |
| `GetLinkDetail` | 按运行时 ID 取连接完整详情。 |
| `ListCreatableTypes` | 可创建的节点/槽位类型（扫描已注册 + 树所在程序集）。 |
| `ValidateWorkflow` | 警告：零尺寸、孤立、无槽节点，重复连接。 |
| `GetFullTopology` | 一次调用返回整图：节点+槽位+连接。 |
| `CompileWorkflow` | 编译可达子图；返回条目 + 编译序号。 |
| `GetCompileStatus` | 不重编译读取当前编译身份（Order/ChainIndex/Offset）。 |
| `GetExecutionLog` | 树的聚合直连执行日志（约定命名的 `ExecutionLog` 属性）。 |

#### 状态 / 差异 / 置脏 —— 3 个工具

| 工具 | 用途 |
|---|---|
| `TakeSnapshot` | 状态快照；返回版本 + 概要计数。 |
| `GetChangesSinceSnapshot` | 自上次快照的差异（added/removed/modified 节点与连接）。 |
| `MarkDirty` | 把树标记为脏（关闭自动置脏时在变更任务末尾调用一次）。 |

#### 变更（结构性）—— 23 个工具

| 工具 | 用途 |
|---|---|
| `CreateNode` | 经 `CreateNodeCommand` 创建节点；自动偏移避免重叠；尺寸 0 读取类型默认（回退 300×260）。 |
| `CreateSlotOnNode` | 经 `CreateSlotCommand` 创建动态槽位。 |
| `MoveNode` | 相对偏移移动节点（派发 `SetAnchorCommand`；不可撤销，镜像 GUI 拖拽）。 |
| `SetNodePosition` | 设置绝对位置/层级（派发 `SetAnchorCommand`；不可撤销）。 |
| `ResizeNode` | 调整尺寸（派发 `SetSizeCommand`；不可撤销）。 |
| `DeleteNode` | 删除节点；级联槽位与连接（原子，一个撤销条目）。 |
| `DeleteSlot` | 删除槽位及其连接。 |
| `ConnectSlots` | 按节点/槽位索引连接（优先用 `ConnectByProperty`）。 |
| `ConnectSlotsById` | 按运行时 ID 连接。 |
| `ConnectByProperty` | 按所属节点的槽位属性名连接（复合便捷）。 |
| `DisconnectSlots` | 按节点/槽位索引移除连接。 |
| `DisconnectSlotsById` | 按槽位运行时 ID 移除连接。 |
| `SetSlotChannel` | 修改槽位的 `SlotChannel`。 |
| `SetEnumSlotChannel` | 按条件值设置 `SlotEnumerator` 槽位的通道。 |
| `ConnectEnumSlot` | 连接 `SlotEnumerator` 槽位（按条件）到槽位/索引/枚举槽位。 |
| `PatchNodeProperties` | 修补节点自定义属性（拒绝框架管理与槽位属性）。 |
| `PatchComponentById` | 按运行时 ID 修补任意组件的自定义属性。 |
| `AddSlotToCollection` | 经 `CreateSlotCommand` 向集合属性添加槽位。 |
| `RemoveSlotFromCollection` | 按运行时 ID 从集合属性移除槽位。 |
| `SetEnumSlotCollection` | 在既有节点上设置 `SlotEnumerator` 选择器（枚举/bool 或非枚举 `ISlotProvider`）。 |
| `Undo` | 撤销上一步。 |
| `Redo` | 重做上一步。 |
| `ClearHistory` | 丢弃撤销/重做历史而不触碰画布。 |

#### 执行（节点业务代码，受 `WithAllowNodeExecution` 门禁）—— 5 个工具

| 工具 | 用途 |
|---|---|
| `ExecuteNode` | 执行节点 `ReceiveCommand` 并等待完成（节点级 EXEC）。 |
| `ExecuteNodes` | 对多个节点执行 `ReceiveCommand` 并等待。 |
| `BroadcastNode` | 执行 `BroadcastCommand`（下游派发为 fire-and-forget）。 |
| `ReverseBroadcastNode` | 执行 `ReverseBroadcastCommand`（触发上游 `ReceiveCommand`）。 |
| `RunCompiledWorkflow` | 链级入口：从起点编译并经由 `CompilerEngine` + `RuntimeContext` 驱动整条链。 |

#### 命令（通用，受 `WithAllowedGenericCommands` 门禁）—— 2 个工具

| 工具 | 用途 |
|---|---|
| `ExecuteCommandOnNode` | 按索引执行节点上任意命令。 |
| `ExecuteCommandById` | 按运行时 ID 执行组件（节点/槽位/连接）上任意命令。 |

#### 图（遍历）—— 5 个工具

| 工具 | 用途 |
|---|---|
| `SearchForward` | 从节点 BFS 下游（可选类型过滤、最大深度）。 |
| `SearchReverse` | 从节点 BFS 上游。 |
| `SearchAllRelative` | 两个方向 BFS。 |
| `IsConnected` | 直接/传递连接检查（`forward`/`reverse`/`any`）。 |
| `FindPath` | 两节点间最短前向路径（BFS）。 |

#### 分析 —— 1 个工具

| 工具 | 用途 |
|---|---|
| `GetNodeStatistics` | 入度/出度/总连接/相连节点 id/槽位利用率。 |

#### 交互（仅注册了处理器且安全级别 > 0 时）—— 2 个工具

| 工具 | 用途 |
|---|---|
| `RequestSelection` | 呈现单选/多选 + 自由文本提示并等待用户。 |
| `RequestConfirmation` | 请求显式用户确认；支持一次允许/会话内始终允许/拒绝。 |

> **已移除工具。** 旧版本文档列出的 `AlignNodes`、`DistributeNodes`、`AutoLayout`、`ArrangeNodes`、`BatchExecute`、`BulkPatchNodes`、`CloneNodes`、`DeleteNodes`、`DisconnectAllFromSlot`、`DisconnectAllFromNode`、`ReplaceConnection`、`CreateAndConfigureNode` **不再提供** —— `WorkflowAgentToolkitTests` 断言其不存在（显式检查 `AutoLayout`、`BatchExecute`、`CloneNodes`、`CreateAndConfigureNode`）。多节点布局改为逐节点 `MoveNode`/`SetNodePosition`；批量操作用 `ExecuteNodes`/循环变更。旧页的 `GetChanges` 在当前源码中为 `GetChangesSinceSnapshot`。
