# 工作流代理 — 命名空间：`VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit` 把一棵被作用域绑定的树转换为约 60 个 MAF `AITool` 实例（完整操作控制），并按 `WorkflowToolCategory` 分组；辅助类 `CommandInvoker`、`ComponentPatcher` 与 `TypeIntrospector` 支撑命令/补丁/模式工具。所有 JSON 输出均为 `Formatting.None`（紧凑）以节省 token；大多数工具返回带 `status: "ok" | "error" | "rejected"` 的对象（拒绝时附带 `reasons`、`hint`、`preferredAlternative`）。每个内置工具都被包装：调用时会按配置封送到 UI 上下文、计入上限、通过 `ToolCalled`/`WithToolCallCallback` 上报，并在启用时自动标脏。

实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/`。**证据：** **测试**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*`——工具经由公开的 `scope.ProvideTools()` 注册路径调用）+ **Demo**（`AgentHelper.ProvideAgent`）。

## WorkflowAgentToolkit

`public sealed class WorkflowAgentToolkit(WorkflowAgentScope scope)`。构造时 `scope` 为 null 抛 `ArgumentNullException`。每个工具包各持有一个基于被作用域绑定树的 `WorkflowStateTracker`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | 构造限定到给定类别标志的工具集。默认 `CreateTools()` = `CreateTools(All)`。在作用域上注册的自定义工具（`WithTools`/`WithQueryTools`）不受 `categories` 限制，始终包含。 |

## WorkflowToolCategory

`[Flags] public enum WorkflowToolCategory`——`CreateTools` 的工具组选择器。

| 标志 | 值 | 包含 |
|---|---|---|
| `Query` | `1 << 0` | 只读检查（20 个工具）。 |
| `Mutation` | `1 << 1` | 结构性图编辑（23 个工具）。 |
| `Execution` | `1 << 2` | 运行节点业务代码（6 个工具，受闸门）。 |
| `Command` | `1 << 3` | 泛型白名单命令执行（2 个工具，受闸门）。 |
| `Graph` | `1 << 4` | 遍历与寻路（5 个工具）。 |
| `Layout` | `1 << 5` | **保留**——无内置布局工具。 |
| `Analytics` | `1 << 6` | `GetNodeStatistics`。 |
| `State` | `1 << 7` | 快照与标脏（3 个工具）。 |
| `Composite` | `1 << 8` | **保留**——无组合/批量工具。 |
| `Interaction` | `1 << 9` | `RequestSelection` / `RequestConfirmation`——仅在已配置处理器且安全级别 > 0 时注册。 |
| `All` | 以上全部 | 所有类别。 |

`Layout` 与 `Composite` 按设计保留：多节点布局逐节点通过 `MoveNode`/`SetNodePosition` 完成，每个操作都是单个组件命令步骤，因此框架的撤销/重做栈始终是唯一事实来源，绝不会被绕过或双重提交。

## 工具清单（摘自 `CreateTools()`）

### Query——只读，20 个工具

| 工具 | 用途 |
|---|---|
| `ListNodes` | 紧凑节点列表 `[{i,id,t,x,y,l,w,h,slots,...props}]`；完整信息用 `GetNodeDetail`。 |
| `GetNodeDetail` | 按从零开始的索引取节点完整详情：属性、带连接的槽。 |
| `GetNodeDetailById` | 按运行时 ID 取节点完整详情（跨增删稳定）。 |
| `ListConnections` | 仅可见连接（紧凑，带连接 id）。 |
| `GetTypeSchema` | 按全名取某 .NET 类型的 JSON 模式（`TypeIntrospector`）。 |
| `GetWorkflowSummary` | 高层摘要：树 id/类型、节点/连接计数、不同节点类型。 |
| `GetComponentContext` | 按全名取某类型的 `[AgentContext]` 文档（`language` 为 `"English"`/`"Chinese"`）。 |
| `ListComponentCommands` | 某节点上的命令：名称 + 参数类型。 |
| `FindNodes` | 按类型名子串和/或属性值过滤节点。 |
| `ResolveSlotId` | 由其所属属性名（+ 集合索引）解析槽运行时 ID。 |
| `ListSlotProperties` | 命名单槽、槽集与 `SlotEnumerator` 属性，含 id/选择器/`allowedSelectorTypes`。 |
| `GetEnumSlotByValue` | 按枚举/bool 条件值取 `SlotEnumerator` 槽的运行时 ID。 |
| `GetLinkDetail` | 按运行时 ID 取连接完整详情（收发槽 + 父节点）。 |
| `ListCreatableTypes` | 可创建节点/槽类型（扫描已注册 + 树所属程序集）。 |
| `ValidateWorkflow` | 警告：零尺寸、孤立（有槽无连接）、无槽节点、重复连接。 |
| `GetFullTopology` | 一次调用取全图：节点 + 槽（属性名/id）+ 连接。 |
| `CompileWorkflow` | 对从起始节点可达的子图生成编译计划（Root 角色）。 |
| `CompileNodeResult` | 对某节点的祖先锥生成编译计划（Terminal 角色）。 |
| `GetCompileStatus` | 每个编译感知节点的当前编译身份（Order/ChainIndex/Offset/isStopped），不重编译。 |
| `GetExecutionLog` | 树的聚合直接执行日志（约定命名的 `ExecutionLog` 属性）。 |

