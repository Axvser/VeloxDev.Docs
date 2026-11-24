# Dashboard

`VeloxDev.AI.Dashboard.AgentDashboardViewModel` is the host-facing panel over one `WorkflowAgentScope`: what the agent can currently do, how busy each piece is, and a switch per member. Each row is a projection, never a second source of truth.

## Class: AgentDashboardViewModel

| Member | Type / Signature | Description |
|---|---|---|
| `Create` | `static AgentDashboardViewModel Create(WorkflowAgentScope scope)` | Builds the panel over a scope. The scope need not be configured first; later `With*` calls reach the panel through `Changed`. |
| `SystemTools` | `ObservableCollection<ToolMemberViewModel>` | The workflow built-ins plus developer-registered tools. |
| `SkillTools` | `ObservableCollection<ToolMemberViewModel>` | The four skill-management tools. |
| `McpServers` | `ObservableCollection<McpServerMemberViewModel>` | One row per configured server, each expandable to its tools. |
| `Skills` | `ObservableCollection<SkillMemberViewModel>` | Every discovered skill. |
| `SubAgents` | `ObservableCollection<SubAgentStatusViewModel>` | The children this session dispatched, when the subsystem is attached. |
| `SystemToolSummary` | `string` | Tools switched on over tools offered. |
| `SkillSummary` | `string` | Skills switched on over skills discovered. |
| `McpSummary` | `string` | Servers connected over servers configured. |
| `SubAgentSummary` | `string` | Sub-agents still running over sub-agents dispatched. |
| `McpStatusText` | `string` | Alive / failed split, counted from each server's exclusive state. |
| `CanReloadMcp` | `bool` | Whether no server is mid-connect, so a reload would not fight one in flight. |
| `ReloadAllServersAsync()` | `Task ReloadAllServersAsync()` | Reconnects every server the host registered. |
| `CallSummary` | `string` | Connected, switched-off and stopwatch-fallback counts. |
| `Rebuild()` | `void Rebuild()` | Re-reads every member from the scope. Public so a host can force a pass after changing the scope directly. |
| `Dispose()` | `void Dispose()` | Detaches from the scope. Call when the view goes away. |

The dashboard captures the `SynchronizationContext` it is constructed on and marshals every scope-driven update onto it. With no context, it is fully synchronous, which makes it testable without a dispatcher. `Changed` fires on every configuring `With*` call — `WithAutoDiscovery` alone fires once per discovered type — so rebuilds are coalesced into one posted pass.

## Class: AgentMemberViewModel

The abstract base of one switchable row: a tool, an MCP server, an MCP server's tool, or a skill.

### Generated properties

| Name | Type | Description |
|---|---|---|
| `Name` | `string` | Display name. |
| `Description` | `string` | Description. |
| `IsEnabled` | `bool` | Whether the member is offered. Setting it calls `ApplyToScope`. |
| `StateText` | `string` | State as text. |
| `Note` | `string` | Why a member is blocked even when on. |
| `CallCount` | `int` | Calls this session. |
| `LastCalledText` | `string` | Last-call time as text. |

### Computed and protected members

| Member | Type / Signature | Description |
|---|---|---|
| `IsOff` | `bool` | `!IsEnabled`. |
| `IsReachable` | `bool` | `IsEnabled && Note.Length == 0` — "on but blocked by host policy" is a real state. |
| `HasBeenCalled` | `bool` | `CallCount > 0`. |
| `ActivityText` | `string` | Call count as display text. |
| `ApplyToScope` | `protected abstract void ApplyToScope(bool enabled)` | Pushes a host switch into the owning scope. Implemented by each row type. |

A row must not write a scope's bindable flag directly (e.g. `SkillStatusViewModel.IsEnabled`): that bypasses the scope's `Version` bump, and a cached prompt would keep serving text the host thought it had switched off. The row's `ApplyToScope` routes through the scope instead.

## Row types

| Type | Extra members |
|---|---|
| `ToolMemberViewModel` | None; the switch is stored on the shared tool policy. |
| `SkillMemberViewModel` | `HasResources`. |
| `McpServerMemberViewModel` | `HasError`, `IsFailedState`, `ToggleExpand()`, `CanUnload`, `CanReload`, `UnloadAsync()`, `ReloadAsync()`. |
| `McpToolMemberViewModel` | None; switching it off keeps the server offering its other tools. |

`McpServerMemberViewModel` deliberately offers both a switch and an unload: the switch drops the server's tools from the tool set while the connection stays up (instant and reversible), whereas `UnloadAsync` tears the process or transport down and has to pay for it again. `ReloadAsync` connects again using the registered configuration.

## Example

```csharp
using VeloxDev.AI.Dashboard;

using var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine(dashboard.SystemToolSummary);
Console.WriteLine(dashboard.SkillSummary);
Console.WriteLine(dashboard.McpSummary);
Console.WriteLine(dashboard.SubAgentSummary);
```

## Related

- [Transcript](../00_transcript/index.md) — the conversation beside the panel.
- [MCP status](../../20_mcp-integration/02_mcp-status/index.md) — the view-model the demos bind instead.
- [Sub-agent roster](../../21_sub-agents/02_roster/00_summary-and-row/index.md) — the rows `SubAgents` holds.
