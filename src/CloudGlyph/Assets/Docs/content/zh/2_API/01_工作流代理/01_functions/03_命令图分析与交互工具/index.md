# 函数 · 命令、图、分析与交互工具

## Command —— 通用白名单执行（2）

受 `WithAllowedGenericCommands(...)` 闸控。从不调用 ⇒ 通用命令执行被完全禁用（安全默认）；未列出的命令返回错误，要求宿主加入白名单。

| 工具 | 签名 | 用途 |
|---|---|---|
| `ExecuteCommandOnNode` | `ExecuteCommandOnNode(int nodeIndex, string commandName, string? jsonParameter = null)` | 按索引在节点上执行白名单命令。用 `ListComponentCommands` 发现命令。 |
| `ExecuteCommandById` | `ExecuteCommandById(string runtimeId, string commandName, string? jsonParameter = null)` | 同上，作用于按运行时 ID 的任意组件（节点/槽/链接）。 |

背后是 `CommandInvoker.Invoke`；JSON 参数被反序列化为 `[AgentCommandParameter]` 声明的类型。

## Graph —— 遍历与寻路（5）

| 工具 | 签名 | 用途 |
|---|---|---|
| `SearchForward` | `SearchForward(int nodeIndex, string? typeName = null, int maxDepth = 0)` | 下游 BFS；可选类型名子串过滤；`0` = 不限深度。 |
| `SearchReverse` | `SearchReverse(int nodeIndex, string? typeName = null, int maxDepth = 0)` | 上游 BFS。 |
| `SearchAllRelative` | `SearchAllRelative(int nodeIndex, string? typeName = null, int maxDepth = 0)` | 双向 BFS。 |
| `IsConnected` | `IsConnected(int sourceNodeIndex, int targetNodeIndex, string direction = "forward")` | 直接/传递连通检查；`direction` = `"forward"` / `"reverse"` / `"any"`。 |
| `FindPath` | `FindPath(int sourceNodeIndex, int targetNodeIndex)` | 最短前向路径（BFS）；有序 `{i,id,t}` 列表或空。 |

五个都是只读查询（永不标脏）。

## Analytics（1）

| 工具 | 签名 | 用途 |
|---|---|---|
| `GetNodeStatistics` | `GetNodeStatistics(int nodeIndex)` | 入度、出度、总连接数、相连节点 id、槽利用率。 |

## Interaction（至多 4）

注册完全取决于处理器是否存在 —— 已无安全级别。两个交互工具都是 `AgentActionCategory.Interact`，任何权限模式都不会把它们交给用户；计划模式的一对在旁边注册，并经同一个确认处理器询问。

| 工具 | 注册条件 | 签名 | 用途 |
|---|---|---|---|
| `RequestSelection` | 调用了 `WithSelectionHandler` | `RequestSelection(string prompt, string optionsJson, string freeTextPrompt, bool allowMultiSelect = false)` | 呈现单选/多选 + 自由文本框并等待用户。返回 `chosen`（单选）/ `chosenList`（多选）+ `freeText`。 |
| `RequestConfirmation` | 调用了 `WithConfirmationHandler` | `RequestConfirmation(string operationKey, string description)` | 请求显式确认：仅此一次 / 本会话始终 / 拒绝。被拒则不要继续。 |
| `EnterPlanMode` | 调用了 `WithConfirmationHandler` | `EnterPlanMode()` | 先询问用户，再把会话切到 `AgentPermissionMode.Plan`，并记住要恢复的模式。 |
| `ExitPlanMode` | 调用了 `WithConfirmationHandler` | `ExitPlanMode()` | 先询问用户，再恢复进入 `Plan` 前的模式。 |

`RequestSelection` 由 `WorkflowAgentScope.WithSelectionHandler` 支撑；`RequestConfirmation` 由 `WithConfirmationHandler` 支撑。确认处理器的键在 `Ask` 权限决定中是工具名，在本工具中是模型给出的 `operationKey`。`ResetToolCallLimit` 也以 `extend-tool-call-budget` 询问。

## 示例

```text
// Source: Test — ComposedProvidersTests / BudgetResetTests
SearchForward(nodeIndex: 0)                          → {"nodes":[{"i":1,"id":"...","t":"..."}]}
GetNodeStatistics(nodeIndex: 0)                      → {"inDegree":1,"outDegree":1,"totalConnections":2,...}
ExecuteCommandOnNode(0, "ReceiveCommand", null)      → {"status":"ok"}   // 已加入白名单时
RequestConfirmation("delete-all-nodes", "Delete every node") → {"status":"denied"|...}
```

**预期结果：** 未加入任何通用命令白名单时 `ExecuteCommandOnNode` 返回错误；两个处理器都配置时 `RequestSelection` / `RequestConfirmation` / `EnterPlanMode` / `ExitPlanMode` 在 `ProvideTools()` 中各出现一次。