### State——快照/差异/标脏，3 个工具

| 工具 | 用途 |
|---|---|
| `TakeSnapshot` | 取状态快照；仅返回 `version` + 汇总计数。 |
| `GetChangesSinceSnapshot` | 自上次快照以来的差异（增/删/改的节点与连接）。 |
| `MarkDirty` | 把树标脏——自动标脏关闭时，在变更任务结束时调用一次。 |

### Mutation——结构性变更，23 个工具

每个工具恰好执行一个组件命令（至多一个撤销条目；框架撤销/重做栈是权威）。

| 工具 | 用途 |
|---|---|
| `MoveNode` | 按相对偏移移动节点（`SetAnchorCommand`；不可撤销——镜像 GUI 拖拽）。 |
| `SetNodePosition` | 绝对位置/层级（`SetAnchorCommand`；不可撤销）。 |
| `ResizeNode` | 缩放（`SetSizeCommand`；不可撤销）。 |
| `DeleteNode` | 删除节点；级联删除子槽与连接（原子，一个撤销条目）。 |
| `DeleteSlot` | 删除槽及其连接。 |
| `ConnectSlots` | 按节点/槽下标连接（优先 `ConnectByProperty`）。 |
| `ConnectSlotsById` | 按槽运行时 ID 连接。 |
| `ConnectByProperty` | 按所属节点上的槽属性名连接（支持单槽/集合/`SlotEnumerator`）。 |
| `DisconnectSlots` | 按节点/槽下标移除连接。 |
| `DisconnectSlotsById` | 按槽运行时 ID 移除连接。 |
| `SetSlotChannel` | 更改槽的 `SlotChannel`。 |
| `SetEnumSlotChannel` | 按条件值设置 `SlotEnumerator` 槽的通道。 |
| `ConnectEnumSlot` | 将 `SlotEnumerator` 槽（按条件）连接到某槽/下标/枚举槽。 |
| `PatchNodeProperties` | 补丁节点的自定义属性（拒绝式补丁器）。 |
| `PatchComponentById` | 按运行时 ID 补丁任意组件的自定义属性。 |
| `CreateNode` | 经 `CreateNodeCommand` 创建节点；自动偏移避免重叠；尺寸为 0 时读取类型默认（`[DefaultSize]`，兜底 300×260）。 |
| `CreateSlotOnNode` | 经 `CreateSlotCommand` 创建动态槽（类型化槽属性由源生成器生成）。 |
| `AddSlotToCollection` | 经 `CreateSlotCommand` 向集合属性添加槽。 |
| `RemoveSlotFromCollection` | 按槽运行时 ID 从集合属性移除槽。 |
| `SetEnumSlotCollection` | 在既有节点上设置 `SlotEnumerator` 选择器（枚举/bool 类型名，或经 JSON + `nonEnumTypeName` 的非枚举 `ISlotProvider`）。 |
| `Undo` | 撤销上一个动作。 |
| `Redo` | 重做上一个被撤销的动作。 |
| `ClearHistory` | 丢弃撤销/重做历史而不触碰画布。 |

