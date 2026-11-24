# Archive and manifest

The CLI reads what the library's serializer wrote, plus the assemblies its component types live in. It never reads a project file. That keeps the execution host independent of any GUI framework and makes an edit-and-run loop possible against the same document the editor saves.

## The archive

An archive is a document produced by `tree.Serialize()`, not hand-written JSON. Serializing through a concrete tree type avoids emitting a root `$type`; serializing through a base or interface reference adds one.

```csharp
using System.IO;
using VeloxDev.Serialization;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(node);

File.WriteAllText("graph.json", tree.Serialize());
Console.WriteLine($"wrote graph.json with {tree.Nodes.Count} node(s)");
```

## The manifest

Dependencies are declared in a sidecar named `<archive>.manifest.json`.

```json
{
  "assemblies": [ "lib/MyNodes.dll", "lib/MyNodes.Helpers.dll" ],
  "rootType": "MyCompany.ViewModels.MyTreeViewModel",
  "allowExecution": false
}
```

| Field | Effect |
|---|---|
| `assemblies` | Files that declare the node, slot and link types in the archive. Paths resolve relative to the manifest and may not escape its directory. |
| `rootType` | The concrete tree type the document was serialized from. Needed when it is not `TreeDefaultViewModel`; without it the CLI reads the graph into `TreeDefaultViewModel`. |
| `allowExecution` | Opt-in for execution tools. Without it (or `--allow-execution`), execution tools are absent from the MCP surface. |

`--assembly <path>` adds a dependency without editing the manifest. A document naming a type whose assembly was not loaded fails before deserialization, with the type name and the remedy (`--assembly` or a manifest entry).

Loading an assembly runs its module initializers, which register serializer readers. Both the manifest and `--assembly` are therefore privileged input: load only files you trust.

## Compatibility

- A component built against a newer Core than the CLI bundles is fine.
- An older component is supported down to Core 10.0.1.
- `VeloxDev.Core.Extension` is not a unified model layer, so any version difference is reported as a risk.
- `--strict-plugin-versions` refuses a plugin whose Core / Core.Extension reference has a different major version; the default loads it and warns.

## Producing and running

```powershell
dotnet new console -n ArchiveBuilder
cd ArchiveBuilder
dotnet add package VeloxDev.Core --version 12.3.0
dotnet run
veloxdev run --archive graph.json --start 0 --log-file run.log
veloxdev mcp --archive graph.json --allow-execution
```

**Expected result:** `ArchiveBuilder` prints `wrote graph.json with 1 node(s)`; the two `veloxdev` commands run against that file.

## Related

- [run command](../00_run-command/index.md) — consuming the archive once.
- [mcp command](../01_mcp-command/index.md) — serving it over stdio.
