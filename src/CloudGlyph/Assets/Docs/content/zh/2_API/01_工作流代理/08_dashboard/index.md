# 工作流代理 —— 命名空间：`VeloxDev.AI.Dashboard`

一个视图模型把整个 agent 投影成一个可绑定面板，在其中可开关每项能力（workflow 工具、技能工具、技能、MCP 服务器及其工具）并观察其调用活动。所有类型位于 `VeloxDev.AI.Dashboard`（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Dashboard/`）。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Dashboard/AgentDashboardViewModelTests` —— 20 个测试）。

## AgentDashboardViewModel

`public sealed partial class AgentDashboardViewModel : IDisposable`。构造函数私有；用 `Create` 构建。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | 唯一入口。 |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | 每个 workflow 工具，带宿主闸门说明。 |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | 技能工具（无技能时为空）。 |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | MCP 服务器及其工具。 |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | 已发现的技能。 |
| `SummaryText` | `string` | 标题文本。 |
| `SystemToolSummary` / `SkillSummary` / `McpSummary` | `string` | 分区聚合。 |
| `McpStatusText` | `string` | 如 `存活 1 · 错误 0`。 |
| `CanReloadMcp` | `bool` | 重载是否有意义。 |
| `ReloadAllServersAsync` | `Task` | 重载每个已注册服务器（无服务器时为空操作）。 |
| `CallSummary` | `string` | 调用活动。 |
| `Rebuild` | `void` | 重读作用域。 |
| `Dispose` | `void` | 解除订阅。 |

## AgentMemberViewModel

`public abstract partial class AgentMemberViewModel` —— 行基类。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` / `Description` | `string` | 身份。 |
| `IsEnabled` | `bool` | 复选框（默认 `true`）。 |
| `StateText` / `Note` | `string` | 宿主闸门说明（如点名 `WithAllowNodeExecution`）。 |
| `CallCount` / `LastCalledText` | `int` / `string` | 活动。 |
| `IsOff` / `IsReachable` / `HasBeenCalled` | `bool` | 派生。 |
| `ActivityText` | `string` | 渲染的活动文本。 |
| `ApplyToScope` | `protected abstract void ApplyToScope(bool enabled)` | 推送开关。 |

四个具体行：

| 类型 | 背后的对象 | 额外成员 |
|---|---|---|
| `ToolMemberViewModel` | 一个 workflow / 技能工具 | — |
| `SkillMemberViewModel` | 一个技能 | `SourceText`、`ResourceCount`、`HasResources`、`Sync(...)` |
| `McpServerMemberViewModel` | 一个服务器 | `Tools`、`IsExpanded`、`ExpandGlyph`、`ToggleExpand()`、`RunModeText`、`LoadedToolCount`、`Error`、`IsConnected`、`IsWorking`、`IsFailed`、`HasError`、`IsFailedState`、`CanUnload`、`CanReload`、`UnloadAsync()`、`ReloadAsync()`、`Sync(...)` |
| `McpToolMemberViewModel` | 某个服务器工具 | `DescribeServerState(...)` |

四者的构造函数都是 `internal` —— 外部宿主经 `AgentDashboardViewModel.Create`。

## 相关状态模型

仪表盘呈现子系统状态模型，它们记录在各自命名空间的页面：`McpStatusViewModel` / `McpServerStatusViewModel` / `McpServerSummary`（MCP 页）、`SkillStatusViewModel` / `SkillsViewModel` / `SkillSummary`（技能页）、`SubAgentStatusViewModel` / `SubAgentTreeViewModel`（子代理页）。

## 示例

```text
// Source: Test — AgentDashboardViewModelTests
var dashboard = AgentDashboardViewModel.Create(scope);
dashboard.SystemTools.Select(t => t.Name)      // == scope.ProvideTools() 的名字
dashboard.McpStatusText                        // "存活 1 · 错误 0"（1 存活，0 错误）
dashboard.CanReloadMcp                         // 未挂载 MCP 作用域时为 false
```

**预期结果：** `ExecuteNode` 显示 `IsEnabled:true`、`IsReachable:false`，`Note` 点名 `WithAllowNodeExecution`；被拒绝的工具会报告给模型，`CallCount` 保持 0。
