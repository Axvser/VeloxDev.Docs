# Usage

## Run modes

| `McpServerRunMode` | Launch |
|---|---|
| `Npm` | install the package, then run it with Node |
| `Npx` | `npx -y <package> <args>` — no install |
| `Uvx` | `uvx <package> <args>` — isolated Python environment |
| `Pip` | create a venv, `pip install`, then run the module |
| `Dotnet` | `dotnet <dll> <args>` |
| `Exe` | run `<mcpRoot>/exe/<Package>` directly |
| `Normal` | run `Package` exactly as written, with `Arguments` verbatim |
| `Http` | connect to `Endpoint` over Streamable HTTP, with SSE fallback |

Local installs are isolated under `.evn/mcp/{runtime}/`. `Normal` has no install step and no root prefix; the OS resolves the command.

**Expected result:** a `Normal` server configured with `Package = "node"` and `Arguments = ["server.js"]` runs exactly that command.

## Loading, replacing and adding

```csharp
var tools = await mcp.LoadAsync(mcp.RegisteredServers); // REPLACE everything loaded before
```

`LoadAsync` releases the clients it replaces, so old stdio children do not outlive a reload. `AddAsync` is the incremental counterpart:

```csharp
var extraTools = await mcp.AddAsync(new McpServerConfiguration
{
    Name = "Local tools",
    RunMode = McpServerRunMode.Normal,
    Package = "node",
    Arguments = ["server.js", "--port", "0"],
});
```

Both record the configuration, so the agent's `LoadMcpServers` can bring it back by name later.

**Expected result:** after `LoadAsync` of two servers, `mcp.LoadedTools` contains their tools and `mcp.Status.Servers` has two tracked rows.

## Read `.mcp.json`

```csharp
var configs = McpConfigurationFile.Load(".mcp.json");   // or Parse(json)
mcp.WithServersFromFile(".mcp.json");                   // pre-register, load later by name
await mcp.LoadConfigurationFileAsync(".mcp.json", ct);  // load now (replace semantics)
```

A `command` entry becomes `Normal` with its arguments preserved; a `url` entry becomes `Http`; `env`, `cwd`, `headers` and `type: "sse"` map to `Options`; `disabled: true` entries are skipped. `${VAR}` and `${VAR:-default}` references expand from the process environment.

**Expected result:** a document with one `command`, one `url` and one `disabled` entry yields two registered servers.

## The management tools

`mcp.CreateContextProvider()` contributes these on every turn:

| Tool | Category | Purpose |
|---|---|---|
| `ListMcpServers` | Read | server state and tool counts |
| `DescribeMcpServer` | Read | export a server's tool-capability prompt |
| `ListMcpResources` / `ReadMcpResource` | Read | MCP resources |
| `ListMcpPrompts` / `GetMcpPrompt` | Read | MCP prompt templates |
| `LoadMcpServers` / `UnloadMcpServer` | Curate | install/connect or tear down |
| `AddMcpServer` / `SetMcpServerArguments` | Curate | add or reconfigure a server |

Attach it to a workflow scope and the same tools are governed by that scope's budget and permission policy:

```csharp
var scope = tree.AsAgentScope()
    .WithMcps(mcp)
    .WithPermissionMode(AgentPermissionMode.AutoEdit);
```

In `AutoEdit`, loading a server (`Curate`) asks the host's confirmation handler; in `Bypass` it does not ask, but a `Deny` rule on `category:Curate` still holds.

**Expected result:** the model sees `ListMcpServers` and `LoadMcpServers` on its next turn, without a rebuild.

## Per-server and per-tool switches

```csharp
mcp.SetServerEnabled("Filesystem (npx)", false);
mcp.SetToolEnabled("Microsoft Learn", "microsoft_docs_search", false);
```

A disabled server keeps its connection and status but contributes no tools; a disabled tool is filtered from that server's tool list. Both switches advance `Version`, so the next prompt reflects them.

**Expected result:** `mcp.IsServerEnabled("Filesystem (npx)")` is `false`, and its tools are absent from `LoadedTools`.

## The status view-model

`mcp.Status` is bindable and thread-marshalled when a `SynchronizationContext` is set:

- per server: `Name`, `StateText` (`NotStarted` / `Installing` / `Connecting` / `Connected` / `Error`), `ToolCount`, `Error`;
- aggregates: `ConnectedCount`, `ErrorCount`, `WorkingCount`, `IsAllReady`, `HasError`.

From a non-UI thread read `mcp.Status.Snapshot` (an immutable copy), not `Servers`.

**Expected result:** while a server connects, `WorkingCount` is `1`; after it connects, `ConnectedCount` is `1`.

## Verification

1. Run the complete program. It prints two registered servers and an inventory block naming both.
2. Confirm the disabled entry is absent.
3. With network access, call `await mcp.LoadAsync(new[] { learn })` and check `Status.Servers[0].StateText` reaches `Connected`; without network it reaches `Error` and the message names the cause.

## Complete code

```csharp
using VeloxDev.AI.MCP;

const string document = """
{
  "mcpServers": {
    "learn": {
      "url": "https://learn.microsoft.com/api/mcp"
    },
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/data"]
    },
    "disabled-example": {
      "command": "node",
      "args": ["server.js"],
      "disabled": true
    }
  }
}
""";

var configs = McpConfigurationFile.Parse(document);
var mcp = new McpScope().WithServers(configs.ToArray());

Console.WriteLine($"registered: {mcp.RegisteredServers.Count}");
foreach (var server in mcp.RegisteredServers)
    Console.WriteLine($"  {server.Name} ({server.RunMode})");

Console.WriteLine();
Console.WriteLine(mcp.BuildInventoryBlock());
```

**Expected output shape:**

```text
registered: 2
  learn (Http)
  files (Normal)

# MCP Servers
… inventory text naming learn and files …
```

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, `McpConfigurationFile.cs`, `McpServerConfiguration.cs`, `McpServerRunMode.cs`, `McpAgentToolkit.cs`, `McpStatusViewModel.cs`, and the usage notes in `Src/Core/VeloxDev.Core.Extension/README.md`. Connecting to a live server needs network access, so no run output is recorded.
