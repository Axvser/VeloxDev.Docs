# Server configuration

A server configuration says how a server is launched or reached. The same object is what `WithServers` pre-registers, what `LoadAsync` loads and what the status rows describe.

## Class: McpServerConfiguration

`VeloxDev.AI.MCP.McpServerConfiguration` is the configuration of one server. Its properties are generated MVVM properties, so they can be bound and written like any `[VeloxProperty]` member.

| Member | Type | Description |
|---|---|---|
| `Name` | `string` | Server key, used by every switch and load-by-name call. |
| `Description` | `string` | Operator-facing description. |
| `RunMode` | `McpServerRunMode` | How the server is reached. |
| `Package` | `string` | Package name or path, interpreted by `RunMode`. |
| `Version` | `string?` | Version tag for `Npm` and `Pip`; `null` means `latest`. |
| `Arguments` | `string[]` | Extra arguments passed to the server process. |
| `Endpoint` | `string?` | Remote URL for `Http`, e.g. `https://mcp.example.com/mcp`. Connect uses Streamable HTTP with SSE fallback. |
| `Options` | `IReadOnlyDictionary<string, object?>?` | Per-server options keyed by name. Unknown keys are rejected when the server is loaded. |

### Recognised option keys

| Key | Purpose |
|---|---|
| `headers` | HTTP headers, e.g. `Authorization`. |
| `oauth` | `clientId`, `clientSecret`, `redirectUri`, `scopes`. |
| `connectionTimeout` | Seconds, or a `TimeSpan` string. |
| `transportMode` | `Http` mode: `AutoDetect`, `StreamableHttp`, `Sse`. |
| `ownsSession` | `Http`: whether to hold the MCP session (stateful). |
| `env` | Environment variables for a stdio child. |
| `workingDirectory` | Working directory for a stdio child. |

`Options` is a dictionary rather than an anonymous object because the archive format's world is closed; a map needs no reflection to read.

## Enum: McpServerRunMode

| Member | Launch |
|---|---|
| `Npm` | Install the package, then run it with Node. |
| `Npx` | `npx -y <package> <args>`; no install. |
| `Uvx` | `uvx <package> <args>`; isolated Python environment. |
| `Pip` | Create a venv, `pip install`, then run the module. |
| `Dotnet` | `dotnet <dll> <args>`. |
| `Exe` | Run `<mcpRoot>/exe/<Package>` directly. |
| `Normal` | Run `Package` exactly as written, with `Arguments` verbatim. |
| `Http` | Connect to `Endpoint` over Streamable HTTP, with SSE fallback. |

Local installs are isolated under `.evn/mcp/{runtime}/`. `Normal` has no install step and no root prefix; the OS resolves the command.

## Class: McpConfigurationFile

`VeloxDev.AI.MCP.McpConfigurationFile` reads the common `.mcp.json` shape used by Claude Code and other MCP clients.

| Member | Signature | Description |
|---|---|---|
| `ServersProperty` | `const string ServersProperty = "mcpServers"` | The document's server-map property name. |
| `Load` | `static IReadOnlyList<McpServerConfiguration> Load(string path)` | Reads and parses a file. Throws when the file is missing or the document is not a server map. |
| `Parse` | `static IReadOnlyList<McpServerConfiguration> Parse(string json)` | Parses JSON text. |
| `Parse` | `static IReadOnlyList<McpServerConfiguration> Parse(JsonElement root)` | Parses an open root element. |

Supported fields: `command`, `args`, `env`, `cwd`, `url`, `type`, `headers`, `description`, `disabled`. A `command` entry becomes `Normal` with its arguments preserved; a `url` entry becomes `Http`; `type: "sse"` maps to `Options`. A `disabled: true` entry is skipped. `${VAR}` and `${VAR:-default}` expand from the process environment.

```csharp
var configs = McpConfigurationFile.Load(".mcp.json");
mcp.WithServers(configs.ToArray());
```

## Related

- [McpScope](../00_mcp-scope/index.md) — consuming these configurations.
- [Server status](../02_mcp-status/index.md) — how a configuration is reported once loaded.
