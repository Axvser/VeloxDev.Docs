# 11 · Dashboard & Status

Every subsystem exposes a bindable status model, and one view-model — `AgentDashboardViewModel` — projects the whole agent (workflow tools, skill tools, skills, MCP servers) into a single panel where each capability can be switched on and off and its call activity watched.

```csharp
using VeloxDev.AI.Dashboard;

var dashboard = AgentDashboardViewModel.Create(scope);
// bind dashboard.SystemTools / SkillTools / Skills / McpServers / SummaryText
```

`Create` is the only way in (the constructor is private). The dashboard follows the scope: it subscribes to `scope.Changed` and rebuilds when the version moves, and pushing a checkbox back calls into the scope (`SetToolEnabled`, `SkillScope.SetEnabled`, `McpScope.SetServerEnabled`/`SetToolEnabled`). Source: `AgentDashboardViewModelTests`.

**Expected result:** `dashboard.SystemTools` names equal `scope.ProvideTools()`; a switch flipped on the panel is visible in `scope.ProvideTools()` on the next render, and a scope change made **off** the panel flows back to the checkbox.

## 1. `AgentDashboardViewModel`

| Member | Type | Notes |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | Builds the panel over a scope. |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | Every workflow tool, with host-gating notes. |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | The four skill tools (empty without skills). |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | The discovered skills. |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | The MCP servers and their tools. |
| `SummaryText` / `SystemToolSummary` / `SkillSummary` / `McpSummary` | `string` | Aggregate text for headers. |
| `McpStatusText` / `CanReloadMcp` | `string` / `bool` | e.g. `存活 1 · 错误 0`. |
| `CallSummary` | `string` | Call activity. |
| `ReloadAllServersAsync` | `Task` | Reloads every registered server (a no-op when none, and safe without an MCP scope). |
| `Rebuild` / `Dispose` | `void` | Re-read the scope / detach. |

A row never lies about reachability: `ExecuteNode` shows `IsEnabled:true` but `IsReachable:false` with a `Note` naming `WithAllowNodeExecution`, while a free tool shows `Note == ""`. A refused call is reported to the model and does **not** count as a call. Source: `AgentDashboardViewModelTests.SystemTools_ReportHostGating_SoAGreenRowIsNotALie`, `ARefusedTool_IsReportedToTheModel_AndDoesNotCountAsACall`.

## 2. Member rows

`AgentMemberViewModel` is the abstract base (`Name`, `Description`, `IsEnabled`, `StateText`, `Note`, `CallCount`, `LastCalledText`, `IsOff`, `IsReachable`, `HasBeenCalled`, `ActivityText`; `ApplyToScope(bool)` pushes a switch). Four concrete rows:

| Type | Backs |
|---|---|
| `ToolMemberViewModel` | a workflow / skill tool on the scope |
| `SkillMemberViewModel` | a skill (`IsEnabled` → `SkillScope.SetEnabled`) |
| `McpServerMemberViewModel` | a server (`Tools`, `ToggleExpand`, `UnloadAsync`, `ReloadAsync`, `IsConnected`, `IsWorking`, `IsFailed`) |
| `McpToolMemberViewModel` | one server tool (`SetToolEnabled(server, tool, …)`) |

**Expected result:** unchecking a skill removes its text from the prompt block; unchecking a server keeps it connected but drops its tools; both are reversible without a reconnect.

## 3. Subsystem status models

| Type | Exposed by | Highlights |
|---|---|---|
| `McpStatusViewModel` | `McpScope.Status` | `Servers`, `IsLoading`, `ConnectedCount`, `ErrorCount`, `WorkingCount`, `IsAllReady`, `HasError`, `Snapshot`; `Track` / `SetLoading` / `Reset` |
| `McpServerStatusViewModel` | one row of the above | `State` (`McpServerStatus`), `ToolCount`, `Error`, `IsEnabled`, `StateText` |
| `SkillsViewModel` | `SkillScope.Status` | `Skills`, `ActiveCount`, `ErrorCount`, `HasError`, `Snapshot` |
| `SkillStatusViewModel` | one row of the above | `State` (`SkillState`), `Source`, `ResourceCount`, `IsEnabled`, `Error`, `StateText` |
| `SubAgentStatusViewModel` | `SubAgentScope.Children` | `State`, `StateText`, `CallCount`, `DurationText`, `TokensText`, granted counts |
| `SubAgentTreeViewModel` | built from a `SubAgentScope` | the bindable tree over the rosters |

`SubAgentStatusViewModel.SetGranted*` and `McpScope.SetServerEnabled` are how the panel seeds and drives them; all of these are MVVM-source-generated (`[VeloxProperty]`) and raise change notifications.

**Expected result:** `McpScope.Status.ConnectedCount` tracks the load lifecycle live; `SubAgentStatusViewModel.StateText` reads `已完成` / `失败` / `已取消` (a cancelled child is not painted as a failure).

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite (2026-10-01, `已通过! 失败: 0，通过: 387`) includes `Dashboard/AgentDashboardViewModelTests` (20 tests), covering tool gating notes, the checkbox round-trip, call counts across slices, skill and MCP convergence, and off-thread change marshalling.
