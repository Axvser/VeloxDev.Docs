# 04 · Custom Tools & MCP

## 1. Developer-registered tools

```csharp
using Microsoft.Extensions.AI;

AIFunction ping = AIFunctionFactory.Create(() => "pong", "Ping");

scope.WithTools("Use Ping to check connectivity.", ping);     // mutation-capable custom tool
scope.WithQueryTools(null, lookupTool);                        // read-only custom tool
```

| Member | Signature | Effect |
|---|---|---|
| `WithTools` | `WithTools(string? promptContext, params AITool[] tools)` | Registers mutation-capable custom tools; always included in `ProvideTools()`. |
| `WithQueryTools` | `WithQueryTools(string? promptContext, params AITool[] tools)` | Registers read-only custom tools — never auto-marked dirty, never counted as a write. |

- An `AIFunction` custom tool is wrapped with `TrackedAIFunction`, so it gets the same UI-thread marshalling, budget accounting, `ToolCalled` callback and auto-dirty treatment as a built-in. A non-`AIFunction` tool is added as-is and gets none of that.
- The optional `promptContext` is injected as a "Custom Tools" section in the prompt. Registration is remembered per group, so a **sub-agent spawn can grant a subset** with the matching guidance — never the guidance for a tool the child did not receive.

**Expected result:** `scope.ProvideTools()` contains your tool names alongside the 68 built-ins.

## 2. Attach MCP servers

`McpScope` loads Model Context Protocol servers and merges their tools into the agent. A host attaches the subsystem with one call; the subsystem contributes its own tools and prompt text per turn.

```csharp
using VeloxDev.AI.MCP;

var mcp = new McpScope();
mcp.WithServers(new McpServerConfiguration
{
    Name = "Filesystem",
    RunMode = McpServerRunMode.Npx,
    Package = "@modelcontextprotocol/server-filesystem",
    Arguments = [AppContext.BaseDirectory],
});

scope.WithMcps(mcp);                 // wire the subsystem into the scope
await mcp.LoadAsync(mcp.RegisteredServers);
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`Mcp`, `McpServers`, `LoadMcpServersAsync`).

`WithMcps` does four things at once: it sets the MCP scope's confirmation handler to the workflow scope's `ResolveConfirmationAsync` (so an approval is configured once), hands it the UI `SynchronizationContext`, and composes `mcp.CreateContextProvider(SharedTools, Pipeline)` so MCP-sourced tools join the **same** budgets, gates and callbacks as the built-in tools.

**Expected result:** after `LoadAsync` the connected server's tools appear in the next turn's tool list; unloading a server removes them from the next turn.

## 3. The MCP management tools

`McpAgentToolkit` exposes server management to the model. Registration is conditional:

| Tool | Registered when |
|---|---|
| `ListMcpServers` | always — pure query |
| `LoadMcpServers` | `!IsGrantedView` (i.e. the host owns the scope, not a narrowed sub-agent view) |
| `UnloadMcpServer` | `!IsGrantedView` |
| `AddMcpServer` | `SelfServiceLevel != McpSelfServiceLevel.Closed` **and** `!IsGrantedView` |

`McpSelfServiceLevel` is a ladder: `Closed = 0` (the demo's choice — the agent may load/unload/inspect only the host's pre-registered servers), `RemoteConfirmed = 1`, `AllConfirmed = 2`, `Unrestricted = 3`. Raise it with `McpScope.WithSelfService(level)`.

**Expected result:** at `Closed`, `ListMcpServers` / `LoadMcpServers` / `UnloadMcpServer` / `DescribeMcpServer` are offered and no `AddMcpServer`; raising the level adds `AddMcpServer`.

## 4. Run modes and configuration

| `McpServerRunMode` | Command model |
|---|---|
| `Npm` | `npm install` into `{root}/node/{package}/`, then `node {entry} {args}`. |
| `Npx` | `npx -y {package} {args}` (temporary download, no install). |
| `Uvx` | `uvx {package} {args}`. |
| `Dotnet` | `dotnet {dll} {args}` (the user pre-publishes under `{root}/dotnet/`). |
| `Pip` | Creates a venv, `pip install`, then `python -m {module} {args}`. |
| `Exe` | Executes `{root}/exe/{package}` directly. |
| `Http` | Connects to a remote server at `Endpoint` (Streamable HTTP, SSE fallback). |

`McpServerConfiguration.Options` is an anonymous-object blob: for `Http` — `headers`, `oauth`, `connectionTimeout`, `transportMode`, `ownsSession`; for stdio — `env`, `workingDirectory`. Unknown keys are rejected.

**Expected result:** a bad configuration (unknown `Options` key, missing `Package` for a local mode) fails that server alone — its status becomes `Error`, `ServerError` fires, and it contributes zero tools; the rest of the batch loads.

## 5. Looking at it all together

```csharp
scope.WithTools("Use Ping to check connectivity.", ping)
     .WithMcps(mcp);
```

**Expected result:** the next turn's tool list is the built-ins plus `Ping` plus every loaded server's tools, and the prompt carries the custom-tool guidance and the MCP inventory block.

## Run declaration

- ⚠️ Not actually run — statically verified only. The wiring and the conditional tool registration are read from `WorkflowAgentScope.WithMcps` and `McpAgentToolkit.CreateTools`; no MCP server was loaded from this page. (The deterministic `Agent/**` test suite passed — see the Tool Budgets page — but that suite does not launch a real MCP server.)
