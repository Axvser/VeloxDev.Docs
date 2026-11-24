# Agent Context and Skills

Context is rendered from a compiled type tree; skills are discovered from embedded resources or from disk. Both paths cache the finished text on a version key, but discovery itself is synchronous, allocation-heavy, and re-reads every document each time it runs. The single quadratic term is in the status rows, not in the documents. Bounds are read from the cited control flow; where a tree helper's internals lie outside the cited module, the bound is inferred.

## Cost model

| Symbol | Meaning |
|---|---|
| $s$ | skills in one scope |
| $d$ | entries in a skill root directory |
| $r$ | resources bundled with one skill |
| $R$ | manifest resources in the assembly |
| $L$ | prompt languages ($\le 2$) |
| $n$ | nodes in the compiled context tree |
| chars | total document text |

## Discovery

`FileSkillSource.Discover` walks exactly two levels — `SKILL.md` in the root and one directory below (`Src/Core/VeloxDev.Core.Extension/Agent/Skills/FileSkillSource.cs:182-192`). It reads each file in full because frontmatter cannot be parsed otherwise, then recursively enumerates the skill's resource tree without opening the resources (`FileSkillSource.cs:194-208`).

```csharp
private static IReadOnlyList<string> EnumerateResources(string skillDirectory)
{
    try
    {
        return
        [
            .. Directory.EnumerateFiles(skillDirectory, "*", SearchOption.AllDirectories)
                .Where(f => !string.Equals(Path.GetFileName(f), SkillFileName, StringComparison.OrdinalIgnoreCase)
                            && ResourceExtensions.Contains(Path.GetExtension(f)))
                .Select(f => f.Substring(skillDirectory.Length)
                    .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                    .Replace(Path.DirectorySeparatorChar, '/'))
                .OrderBy(f => f, StringComparer.OrdinalIgnoreCase)
        ];
    }
```

Discovery costs

$$
T_{\text{discover}} = O(d + s \cdot \text{chars} + \sum r)
$$

and nothing between refreshes is cached except the resulting descriptors. Embedded discovery is similar but pays for the manifest array once per language: $O(L \cdot R + s \cdot \text{chars})$.

## Refresh is quadratic in rows

`SkillScope.Refresh` snapshots its sources, discovers from each, groups descriptors by name, then tracks one status row per concept (`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillScope.cs:429-455`). `Track` calls `NotifyAggregates`, which re-projects the entire bound collection into a new snapshot (`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillStatusViewModel.cs:131-137`, `:159-169`).

```csharp
var previous = Status.Skills.ToDictionary(s => s.Name, s => s.IsEnabled, StringComparer.OrdinalIgnoreCase);

Status.Reset();
foreach (var name in order)
{
    var group = byName[name];
    var primary = group.FirstOrDefault(d => d.Error is null) ?? group[0];
    var errors = group.Where(d => d.Error is not null).Select(d => d.Error!).ToArray();

    Status.Track(new SkillStatusViewModel
    {
        Name = name,
        Description = primary.Description,
        Source = primary.Source,
        Path = primary.Path,
        ResourceCount = group.Max(d => d.ResourceCount),
        // ...
        IsEnabled = !previous.TryGetValue(name, out var wasEnabled) || wasEnabled,
    });
}
```

So a refresh over $s$ skills costs

$$
T_{\text{refresh}} = O(s^2 + s \cdot \text{chars} + \sum r)
$$

The document reads dominate at small $s$; the row rebuild dominates as the catalogue grows.

```plot
{
  "title": "Skill refresh: rows vs. documents",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "linear discovery" },
    { "fn": "x^2", "color": "#f472b6", "title": "row rebuild" }
  ]
}
```

## Lookup and toggle

`SetEnabled` marshals to the UI context and calls `Find`, which is `Status.Skills.FirstOrDefault` over an `ObservableCollection` (`SkillScope.cs:207-224`, `:338-339`). Every toggle and every skill-tool call is therefore $O(s)$. Enabling $n$ skills through tools is $O(n \cdot s)$; no index exists, unlike the MCP scope's `HashSet` keys.

## Context tree and prompt assembly

`AgentContextTreeRenderer.TryEntry` resolves a type path, then lists the parent directory and scans its children (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/AgentContextTreeRenderer.cs:254-263`; `Src/Core/VeloxDev.Core/AI/AIContextTreeRegistry.cs:142-155`). `MembersAcross` walks the recorded base-type chain one directory per level. Rendering a type is

$$
T_{\text{type}} = O(\text{base-depth} \cdot \text{children per directory} + \text{chars})
$$

The full skeleton, `ProvideAllContexts`, reads every embedded reference and renders every framework and registered customer type. The source records the skeleton at roughly 870 KB per render and forbids running it per turn (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2006-2012`). `ProvideProgressiveContextPrompt` keeps the same header and safety text but emits one-line type summaries instead of full property tables (`WorkflowAgentScope.cs:1413-1419`).

## Per-turn caching

`SkillAgentContextProvider` caches instructions and tools on `(Version, PromptLanguage)` and returns the same instances until the key moves (`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillAgentContextProvider.cs:78-104`). `WorkflowAgentContextProvider` caches the whole render on the scope's packed `ContextKey` and reuses the tool array when only the usage band changed (`Agent/Workflow/WorkflowAgentContextProvider.cs:112-132`).

On a hit the cost is $O(1)$ and the allocation is zero. On a miss, instructions cost $O(\text{chars})$ and the selected skills are sorted at $O(s \log s)$ per kind.

## Skills tools

`SkillAgentToolkit` exposes four tools (`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillAgentToolkit.cs:48-49`). `ListSkills` sorts all skills and serialises every resource name, $O(s \log s + \text{chars})$. `LoadSkill` and `UnloadSkill` each pay the $O(s)$ `Find`, and `LoadSkill` then reads the body, $O(\text{chars})$.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the toolkit the prompt describes.
- [MCP Integration](../20_mcp-integration/index.md) — the other per-turn tool source with the same version-cache contract.
