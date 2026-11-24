# WorkflowAgentToolkit

`VeloxDev.AI.Workflow.Functions.WorkflowAgentToolkit` 提供 MAF 兼容的 `AITool` 实例，让智能体对一个 `WorkflowAgentScope` 树拥有完整操作能力。通过 `scope.CreateToolkit()` 获取；每个作用域只有一个实例，因为它持有调用账本与快照历史。

## 类：WorkflowAgentToolkit

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `WorkflowAgentToolkit(WorkflowAgentScope scope)` | 为持有会话工具调用额度的作用域创建 toolkit。 |
| CreateTools | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | 返回所选分组的内置工具及所有自定义工具，省略被 `WithToolEnabled` 关闭的工具。 |

每个内置工具都是被跟踪函数包装的 `AIFunction`，因此调用会被编组到作用域上下文、计入预算、通过 `ToolCalled` 上报，并在启用时把树标记为脏。不是 `AIFunction` 的自定义工具原样加入，不获得这些能力。

`CreateTools` 是决定哪些工具到达模型的唯一节点。被关闭的工具无论请求哪个分类都会省略，因此开关不会在一条路径上生效而在另一条上被忽略。

## 枚举：WorkflowToolCategory

`VeloxDev.AI.Workflow.Functions` 中的 `[Flags]` 枚举。它是**表面过滤器**——决定哪些分组发送给模型——调用时从不查询。调用期权限是另一个分类，即[智能体安全与预算](../../18_智能体安全与预算/index.md)中的 `AgentActionCategory`。

| 成员 | 值 | 注册 |
|---|---|---|
| `Query` | `1 << 0` | 只读检查 |
| `Mutation` | `1 << 1` | 结构图编辑 |
| `Execution` | `1 << 2` | 节点与链执行 |
| `Command` | `1 << 3` | 通用命令调用 |
| `Graph` | `1 << 4` | 遍历与路径查询 |
| `Layout` | `1 << 5` | 布局检查、预览与应用 |
| `Analytics` | `1 << 6` | 节点统计 |
| `State` | `1 << 7` | 快照、差异与脏标记 |
| `Composite` | `1 << 8` | 保留；不注册工具 |
| `Interaction` | `1 << 9` | 选择、确认与模式切换 |
| `All` | 所有标志的并集 | 每个分组 |

## 工具目录

下表列出模型看到的工具名。它们的签名是面向模型的 JSON schema，不是 C# 签名；快速开始展示了实时调用。

### Query

`ListNodes`、`GetNodeDetail`、`GetNodeDetailById`、`ListConnections`、`GetTypeSchema`、`GetWorkflowSummary`、`GetComponentContext`、`ListComponentCommands`、`FindNodes`、`ResolveSlotId`、`ListSlotProperties`、`GetEnumSlotByValue`、`GetLinkDetail`、`ListCreatableTypes`、`ValidateWorkflow`、`GetFullTopology`、`CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`、`GetExecutionLog`、`SerializeWorkflow`、`LocateNode`、`LocateSlot`、`LocateLink`、`ListCompiledRuns`

### Mutation

`MoveNode`、`SetNodePosition`、`ResizeNode`、`DeleteNode`、`DeleteSlot`、`ConnectSlots`、`ConnectSlotsById`、`ConnectByProperty`、`DisconnectSlots`、`DisconnectSlotsById`、`SetSlotChannel`、`SetEnumSlotChannel`、`ConnectEnumSlot`、`PatchNodeProperties`、`PatchComponentById`、`CreateNode`、`CreateSlotOnNode`、`AddSlotToCollection`、`RemoveSlotFromCollection`、`SetEnumSlotCollection`、`Undo`、`Redo`、`ClearHistory`、`LoadWorkflow`、`ClearFinishedRuns`

每个变更工具恰好执行一个组件命令，因此 Core 的撤销/重做栈始终是事实源。不存在打包的多步手势。

### Execution

`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow`、`GetNodeResult`、`StartCompiledWorkflow`、`ContinueCompiledWorkflow`、`GetCompiledRunStatus`、`PauseCompiledRun`、`ResumeCompiledRun`、`StopCompiledRun`

节点执行工具（`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`）会运行任意业务代码，在 `WithAllowNodeExecution(true)` 之前一律拒绝。

### Command

`ExecuteCommandOnNode`、`ExecuteCommandById`

在 `WithAllowedGenericCommands(...)` 列出允许的命令之前一律拒绝。

### Graph

`SearchForward`、`SearchReverse`、`SearchAllRelative`、`IsConnected`、`FindPath`

### Layout

`GetLayoutInfo`、`PreviewLayout`、`ArrangeLayout`

`PreviewLayout` 以 dry-run 方式使用已注册的 `IWorkflowLayoutSolver`；`ArrangeLayout` 通过与 GUI 相同的路径应用它。

### Analytics

`GetNodeStatistics`

### State

`TakeSnapshot`、`GetChangesSinceSnapshot`、`MarkDirty`

### Interaction

| 工具 | 注册条件 |
|---|---|
| `RequestSelection` | 给了 `WithSelectionHandler` 处理器 |
| `RequestConfirmation` | 给了 `WithConfirmationHandler` 处理器 |
| `EnterPlanMode`、`ExitPlanMode` | 存在确认处理器时 |

交互工具从不会被权限模式阻止。询问是计划获得同意的方式，移除它们的模式会让智能体只能拒绝。

### 始终提供

`ResetToolCallLimit` 在每个模式下注册，且从不会被 `WithToolEnabled` 过滤。它是宿主退出调用预算的方式；在预算耗尽时恰好隐藏它会让它毫无用处。

## 示例

```csharp
using VeloxDev.AI.Workflow.Functions;

var toolkit = scope.CreateToolkit();
foreach (var tool in toolkit.CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine(tool.Name);
```

这会按注册顺序打印 25 个查询工具名。

## 相关

- [WorkflowAgentScope](../00_工作流作用域/index.md) —— 持有 toolkit 的作用域。
- [智能体安全与预算](../../18_智能体安全与预算/index.md) —— `AgentActionCategory` 与调用期闸门。
- [工作流智能体工具快速开始](../../../1_快速开始/17_工作流智能体工具/index.md) —— 同一批工具在真实对话中的用法。
