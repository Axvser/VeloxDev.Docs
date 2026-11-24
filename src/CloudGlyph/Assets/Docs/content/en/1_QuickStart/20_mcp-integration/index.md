# MCP Integration

`McpScope` connects the Model Context Protocol servers an agent may use. A server can be a local process started through npm, npx, uvx, pip, dotnet or a plain executable, or a remote endpoint reached over Streamable HTTP. Every connected server's tools join the agent's tool set **per turn**, so loading or unloading one takes effect on the next turn without rebuilding the agent.

The scope also contributes management tools: list, describe, load, unload, add and reconfigure servers, and read their resources and prompts.

## What you will build

- a `McpScope` from a `{ "mcpServers": … }` document;
- a local npx server and a remote HTTP server configured side by side;
- the management and reading tools an agent uses to operate them.

## Pages

- [Setup](00_setup/index.md) — prerequisites, the package, and the first server.
- [Usage](01_usage/index.md) — run modes, loading, the management tools, the status view-model, and the complete program.

## Where the tools come from

| Source | Contributed by |
|---|---|
| a connected server's tools | the MCP context provider, per turn |
| `ListMcpServers`, `LoadMcpServers`, `UnloadMcpServer`, `AddMcpServer`, … | the same provider |
| `ListMcpResources`, `ReadMcpResource`, `ListMcpPrompts`, `GetMcpPrompt` | the same provider |

Do not also register these with `WithTools`: the framework unions tool lists without deduplicating by name.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the built-in tools MCP tools sit beside.
- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — why adding a server is a `Curate` action.
