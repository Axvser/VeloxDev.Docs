# 11 · 仪表盘与状态

每个子系统都暴露一个可绑定状态模型，而一个视图模型 —— `AgentDashboardViewModel` —— 把整个 agent（workflow 工具、技能工具、技能、MCP 服务器）投影到一个面板，在其中可开关每项能力并观察其调用活动。

```csharp
using VeloxDev.AI.Dashboard;

var dashboard = AgentDashboardViewModel.Create(scope);
// 绑定 dashboard.SystemTools / SkillTools / Skills / McpServers / SummaryText
```

`Create` 是唯一入口（构造函数为私有）。仪表盘跟随作用域：它订阅 `scope.Changed` 并在版本移动时重建，把复选框推回时会调用作用域（`SetToolEnabled`、`SkillScope.SetEnabled`、`McpScope.SetServerEnabled`/`SetToolEnabled`）。来源：`AgentDashboardViewModelTests`。

**预期结果：** `dashboard.SystemTools` 的名字与 `scope.ProvideTools()` 一致；在面板上翻转的开关在下一次渲染时于 `scope.ProvideTools()` 中可见，而在面板**之外**做的作用域改动会回流到复选框。

## 1. `AgentDashboardViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | 在某个作用域上构建面板。 |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | 每个 workflow 工具，带宿主闸门说明。 |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | 四个技能工具（无技能时为空）。 |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | 已发现的技能。 |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | MCP 服务器及其工具。 |
| `SummaryText` / `SystemToolSummary` / `SkillSummary` / `McpSummary` | `string` | 标题用的聚合文本。 |
| `McpStatusText` / `CanReloadMcp` | `string` / `bool` | 如 `存活 1 · 错误 0`。 |
| `CallSummary` | `string` | 调用活动。 |
| `ReloadAllServersAsync` | `Task` | 重载每个已注册服务器（无服务器时为空操作，无 MCP 作用域时也安全）。 |
| `Rebuild` / `Dispose` | `void` | 重读作用域 / 解除订阅。 |

一行绝不谎报可达性：`ExecuteNode` 显示 `IsEnabled:true` 但 `IsReachable:false`，其 `Note` 点名 `WithAllowNodeExecution`；而一个自由工具显示 `Note == ""`。被拒绝的调用会报告给模型，且**不**计为一次调用。来源：`AgentDashboardViewModelTests.SystemTools_ReportHostGating_SoAGreenRowIsNotALie`、`ARefusedTool_IsReportedToTheModel_AndDoesNotCountAsACall`。

## 2. 成员行

`AgentMemberViewModel` 是抽象基类（`Name`、`Description`、`IsEnabled`、`StateText`、`Note`、`CallCount`、`LastCalledText`、`IsOff`、`IsReachable`、`HasBeenCalled`、`ActivityText`；`ApplyToScope(bool)` 推送开关）。四个具体行：

| 类型 | 背后的对象 |
|---|---|
| `ToolMemberViewModel` | 作用域上的一个 workflow / 技能工具 |
| `SkillMemberViewModel` | 一个技能（`IsEnabled` → `SkillScope.SetEnabled`） |
| `McpServerMemberViewModel` | 一个服务器（`Tools`、`ToggleExpand`、`UnloadAsync`、`ReloadAsync`、`IsConnected`、`IsWorking`、`IsFailed`） |
| `McpToolMemberViewModel` | 某个服务器工具（`SetToolEnabled(server, tool, …)`） |

**预期结果：** 取消勾选技能会从提示块中移除其文本；取消勾选服务器会让它保持连接但丢弃其工具；两者都可无需重连地还原。

## 3. 子系统状态模型

| 类型 | 由谁暴露 | 要点 |
|---|---|---|
| `McpStatusViewModel` | `McpScope.Status` | `Servers`、`IsLoading`、`ConnectedCount`、`ErrorCount`、`WorkingCount`、`IsAllReady`、`HasError`、`Snapshot`；`Track` / `SetLoading` / `Reset` |
| `McpServerStatusViewModel` | 上者的某一行 | `State`（`McpServerStatus`）、`ToolCount`、`Error`、`IsEnabled`、`StateText` |
| `SkillsViewModel` | `SkillScope.Status` | `Skills`、`ActiveCount`、`ErrorCount`、`HasError`、`Snapshot` |
| `SkillStatusViewModel` | 上者的某一行 | `State`（`SkillState`）、`Source`、`ResourceCount`、`IsEnabled`、`Error`、`StateText` |
| `SubAgentStatusViewModel` | `SubAgentScope.Children` | `State`、`StateText`、`CallCount`、`DurationText`、`TokensText`、授予计数 |
| `SubAgentTreeViewModel` | 由一个 `SubAgentScope` 构建 | 名册之上的可绑定树 |

`SubAgentStatusViewModel.SetGranted*` 与 `McpScope.SetServerEnabled` 是面板播种与驱动它们的方式；这些都是 MVVM 源生成的（`[VeloxProperty]`）并会触发变更通知。

**预期结果：** `McpScope.Status.ConnectedCount` 实时跟随加载生命周期；`SubAgentStatusViewModel.StateText` 读作 `已完成` / `失败` / `已取消`（被取消的子代理不会被涂成失败）。

## 运行声明

- ✅ 实际构建并运行 —— 确定性 agent 测试套件（2026-10-01，`已通过! 失败: 0，通过: 387`）包含 `Dashboard/AgentDashboardViewModelTests`（20 个测试），覆盖工具闸门说明、复选框往返、跨切片的调用计数、技能与 MCP 收敛，以及跨线程变更编组。
