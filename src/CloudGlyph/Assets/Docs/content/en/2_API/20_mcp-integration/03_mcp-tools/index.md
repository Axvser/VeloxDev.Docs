# MCP tools

The MCP subsystem reaches the model through a management toolkit and a context provider. The toolkit's names are public constants so a host composing several tool sources can classify them without repeating literals.

## Class: McpAgentToolkit

`VeloxDev.AI.MCP.McpAgentToolkit` is the MCP management tool set callable by the agent. Server configuration is provided in advance by the host; the agent does not construct arbitrary configs. The security boundary matches the workflow tools: *host registers, agent operates*.

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `McpAgentToolkit(McpScope scope, IReadOnlyList<McpServerConfiguration> servers)` | Builds the tools over a scope and the configurations it may load. |
| `CreateTools()` | `IList<AITool> CreateTools()` | The management tools, unwrapped. |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | The tools wrapped so every call is marshalled, gated and reported. This is what a provider contributes. |
| `BuildPromptContext()` | `string BuildPromptContext()` | The prompt text describing the tools. Generated, because a granted view sees a different surface. |
| `ToolNames` | `static readonly string[]` | Every management tool name, in registration order. |
| `ReadToolNames` | `static readonly string[]` | The names that only read; a host classifies them as queries. |

### Tool name constants

| Constant | Value |
|---|---|
| `ListName` | `ListMcpServers` |
| `LoadName` | `LoadMcpServers` |
| `UnloadName` | `UnloadMcpServer` |
| `DescribeName` | `DescribeMcpServer` |
| `AddToolName` | `AddMcpServer` |
| `SetArgumentsName` | `SetMcpServerArguments` |
| `ListResourcesName` | `ListMcpResources` |
| `ReadResourceName` | `ReadMcpResource` |
| `ListPromptsName` | `ListMcpPrompts` |
| `GetPromptName` | `GetMcpPrompt` |
| `LocalKind` | `mcp-add:local` |
| `HttpKind` | `mcp-add:http` |

`LocalKind` and `HttpKind` are the names a host writes rules against when the decision depends on the arguments rather than the tool: one installs software on the machine, the other only sends data out.

### What each tool does

| Tool | Category | Purpose |
|---|---|---|
| `ListMcpServers` | Read | Server state and tool counts. |
| `DescribeMcpServer` | Read | Export a server's tool-capability prompt. |
| `ListMcpResources` / `ReadMcpResource` | Read | MCP resources. |
| `ListMcpPrompts` / `GetMcpPrompt` | Read | MCP prompt templates. |
| `LoadMcpServers` / `UnloadMcpServer` | Curate | Install/connect or tear down. |
| `AddMcpServer` / `SetMcpServerArguments` | Curate | Add or reconfigure a server. |

Adding and reconfiguring are always offered; whether a call runs is decided at call time by the session's permission mode and the host's rules. A **granted view** — the surface handed to a spawned child — registers only `ReadToolNames`, because a child runs while its parent's turn is suspended and must not install or tear down software.

## Class: McpAgentContextProvider

`VeloxDev.AI.MCP.McpAgentContextProvider : AIContextProvider` contributes a scope's state per invocation: the server inventory, the management tools, and every connected server's tools. It makes MCP usable without the workflow layer.

| Member | Signature | Description |
|---|---|---|
| Constructor | `McpAgentContextProvider(McpScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | Creates a provider over a scope. Omit `tools` for standalone use. |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | The provider's state keys. |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | Renders and contributes the MCP state. |

The render is cached on the scope's `Version`. MCP has no language dimension, so the version alone is the whole cache key. Loading, adding or unloading a server advances it, so the change reaches the model on the next turn without rebuilding the agent.

## Notes

`McpToolProxy` and `HostedMcpServer` are internal connection plumbing and are not part of the public surface. Use `McpScope.LoadedTools`, `GetServerTools` and the status view-model to observe connections.

## Related

- [McpScope](../00_mcp-scope/index.md) — the scope these tools operate.
- [Server status](../02_mcp-status/index.md) — the state the read tools report.
- [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md) — the `Curate` gate.
