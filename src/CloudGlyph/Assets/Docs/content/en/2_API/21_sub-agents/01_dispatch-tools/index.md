# Dispatch tools

`VeloxDev.AI.SubAgents.SubAgentAgentToolkit` is the agent-facing view of a `SubAgentScope`: dispatch a background child, wait for it, read what it concluded, survey the roster, and cancel one.

## Class: SubAgentAgentToolkit

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `SubAgentAgentToolkit(SubAgentScope scope, WorkflowAgentScope host)` | Binds the tools to a subsystem and the host scope whose policy and budget apply. |
| `ToolNames` | `static readonly string[] ToolNames` | `["SpawnSubAgent", "WaitSubAgents", "GetSubAgentResult", "ListSubAgents", "CancelSubAgent"]`. |
| `CreateAllTools()` | `IList<AITool> CreateAllTools()` | Every tool, ignoring the host's switches. For a UI that lists the switchable surface. |
| `CreateTools()` | `IList<AITool> CreateTools()` | The tools, unwrapped, omitting the ones the host switched off. |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | The tools wrapped so every call is marshalled, budgeted and reported. This is what the provider contributes. |

All five are read-only with respect to the workflow graph, so a workflow host keeps them out of the mutation budget and dirty marking. They are asynchronous in shape even where the work is immediate: `SpawnSubAgent` returns a handle and runs the child in the background, so a caller never waits on a child inside a tool call.

## The five tools

| Tool | What it does |
|---|---|
| `SpawnSubAgent` | Starts a child and returns a handle immediately. |
| `WaitSubAgents` | Waits for named children, or all. A timeout is information, not a failure; it reports `timedOut: true` and leaves the children running. |
| `GetSubAgentResult` | Reads one child's result, capped by `maxChars`, after it completes. |
| `ListSubAgents` | Lists the roster and each child's state. |
| `CancelSubAgent` | Stops a running child; its state becomes `Cancelled`, which is not an error. |

## Fields a spawn accepts

Every narrowing field is optional, and **omitting a field means inherit, not none**. An empty array is a request for none, which is a different thing.

| Field | Effect |
|---|---|
| `task` | The child's user message. Required. |
| `name` | The roster label; a numbered stand-in when omitted. |
| `allowedTools` | The exact tools the child may use. |
| `allowedSkills` | Skills the child may read; none also removes its skill tools. |
| `allowedMcpServers` | MCP servers the child may reach. |
| `maxToolCalls` / `maxReadToolCalls` / `maxWriteToolCalls` | The child's sub-limits. |
| `allowNodeExecution` | Whether the child may run node business code. |
| `allowedGenericCommands` | The allowlisted command names the child may invoke. |
| `autoMarkDirty` | Whether the child's mutations mark the tree dirty. |
| `model` | Opaque to this library; handed to the host's factory. |
| `notes` | Free text contributed to the child's briefing. |

A spawn naming two of seven skills gives the child those two, and its briefing names them. The other five are absent and reported as dropped if the spawn asked for more than the parent had.

## Example

```csharp
foreach (var name in SubAgentAgentToolkit.ToolNames)
    Console.WriteLine(name);
```

## Related

- [SubAgentScope](../00_sub-agent-scope/index.md) — the subsystem these tools drive.
- [Roster](../02_roster/index.md) — what the tools report and the panel binds.
- [Context provider](../03_context-provider/index.md) — where these tools are contributed from.
