# 摘要与行

两种形状描述一个子代理：可从任意线程安全读取的不可变摘要，以及写于名册线程的可绑定行。它们分开是因为智能体调用与 UI 面板都在彼此无法控制的线程上读取。

## 枚举：SubAgentState

| 成员 | 含义 |
|---|---|
| `Queued` | 已创建，尚未运行。 |
| `Running` | 正在工作。 |
| `Completed` | 以结果完成。 |
| `Failed` | 以错误完成。 |
| `Cancelled` | 被有意停止。刻意区别于 `Failed`：被宿主或父级停止的子代理没有出错。 |

## 类：SubAgentSummary

一个子代理状态的不可变副本。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Id` | `string` | spawn 返回的句柄，其他工具都使用它。 |
| `Name` | `string` | 任务显示标题，或编号占位。 |
| `ParentId` | `string?` | 派生它的子代理 id；根作用域的直接子级为 `null`。 |
| `Depth` | `int` | 根作用域的直接子级为 1，孙级为 2。 |
| `Task` | `string` | spawn 被要求执行的任务。 |
| `State` | `SubAgentState` | 运行所处状态。 |
| `StateText` | `string` | 本地化状态文本。 |
| `Result` | `string?` | 完成后的答案；之前为 `null`。 |
| `Error` | `string?` | 失败原因，或 `null`。 |
| `CallCount` | `int` | 子代理及其派生的所有子代理所做的工具调用数。 |
| `MaxToolCalls` | `int?` | 授权的调用上限，或 `null`。 |
| `TokensUsed` | `long?` | 子代理自身花费，不是其子树。未测量时为 `null`。 |
| `InputTokens` / `OutputTokens` | `long?` | `TokensUsed` 拆分出的两半，若上报。 |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | 运行边界。 |
| `GrantedToolCount` | `int` | 实际给子代理的工具数。 |
| `GrantedSkillCount` | `int` | 给出的技能数；没有技能 provider 时为零。 |
| `GrantedMcpServerCount` | `int` | 给出的 MCP 服务器数；零是常态。 |
| `DroppedRequests` | `IReadOnlyList<string>` | spawn 请求而未获得的内容，每行一条。 |
| `IsRunning` | `bool` | 仍在运行。 |
| `IsFinished` | `bool` | 已完成，无论以何种方式。 |
| `HasError` | `bool` | 有值得显示的错误。 |
| `HasResult` | `bool` | 有值得显示的结果。 |
| `HasTokens` | `bool` | provider 上报了 token 数。`false` 表示「未测量」而非零。 |
| `Duration` | `TimeSpan?` | 子代理已运行多久，或仍在运行多久。实时测量；读取它，不要缓存。 |

## 类：SubAgentStatusViewModel

一个子代理作为可绑定行。`Id`、`ParentId` 与 `Depth` 在 spawn 时固定；授权列表填充一次且不再修改，因为改写运行中子代理被授予的内容会歪曲其历史。

### 生成属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 显示标题。 |
| `Task` | `string` | 任务。 |
| `State` | `SubAgentState` | 生命周期状态。 |
| `Result` | `string` | 答案。 |
| `Error` | `string` | 失败文本。 |
| `Notes` | `string` | spawn 备注。 |
| `CallCount` | `int` | 已做调用数。 |
| `MaxToolCalls` | `int?` | 授权上限。 |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | 运行边界。 |
| `TokensUsed` / `InputTokens` / `OutputTokens` | `long?` | 花费。 |
| `GrantedTools` / `GrantedSkills` / `GrantedMcpServers` | `ObservableCollection<string>` | 授权的名称。 |
| `DroppedRequests` | `ObservableCollection<string>` | 被拒绝的请求。 |

### 自有与计算成员

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Id` | `string` | 每个工具使用的句柄。 |
| `ParentId` | `string?` | 派生它的作用域 id，或 `null`。 |
| `Depth` | `int` | 树深度。 |
| `Transcript` | `AgentTranscript?` | 子代理自己的对话，一旦其作用域拥有。持有而非复制。 |
| `StateText` | `string` | 状态的展示文本。 |
| `IsRunning` / `IsFinished` | `bool` | 运行边界谓词。 |
| `HasError` / `HasResult` | `bool` | 展示谓词。 |
| `HasDroppedRequests` | `bool` | spawn 请求的某些内容被拒绝。 |
| `GrantedSummary` | `string` | 授权能力，每项一行。 |
| `Duration` | `TimeSpan?` | 实时已用时间。 |
| `DurationText` | `string` | 已用时间文本。 |
| `HasTokens` | `bool` | 是否上报了 token 数。 |
| `TokensText` | `string` | token 数文本；无则为空。 |
| `NotifyElapsed()` | `void NotifyElapsed()` | 通知绑定面板 `Duration` 与 `DurationText` 已变化。库不拥有计时器；宿主驱动时钟。 |

## 相关

- [树](../01_树/index.md) —— 在这些行之上的可绑定投影。
- [派发工具](../../01_派发工具/index.md) —— 填充它们的字段。
