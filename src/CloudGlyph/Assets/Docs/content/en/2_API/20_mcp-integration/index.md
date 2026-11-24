# MCP Integration

`McpScope` connects the Model Context Protocol servers an agent may use. A server can be a local process launched through npm, npx, uvx, pip, dotnet or a plain executable, or a remote endpoint over Streamable HTTP. Every connected server's tools join the agent's tool set **per turn**, so loading or unloading one takes effect on the next turn without rebuilding the agent.

The scope also contributes management tools: list, describe, load, unload, add and reconfigure servers, and read their resources and prompts.

## Namespaces

| Namespace | Types |
|---|---|
| `VeloxDev.AI.MCP` | `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpConfigurationFile`, `McpServerStatus`, `McpServerStatusViewModel`, `McpStatusViewModel`, `McpServerSummary`, `McpAgentToolkit`, `McpAgentContextProvider` |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope.WithMcps`, `WorkflowAgentScope.Mcp` |

## Pages

- [McpScope](00_mcp-scope/index.md) — configuration, loading, unload, switches, status and disposal.
- [Server configuration](01_mcp-configuration/index.md) — `McpServerConfiguration`, run modes and `.mcp.json` parsing.
- [Server status](02_mcp-status/index.md) — the bindable server rows and aggregate counts.
- [MCP tools](03_mcp-tools/index.md) — the management toolkit and the context provider.

## Where the tools come from

| Source | Contributed by |
|---|---|
| a connected server's tools | the MCP context provider, per turn |
| `ListMcpServers`, `LoadMcpServers`, `UnloadMcpServer`, `AddMcpServer`, … | the same provider |
| `ListMcpResources`, `ReadMcpResource`, `ListMcpPrompts`, `GetMcpPrompt` | the same provider |

Do not also register them with `WithTools`: the framework unions tool lists without deduplicating by name.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the built-in tools MCP tools sit beside.
- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — why adding a server is a `Curate` action.
