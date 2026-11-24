# Headless CLI

The CLI has two verbs, `mcp` and `run`, and no directory discovery: every file it touches is named explicitly. The costs that matter are the one-time option scan, the plugin loader's linear lists, and the fact that every isolated worker run reloads the whole plugin set in a fresh process. Bounds are read from the cited control flow; where a runtime or framework helper is outside the cited file, the bound is inferred.

## Cost model

| Symbol | Meaning |
|---|---|
| $a$ | argv tokens |
| $p$ | plugins loaded in this process, cumulative |
| $r$ | assembly references of one plugin |
| $f$ | manifest assembly entries |
| $t$ | toolkit tools exposed by the session |
| $j$ | live worker jobs |
| $A$ | audit ring capacity (500) |
| chars | archive, result or CSV text |

## Option parsing

`CliOptions.Parse` is one forward scan from index 1. `Split` cuts on the first `=`, and a local `Value()` consumes the next token when the value is inline (`Src/Cli/VeloxDev.Cli/CliOptions.cs:113-124`).

```csharp
for (var i = 1; i < args.Length; i++)
{
    var raw = args[i];
    var (name, inline) = Split(raw);

    string Value()
    {
        if (inline is not null) return inline;
        if (i + 1 >= args.Length) throw new CliUsageException($"Option '{name}' requires a value.");
        return args[++i];
    }
```

Parsing is

$$
T_{\text{parse}} = O(a) + O(\text{value length})
$$

with $O(a)$ space for the assembly list and scalar fields. The verb is validated up front and dispatched in `Program` (`CliOptions.cs:102-104`; `Src/Cli/VeloxDev.Cli/Program.cs:22-26`).

## Archive and manifest

`WorkflowArchive.Load` canonicalises and reads the graph, then parses the sidecar manifest and iterates its `assemblies` array (`Src/Cli/VeloxDev.Cli/WorkflowArchive.cs:134-145`). `ResolveInside` recomputes `GetFullPath(directory)` for every entry before testing the prefix (`WorkflowArchive.cs:170-188`).

$$
T_{\text{archive}} = O(\text{chars} + f \cdot L_{\text{path}})
$$

The parsed graph text is retained for the session lifetime. No directory enumeration occurs anywhere, so there is no hidden $O(\text{files})$ term.

## Plugin loading

`PluginLoader.Load` holds one lock, hooks the resolving events once, installs an `AssemblyDependencyResolver`, finds the loaded assembly by scanning `AssemblyLoadContext.Default.Assemblies`, copies the file to a staging directory, loads it, runs its module constructor, and checks referenced versions (`Src/Cli/VeloxDev.Cli/PluginLoader.cs:129-210`).

```csharp
foreach (var resolver in _resolvers)
{
    var path = resolver.ResolveAssemblyToPath(name);
    if (path is not null && File.Exists(path))
        return LoadResolved(context, path);
}

if (name.Name is { Length: > 0 } simpleName)
{
    foreach (var directory in _directories)
    {
        var candidate = System.IO.Path.Combine(directory, simpleName + ".dll");
        if (File.Exists(candidate))
            return LoadResolved(context, candidate);
```

Every one of these lookups is a linear scan over lists — resolvers, directories, loaded assemblies, warnings, mismatches. Loading $p$ plugins therefore costs

$$
T_{\text{plugins}} = O\left(p^2(1 + r)\right)
$$

and unresolved dependencies pay $O(p)$ filesystem probes each time the resolver runs. Assemblies are never unloaded, and the registry survives `LoadArchive` reloads, so $p$ grows for the process lifetime.

```plot
{
  "title": "Plugin load: linear lists vs. a set",
  "grid": true,
  "xAxis": { "domain": [1, 60] },
  "yAxis": { "domain": [0, 4000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "set-based" },
    { "fn": "x^2", "color": "#f472b6", "title": "linear scans per load" }
  ]
}
```

## Session creation

`WorkflowSession.Create` validates each path, loads the archive, loads every manifest and explicit assembly, resolves the root type, deserialises the whole graph, builds the agent scope, auto-discovers types, installs the redirect policy and stores, and finally enumerates toolkit tools into a name-to-function dictionary (`Src/Cli/VeloxDev.Cli/WorkflowSession.cs:149-257`, `:325-346`).

$$
T_{\text{session}} = O\left(\text{chars} + n + l + t + \sum \text{plugin loads}\right)
$$

`BuildExposedFunctions` is called again by `CreateMcpTools`, `DescribeCapabilities` and `IsBatchableTool`; batch application calls the latter twice per operation, so $k$ operations cost $O(k \cdot t)$ tool constructions (`WorkflowSession.cs:294-296`; `Src/Cli/VeloxDev.Cli/ArchiveTools.cs:124-128`).

## Host, audit and reload

`WorkflowSessionHost.Acquire` increments a lease under lock and `Release` retires a replaced session at zero (`Src/Cli/VeloxDev.Cli/WorkflowSessionHost.cs:107-135`). Tool dispatch is a dictionary lookup, then `Stopwatch` timing and an audit record; the audit list trims with `RemoveRange` once past 500, an $O(A)$ shift per record (`:161-182`).

$$
T_{\text{dispatch}} = O(\text{tool cost} + \text{args} + \text{result}) + O(A)
$$

`ReloadAsync` serialises reloads with a semaphore, builds the next session fully, then swaps (`:254-302`). At most one retired session is retained.

## Workers and jobs

`WorkerJobRegistry` keys jobs by a short GUID in a dictionary, so start and find are $O(1)$ average; listing sorts by start time at $O(j \log j)$ and clearing scans at $O(j)$ (`Src/Cli/VeloxDev.Cli/WorkerJobRegistry.cs:91-157`).

```csharp
public WorkerJob? Find(string id)
{
    lock (_gate)
    {
        return _jobs.TryGetValue(id, out var job) ? job : null;
    }
}

public IReadOnlyList<WorkerJob> List()
{
    lock (_gate)
    {
        return [.. _jobs.Values.OrderBy(j => j.StartedAt)];
    }
}
```

`WorkerRunner` serialises the live tree to a temporary archive and starts `dotnet <cli> run` with every plugin path, reading stdout and stderr fully (`Src/Cli/VeloxDev.Cli/WorkerRunner.cs:41-191`). The child re-enters session creation, so each isolated run repays the plugin cost above.

$$
T_{\text{worker}} = O(n + l + \text{chars}) + T_{\text{plugins}}
$$

## CSV and workspace

`RunLogCsv.TryWrite` parses the result, buffers the whole CSV in a `StringBuilder`, writes once, then `Attach` parses and rewrites the result to add `csvFile` (`Src/Cli/VeloxDev.Cli/RunLogCsv.cs:22-108`). Cost is $O(\text{chars})$ in each direction and $O(\text{outChars})$ peak memory, since the file is never streamed.

`WorkspaceRule.Ensure` canonicalises each candidate and does a prefix test against the workspace plus separator (`Src/Cli/VeloxDev.Cli/WorkspaceRule.cs:28-41`). Each check is $O(L_{\text{path}})$, but the same paths are checked at startup, again inside `Create`, and again on every load/save/assembly operation — constant work repeated per operation, never memoised.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the toolkit the CLI exposes over MCP.
- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the headless surface the CLI runs without.
