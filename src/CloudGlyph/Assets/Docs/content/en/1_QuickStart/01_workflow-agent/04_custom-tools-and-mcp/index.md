# Workflow Agent — Custom Tools & MCP

On top of the built-in toolkit you can register your own tools, and you can extend the agent with Model Context Protocol servers whose tools are merged into every conversation.

## 1. Register custom tools

`WithTools` and `WithQueryTools` append extra `AITool`s to the surface returned by `ProvideTools()`. Both accept a `promptContext` string that becomes a "Custom Tools" system-prompt section and a params array of tools:

```csharp
AITool serverStatus = AIFunctionFactory.Create(
    () => $"workflow nodes: {scope.Tree.Nodes.Count}", "ServerStatus");

AITool readOnlyClock = AIFunctionFactory.Create(
    () => DateTimeOffset.Now.ToString("O"), "ReadOnlyClock");

scope.WithTools("ServerStatus reports the current number of workflow nodes.", serverStatus);
scope.WithQueryTools("ReadOnlyClock returns the current time; it never mutates the tree.", readOnlyClock);
```

`AITool` and `AIFunctionFactory` come from `Microsoft.Extensions.AI`; `scope` is the `WorkflowAgentScope` built on the previous page.

- `WithTools` registers mutation-capable tools: `AIFunction`s get a **tracked wrapper** (UI-thread marshalling, budget accounting, the tool-call callback and auto-dirty). `WithQueryTools` registers read-only tools with identical behaviour except they never trigger auto-dirty marking and count against the read budget.
- Non-`AIFunction` tools (for example a raw MCP client tool) are added as-is, without the tracked wrapper.

**Expected result:** after registration `scope.ProvideTools()` contains `ServerStatus` and `ReadOnlyClock`; a `ReadOnlyClock` call never marks the tree dirty.

## 2. Load MCP servers with `McpScope`

`McpScope` (`VeloxDev.AI.MCP`) loads servers and exposes their tools as `AITool`s. Each server is described by an `McpServerConfiguration` whose `RunMode` picks the launch strategy:

```csharp
var mcp = new McpScope()                          // installs into ".evn/mcp" by default
    .WithMcpRoot(".evn/mcp")                      // override the install root if you like
    .WithConnectionTimeout(TimeSpan.FromSeconds(30));

McpServerConfiguration[] servers =
[
    new()                                          // remote Streamable HTTP: no local runtime
    {
        Name = "Microsoft Learn",
        Description = "Microsoft docs retrieval (remote Streamable HTTP)",
        RunMode = McpServerRunMode.Http,
        Endpoint = "https://learn.microsoft.com/api/mcp",
        Options = new { connectionTimeout = 30 },
    },
    new()                                          // local npx server
    {
        Name = "Filesystem",
        RunMode = McpServerRunMode.Npx,
        Package = "@modelcontextprotocol/server-filesystem",
        Arguments = [AppContext.BaseDirectory],
        Options = new { env = new { FILESYSTEM_ROOT = AppContext.BaseDirectory } },
    },
];

AITool[] mcpTools = await mcp.LoadAsync(servers);
```

- `McpServerConfiguration` fields: `Name`, `Description`, `RunMode`, `Package`, `Version`, `Arguments` (string array), `Endpoint`, and an arbitrary `Options` object. `McpServerRunMode` members: `Npm`, `Npx`, `Uvx`, `Dotnet`, `Pip`, `Exe`, `Http`.
- `Http` connects over Streamable HTTP using `Endpoint` + `Options` (headers, OAuth, `connectionTimeout`, `transportMode`, `ownsSession`). The stdio modes (`Npx`, …) install the `Package` (npm/pip/dotnet/uvx as appropriate) into `McpRootRelative` and connect over stdio using `Package`/`Version`/`Arguments`/`Options.env`/`Options.workingDirectory`.
- `McpScope` also offers `WithSynchronizationContext` (marshal load/status callbacks onto the UI thread) and `WithOAuthAuthorizationRedirect((authUri, redirectUri, ct) => ...)` for HTTP OAuth. After loading, `mcp.LoadedTools` holds the connected servers' tools, `mcp.GetServerTools(name)` per-server tools, `mcp.UnloadServer(name)` removes one mid-session, and `mcp.Status` is a live `McpStatusViewModel` (per-server state, connected/error counts).

**Expected result:** `LoadAsync` returns the connected servers' tools as `AITool[]`; each tool name is prefixed with its server; a server that fails to connect does not throw but is tracked in `mcp.Status` with state `Error`.

## 3. Hand MCP servers to the agent via `McpAgentToolkit`

Two different design points exist: you can merge *server* tools into the conversation yourself (the next page), or you can let the *agent* manage host pre-registered servers with `McpAgentToolkit`:

```csharp
var mcp = new McpScope();                          // one shared loader
McpServerConfiguration[] hostConfigs = [...];      // fixed once by the host at load time

scope.WithTools(
    "MCP server management tools: ListMcpServers reports each server's state; " +
    "DescribeMcpServer exports a connected server's tool-capability prompt; " +
    "LoadMcpServers loads host pre-registered servers (installing and connecting when needed); " +
    "UnloadMcpServer removes a server mid-session. Configuration is fixed by the host " +
    "and cannot be changed afterwards.",
    [.. new McpAgentToolkit(mcp, hostConfigs).CreateTools()]);
```

`McpAgentToolkit.CreateTools()` returns four agent-facing tools — `ListMcpServers`, `DescribeMcpServer`, `LoadMcpServers`, `UnloadMcpServer`. Because they are registered through `WithTools`, the agent can inspect and load servers mid-session, but **cannot reconfigure them**: server configuration is fixed once at load time. Loading a local server installs npm/pip runtimes and can be slow, so the prompt instructs the agent to confirm with the user first.

**Expected result:** `ProvideTools()` contains the four `Mcp*` management tools; after the agent calls `LoadMcpServers`, the corresponding server tools appear in `mcp.LoadedTools` and on the next conversation's tool set.

## Run declaration

- ⚠️ Statically verified only. API names, `McpServerConfiguration` fields, `McpServerRunMode` members and behaviour are taken from `Src/Core/VeloxDev.Core.Extension/Agent/MCP/*` and the demo `AgentHelper.cs`; no server was actually loaded in this documentation pass.
