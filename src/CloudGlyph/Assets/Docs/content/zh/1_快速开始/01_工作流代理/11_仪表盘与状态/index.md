# 11 · 仪表盘与状态

每个子系统都暴露可绑定的状态模型，而 `AgentDashboardViewModel` 这一个视图模型把整个 agent（workflow 工具、技能工具、技能、MCP 服务器）投影成一块面板，每个能力都能在其中开关，并观察其调用活动。

```csharp
using VeloxDev.AI.Dashboard;

var dashboard = AgentDashboardViewModel.Create(scope);
// 绑定 dashboard.SystemTools / SkillTools / Skills / McpServers / SummaryText
```

`Create` 是唯一入口（构造函数私有）。仪表盘跟随作用域：它订阅 `scope.Changed` 并在版本移动时重建；把复选框推回去会调用作用域（`SetToolEnabled`、`SkillScope.SetEnabled`、`McpScope.SetServerEnabled`/`SetToolEnabled`）。来源：`AgentDashboardViewModelTests`。

**预期结果：** `dashboard.SystemTools` 的名字等于 `scope.ProvideTools()`；在面板上翻转的开关在下一次渲染的 `scope.ProvideTools()` 中可见，而**面板之外**对作用域的改动也会回流到复选框。

## 1. `AgentDashboardViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | 在作用域上构建面板。 |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | 每个 workflow 工具，带宿主闸门说明。 |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | 四个技能工具（无技能时为空）。 |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | 已发现的技能。 |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | MCP 服务器及其工具。 |
| `SummaryText` / `SystemToolSummary` / `SkillSummary` / `McpSummary` | `string` | 标题用的聚合文本。 |
| `McpStatusText` / `CanReloadMcp` | `string` / `bool` | 如 `存活 1 · 错误 0`。 |
| `CallSummary` | `string` | 调用活动。 |
| `ReloadAllServersAsync` | `Task` | 重载每个已注册服务器（没有时为空操作，无 MCP 作用域时也安全）。 |
| `Rebuild` / `Dispose` | `void` | 重读作用域 / 解除挂接。 |

一行永远不会谎报可达性：`ExecuteNode` 显示 `IsEnabled:true` 但 `IsReachable:false`，并用 `Note` 点名 `WithAllowNodeExecution`；自由工具显示 `Note == ""`。被拒绝的调用会报告给模型，且**不**计为一次调用。来源：`AgentDashboardViewModelTests.SystemTools_ReportHostGating_SoAGreenRowIsNotALie`、`ARefusedTool_IsReportedToTheModel_AndDoesNotCountAsACall`。

## 2. 成员行

`AgentMemberViewModel` 是抽象基类（`Name`、`Description`、`IsEnabled`、`StateText`、`Note`、`CallCount`、`LastCalledText`、`IsOff`、`IsReachable`、`HasBeenCalled`、`ActivityText`；`ApplyToScope(bool)` 推送开关）。四个具体行：

| 类型 | 背后是 |
|---|---|
| `ToolMemberViewModel` | 作用域上的 workflow / 技能工具 |
| `SkillMemberViewModel` | 一个技能（`IsEnabled` → `SkillScope.SetEnabled`） |
| `McpServerMemberViewModel` | 一个服务器（`Tools`、`ToggleExpand`、`UnloadAsync`、`ReloadAsync`、`IsConnected`、`IsWorking`、`IsFailed`） |
| `McpToolMemberViewModel` | 服务器的一个工具（`SetToolEnabled(server, tool, …)`） |

**预期结果：** 取消勾选技能会把它从提示块中移除；取消勾选服务器会保持连接但去掉其工具；两者都无需重连即可恢复。

## 3. 子系统状态模型

| 类型 | 由谁暴露 | 要点 |
|---|---|---|
| `McpStatusViewModel` | `McpScope.Status` | `Servers`、`IsLoading`、`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`、`Snapshot`；`Track` / `SetLoading` / `Reset` |
| `McpServerStatusViewModel` | 上述的一行 | `State`（`McpServerStatus`）、`ToolCount`、`Error`、`IsEnabled`、`StateText` |
| `SkillsViewModel` | `SkillScope.Status` | `Skills`、`ActiveCount`、`ErrorCount`、`HasError`、`Snapshot` |
| `SkillStatusViewModel` | 上述的一行 | `State`（`SkillState`）、`Source`、`ResourceCount`、`IsEnabled`、`Error`、`StateText` |
| `SubAgentStatusViewModel` | `SubAgentScope.Children` | `State`、`StateText`、`CallCount`、`DurationText`、`TokensText`、授予计数 |
| `SubAgentTreeViewModel` | 由 `SubAgentScope` 构建 | 名册上的可绑定树 |

`SubAgentStatusViewModel.SetGranted*` 与 `McpScope.SetServerEnabled` 是面板播种与驱动它们的方式；这些都由 MVVM 源生成（`[VeloxProperty]`）并发出变更通知。

**预期结果：** `McpScope.Status.ConnectedCount` 实时跟随加载生命周期；`SubAgentStatusViewModel.StateText` 读作 `已完成` / `失败` / `已取消`（取消的子代理不会被画成失败）。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。`AgentDashboardViewModelTests` 存在且在 2026-10-01 的一次记录运行（387 项）中通过，但该运行早于权限模式重构，不作为当前证据。
