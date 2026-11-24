# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer; the tests run on .NET 10.
- **Package:** `VeloxDev.Core.Extension` 12.3.0, which references `ModelContextProtocol` 2.2.0.
- **For local servers:** the runtime that mode needs on `PATH` — `node`/`npm`/`npx` for Node, `uv` for `Uvx`, Python plus `pip` for `Pip`, a .NET runtime for `Dotnet`, or an executable for `Exe`.
- **For HTTP servers:** network access to the endpoint.
- **No model is required** to parse configuration or inspect registered servers.

## Install

```powershell
dotnet new console -n McpQuickStart
cd McpQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension` and `ModelContextProtocol`.

## Create the scope

```csharp
using VeloxDev.AI.MCP;

var mcp = new McpScope()
    .WithSynchronizationContext(SynchronizationContext.Current ?? new SynchronizationContext());
```

`WithSynchronizationContext` makes the status view-model update on the host's thread. It is optional for a headless host and required for a bound UI.

**Expected result:** `mcp.Status.Servers` is an empty collection and `mcp.RegisteredServers` is empty.

## Configure a remote server

```csharp
var learn = new McpServerConfiguration
{
    Name = "Microsoft Learn",
    Description = "Microsoft documentation search over Streamable HTTP.",
    RunMode = McpServerRunMode.Http,
    Endpoint = "https://learn.microsoft.com/api/mcp",
    Options = new Dictionary<string, object?>
    {
        ["connectionTimeout"] = 30,
    },
};

mcp.WithServers(learn);
Console.WriteLine(mcp.RegisteredServers.Count); // 1
```

`WithServers` pre-registers configurations the agent may later load **by name**. It does not connect anything.

**Expected result:** prints `1`. `mcp.Status.Servers` is still empty because nothing has been loaded.

## Configure a local server

```csharp
var files = new McpServerConfiguration
{
    Name = "Filesystem (npx)",
    RunMode = McpServerRunMode.Npx,
    Package = "@modelcontextprotocol/server-filesystem",
    Arguments = ["C:/data"],
    Options = new Dictionary<string, object?>
    {
        ["env"] = new Dictionary<string, object?> { ["FILESYSTEM_ROOT"] = "C:/data" },
    },
};

mcp.WithServers(files);
```

For `Npx`, `Package` is the npm package name and `Arguments` are passed after it. For `Normal`, `Package` is the command as written and no install step runs.

**Expected result:** `mcp.RegisteredServers.Count` is `2`.

## What is rejected

`Options` accepts only known keys: `headers`, `oauth`, `connectionTimeout`, `transportMode`, `ownsSession`, `env`, `workingDirectory`. An unknown key throws when the server is loaded rather than being silently ignored.

**Expected result:** adding `["timout"] = 5` and calling `LoadAsync` throws with the key named.