**连接拒绝。** 连接工具在派发后会校验连接是否确实出现在 `LinksMap` 中；框架可能静默拒绝（通道不兼容、同节点规则、`ValidateConnection`）。拒绝时返回 `status: "rejected"` 并附 `reasons`、`hint`，常含指出下一步应使用的属性路由工具的 `preferredAlternative`——切勿盲目重试。

### Execution——运行节点业务代码，6 个工具，受 `WithAllowNodeExecution` 闸门

闸门关闭时返回 `status: "error"` 与 “disabled by host policy” 消息。

| 工具 | 角色 | 用途 |
|---|---|---|
| `ExecuteNode` | 节点 EXEC | 执行某节点的 `ReceiveCommand` 并**等待**真正完成。 |
| `ExecuteNodes` | 节点 EXEC | 对 JSON 数组中的多个节点下标执行 `ReceiveCommand` 并逐个等待。 |
| `BroadcastNode` | 节点广播 | 执行 `BroadcastCommand`（下游派发为 fire-and-forget）；等待命令本身完成。 |
| `ReverseBroadcastNode` | 节点广播 | 执行 `ReverseBroadcastCommand`（触发上游 `ReceiveCommand`）；等待命令完成。 |
| `RunCompiledWorkflow` | 链 Root | 从起始节点编译并用引擎驱动整条链。 |
| `GetNodeResult` | Terminal 结果 | 从其祖先锥计算单个节点的结果。 |

### Command——泛型，2 个工具，受 `WithAllowedGenericCommands` 闸门

| 工具 | 用途 |
|---|---|
| `ExecuteCommandOnNode` | 按下标执行某节点上的任意（白名单）命令。 |
| `ExecuteCommandById` | 按运行时 ID 执行某组件（节点/槽/连接）上的任意（白名单）命令。 |

### Graph——遍历，5 个工具

| 工具 | 用途 |
|---|---|
| `SearchForward` | BFS 下游（可选类型名过滤、最大深度）。 |
| `SearchReverse` | BFS 上游。 |
| `SearchAllRelative` | BFS 双向。 |
| `IsConnected` | 直接/传递连接检查（`forward`/`reverse`/`any`）。 |
| `FindPath` | 最短前向路径（BFS）；有序 `{i,id,t}` 列表或为空。 |

### Analytics——1 个工具

| 工具 | 用途 |
|---|---|
| `GetNodeStatistics` | 入度/出度/总连接数/相连节点 id/槽利用率。 |

### Interaction——2 个工具，仅在已配置处理器且安全级别 > 0 时注册

| 工具 | 用途 |
|---|---|
| `RequestSelection` | 呈现单选/多选 + 自由文本并等待用户；返回 `chosen`（单选）或 `chosenList`（多选）及 `freeText`。 |
| `RequestConfirmation` | 请求显式确认；允许一次 / 本会话始终允许 / 拒绝。 |

## Root 与 Terminal 编译语义

编译与链运行工具是 Agent 对 `VeloxDev.Core.WorkflowSystem.CompilerEx` 引擎的视图。底层引擎：`new CompilerViewModel().CompileAsync(node, CompileRole)` 之后 `new RuntimeEngine().RunAsync(graph, runtimeContext, ct)`——**不是**旧的 `CompilerEngine`/`CompileToAsync` API。两种编译角色对应两个入口：

| | `CompileWorkflow`（计划）/ `RunCompiledWorkflow`（运行） | `CompileNodeResult`（计划）/ `GetNodeResult`（运行） |
|---|---|---|
| 角色 | `CompileRole.Root`——起始节点是控制器/入口。 | `CompileRole.Terminal`——该节点是结果末端。 |
| 范围 | 编译自起始节点向下游可达的子图。 | 反向编译该节点的**祖先锥**：从其输入槽回溯喂给它的上游生产者；无需控制器，锥的入口前沿自动推导。 |
| 运行时目标 | 整链运行；`context.Target` 为 null。 | `context.Target = node`；只驱动该锥并上报节点结果。 |
| 输出 | `role`、`runStatus`（`Completed`/`Stopped`）、`endedWithError`、`attempts`、`data`、`logs`。 | 同构**且**多出 `targetReached`（仅 Terminal 存在）。 |
| 分支语义 | 静态剪枝：不在任何活跃分支上的下游节点得到 `Order = -1`（绝对停止）。 | 锥内路由器保持**真实**的 `BranchSegment` 选择——只编译通向该节点的分支（兄弟分支缺席，而非 `Order = -1`）。若同一路由器的多条路由键都到达该节点，编译返回错误（一次前向运行只能取一条分支）。 |

