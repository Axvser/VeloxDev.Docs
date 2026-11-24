# MCP Integration

MCP cost is dominated by I/O and by list maintenance, not by graph size. Server handshakes are sequential; tool lists are flattened and re-filtered on every access; and two server registries rebuild status snapshots per row. The tool surface itself is a flat concatenation with no cross-server qualification. Bounds are read from the cited control flow; where a composed path depends on a helper outside the cited file, the bound is inferred.

## Cost model

| Symbol | Meaning |
|---|---|
| $m$ | configured or loaded servers |
| $k_i$ | tools offered by server $i$ |
| $r$ | resources of one server |
| $p$ | prompts of one server |
| args | prompt/resource arguments |
| chars | configuration or payload text |

## Configuration parsing

`McpConfigurationFile.Load` reads and parses the whole document, then `ParseServer` per entry maps `url` to HTTP or `command` to a stdio launch, expanding environment references (a dollar-brace name with an optional `:-default` fallback) with one compiled regex per string (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpConfigurationFile.cs:44-201`).

```csharp
if (!root.TryGetProperty(ServersProperty, out var servers) || servers.ValueKind != JsonValueKind.Object)
    throw new InvalidDataException($"The document has no object-valued '{ServersProperty}' property.");

var result = new List<McpServerConfiguration>();
foreach (var entry in servers.EnumerateObject())
{
    var config = ParseServer(entry.Name, entry.Value);
    if (config is not null) result.Add(config);
}

return result;
```

Parsing costs $O(\text{chars} + m + \sum \text{args} + \sum \text{env})$. Nothing is cached: a repeated `WithServersFromFile` re-reads and re-parses the file.

## Registration is quadratic

`WithServers` calls `Remember` for each configuration, and `Remember` does `_registered.RemoveAll(...)` before adding — a full scan of the current list per server (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs:341-360`, `:383-391`).

$$
T_{\text{register}} = O(m^2)
$$

The same shape appears in `ListServers`, where each status row resolves its configuration by copying the registered list under lock and scanning it (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpAgentToolkit.cs:760`, `:415-419`; `McpScope.cs:328-335`).

```plot
{
  "title": "Server registration",
  "grid": true,
  "xAxis": { "domain": [1, 60] },
  "yAxis": { "domain": [0, 4000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "linear" },
    { "fn": "x^2", "color": "#f472b6", "title": "Remember per server" }
  ]
}
```

## Server load

`LoadAsync` has replace semantics: it resets status, detaches and disposes every existing host, then loads each configuration in a `foreach` with `await` (`McpScope.cs:778-806`, `:897-955`). Each `LoadOneAsync` also calls `TrackServerAsync`, which scans the status rows.

$$
T_{\text{load}} = O\left(m^2 + \sum_i (\text{handshake}_i + k_i)\right)
$$

Wall-clock time is additive across servers because the loop never starts two handshakes at once. `AddAsync` loads one server without disturbing the rest. A failed server is recorded and does not stop the batch. Connection time is bounded only for HTTP, by a linked cancellation token; stdio install and launch have no equivalent cap in this path.

## Tool flattening

`LoadedTools` and `LoadedToolsByServer` rebuild a list from every per-server set on each access, filtering disabled servers and disabled `server/tool` keys (`McpScope.cs:152-188`).

```csharp
public IReadOnlyList<AITool> LoadedTools
{
    get
    {
        lock (_loadedToolsLock)
            return
            [
                .. _loadedToolSets
                    .Where(kv => !_disabledServers.Contains(kv.Key))
                    .SelectMany(kv => kv.Value.Where(t => !_disabledServerTools.Contains(ToolKey(kv.Key, t.Name))))
            ];
    }
}
```

`ToolKey` concatenates `server + "/" + tool` on every test (`McpScope.cs:196`), so one access costs

$$
T_{\text{flatten}} = O\left(\sum k_i\right)
$$

time, that many temporary strings, and a fresh list. The context provider calls `LoadedToolsByServer` once per render, so a version change repays the whole flatten and wraps each tool in a new `TrackedAIFunction`.

Enable/disable is the cheap path: a hash-set add/remove under the lock, then a status-row scan of $O(m)$ to mirror the row (`McpScope.cs:217-243`).

## Hosted server reconciliation

`HostedMcpServer` keeps one client and a per-server gate. `Adopt` builds `_live` with `ToDictionary(t => t.Name, ...)`, so duplicate tool names within one server throw at connect time (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/HostedMcpServer.cs:343-349`). `Reconcile` reuses existing `McpToolProxy` instances by name and clones each tool's JSON schema (`HostedMcpServer.cs:355-371`).

$$
T_{\text{reconcile}} = O\left(k + \sum \text{schema size}\right)
$$

A rebuild is lazy: `RebuildOwed` compares the built and attempted revisions, so a failed configuration is not retried on every invocation (`HostedMcpServer.cs:293-297`).

## Grants and status rows

`CreateGrantedView` copies only the offered tools of granted servers, filtering per tool through `IsToolEnabled`, which re-enters the lock and allocates a key (`McpScope.cs:518-534`, `:291-296`). Tracking the resulting rows is quadratic because `McpStatusViewModel.Track` calls `NotifyAggregates`, which re-projects all rows (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpStatusViewModel.cs:165-171`, `:202-217`).

## Naming across servers

`McpToolProxy.Name` returns the server's own tool name verbatim, and the provider concatenates every server's list (`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpToolProxy.cs:24-27`; `McpAgentContextProvider.cs:107-125`). Two servers exposing the same tool name therefore contribute two identically named tools; the `mcp:{server}` source string exists only on the wrapper, not in the tool name. There is no qualification pass, so collision handling is the caller's problem.

## Provider cache

`McpAgentContextProvider` caches instructions and tools on the scope `Version` alone (`McpAgentContextProvider.cs:78-100`). On a miss it constructs a fresh toolkit, up to ten management tools, then appends and wraps every loaded server tool. On a hit it returns the same `AIContext` with no lock beyond the provider's own.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the per-call gate and ledger every MCP tool also passes.
- [Agent Context and Skills](../19_agent-context-skills/index.md) — the other per-turn contributor with the same cache contract.
