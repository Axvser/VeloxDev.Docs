# Workflow Agent — Namespace: `VeloxDev.AI.Dashboard`

One view-model projects the whole agent into a bindable panel where each capability (workflow tools, skill tools, skills, MCP servers and their tools) can be switched on/off and its call activity watched. All types live in `VeloxDev.AI.Dashboard` (implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Dashboard/`).

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Dashboard/AgentDashboardViewModelTests` — 20 tests).

## AgentDashboardViewModel

`public sealed partial class AgentDashboardViewModel : IDisposable`. Private constructor; built with `Create`.

| Member | Type / Signature | Notes |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | The only way in. |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | Every workflow tool, with host-gating notes. |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | The skill tools (empty without skills). |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | MCP servers and their tools. |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | The discovered skills. |
| `SummaryText` | `string` | Header text. |
| `SystemToolSummary` / `SkillSummary` / `McpSummary` | `string` | Per-section aggregates. |
| `McpStatusText` | `string` | e.g. `存活 1 · 错误 0`. |
| `CanReloadMcp` | `bool` | Whether reload is meaningful. |
| `ReloadAllServersAsync` | `Task` | Reload every registered server (no-op when none). |
| `CallSummary` | `string` | Call activity. |
| `Rebuild` | `void` | Re-read the scope. |
| `Dispose` | `void` | Detach. |

## AgentMemberViewModel

`public abstract partial class AgentMemberViewModel` — the row base.

| Member | Type | Notes |
|---|---|---|
| `Name` / `Description` | `string` | Identity. |
| `IsEnabled` | `bool` | The checkbox (default `true`). |
| `StateText` / `Note` | `string` | Host-gating note (e.g. names `WithAllowNodeExecution`). |
| `CallCount` / `LastCalledText` | `int` / `string` | Activity. |
| `IsOff` / `IsReachable` / `HasBeenCalled` | `bool` | Derived. |
| `ActivityText` | `string` | Rendered activity. |
| `ApplyToScope` | `protected abstract void ApplyToScope(bool enabled)` | Push a switch. |

Four concrete rows:

| Type | Backs | Extra members |
|---|---|---|
| `ToolMemberViewModel` | a workflow / skill tool | — |
| `SkillMemberViewModel` | a skill | `SourceText`, `ResourceCount`, `HasResources`, `Sync(...)` |
| `McpServerMemberViewModel` | a server | `Tools`, `IsExpanded`, `ExpandGlyph`, `ToggleExpand()`, `RunModeText`, `LoadedToolCount`, `Error`, `IsConnected`, `IsWorking`, `IsFailed`, `HasError`, `IsFailedState`, `CanUnload`, `CanReload`, `UnloadAsync()`, `ReloadAsync()`, `Sync(...)` |
| `McpToolMemberViewModel` | one server tool | `DescribeServerState(...)` |

All four have `internal` constructors — external hosts go through `AgentDashboardViewModel.Create`.

## Related status models

The dashboard surfaces the subsystem status models, which are documented on their own namespaces' pages: `McpStatusViewModel` / `McpServerStatusViewModel` / `McpServerSummary` (MCP page), `SkillStatusViewModel` / `SkillsViewModel` / `SkillSummary` (Skills page), `SubAgentStatusViewModel` / `SubAgentTreeViewModel` (Sub-agents pages).

## Example

```text
// Source: Test — AgentDashboardViewModelTests
var dashboard = AgentDashboardViewModel.Create(scope);
dashboard.SystemTools.Select(t => t.Name)      // == scope.ProvideTools() names
dashboard.McpStatusText                        // "存活 1 · 错误 0" (1 alive, 0 failed)
dashboard.CanReloadMcp                         // false when no MCP scope is attached
```

**Expected result:** `ExecuteNode` shows `IsEnabled:true`, `IsReachable:false`, `Note` naming `WithAllowNodeExecution`; a refused tool is reported to the model and `CallCount` stays 0.