**Terminal 错误契约。** 若锥上的某路由器在运行时实际选择了**兄弟**分支，目标不会被驱动：`GetNodeResult` 返回 `status: "error"` 并带指名目标的 `message`（`"... was NOT reached ... No result was produced."`），且无数据——切勿把其它分支的最终载荷当作该节点的结果。先把路由器指向通向该节点的分支（`PatchNodeProperties`/`SetEnumSlotCollection`）再重试。节点被驱动时返回 `targetReached: true`。

编译会把编译身份附着到锥/链的 `ICompileTimeAware` 节点上；随后可用 `GetCompileStatus` 读取身份而无需重编译。`RunCompiledWorkflow` 采用编译步骤语义——节点以 `IRuntimeContext` 会话运行 `ReceiveAsync` 且**不**自动广播；下游派发由引擎负责。`GetExecutionLog` 返回树的*直接*（非编译）执行日志；编译运行会话日志请用运行工具的 `logs` 字段。

## 辅助类

### CommandInvoker

`public static class CommandInvoker`——发现并调用工作流组件上的 `IVeloxCommand` 属性；支撑 `ListComponentCommands`、`ExecuteCommandOnNode`、`ExecuteCommandById`。把 JSON 参数反序列化为 `[AgentCommandParameter]` 声明的类型。

| 成员 | 签名 | 说明 |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object component)` | `ICommand` 类型属性——先接口属性（属性权威），再具体类型自身（去重）。 |
| `Invoke` | `string Invoke(object component, string commandName, string? jsonParameter)` | 执行命名命令并返回 JSON；缺 `"Command"` 后缀时自动补齐。 |

`CommandDescriptor`（`Name`、`ParameterType`（`Type?`）、`Descriptions` 为 `IReadOnlyList<KeyValuePair<AgentLanguages, string>>`）声明于本文件。

### ComponentPatcher

`public static class ComponentPatcher`——按可写公开属性把 JSON 补丁对象应用到组件。支撑 `PatchNodeProperties`/`PatchComponentById`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ApplyPatch` | `string ApplyPatch(object target, string jsonPatch)` | 应用 `{"Prop": value}`。对框架托管属性（`Parent`、`Nodes`、`Links`、`LinksMap`、`Slots`、`Targets`、`Sources`、`State`、`VirtualLink`、`RuntimeId`、`Helper`）、命令后备属性（引导至其后备命令）、槽类型与 `[SlotSelectors]` 标记属性给出 `rejected`/`skipped` + `reason`；对未挂载进树（无父链）的目标报错；`Type` 属性经 `TypeIntrospector` 解析类型名。直接写入刻意不可撤销（撤销是 Core 命令管线的职责）。 |
| `ApplyPatchWithUndo` | `string ApplyPatchWithUndo(object target, string jsonPatch, IWorkflowTreeViewModel? tree = null)` | 向后兼容别名 → `ApplyPatch`（忽略 `tree`）。 |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target)` | 复制可写标量/枚举属性，跳过命令/槽/框架托管属性。 |

### TypeIntrospector

`public static class TypeIntrospector`——供 Agent 消费的类型解析与 JSON 模式；支撑 `GetTypeSchema`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ResolveType` | `Type? ResolveType(string fullTypeName)` | 委托给 `AgentTypeResolver.ResolveType`。 |
| `GetTypeSchema` | `string GetTypeSchema(Type type)` | 缩进 JSON：`fullName`、`kind`（enum/interface/struct/class）、`baseType`、`interfaces`、枚举 `values` 或属性列表（`name`/`type`/`canRead`/`canWrite`），外加跨语言的 `developerInstructions`（`[AgentContext]`）与可构造默认实例时的 `defaultJson_runtimeOnly`。 |
