# Setup

## Prerequisites

- **Runtime:** .NET 8.0 or newer. The tool targets `net8.0` with `RollForward=LatestMajor`, so a host with only .NET 9 or 10 installed runs it too. Check with `dotnet --list-runtimes`.
- **Package:** `VeloxDev.Cli` 12.0.0. It bundles `VeloxDev.Core` and `VeloxDev.Core.Extension`.
- **An archive:** a document produced by `tree.Serialize()`, not hand-written JSON.
- **The component assemblies:** files that declare the node, slot and link types in the archive. Loading an assembly runs its module initializers and registers its serializer readers — load only files you trust.
- **Compatibility:** a component built against a newer Core than the CLI bundles is fine; an older one is supported down to Core 10.0.1. `VeloxDev.Core.Extension` is not a unified model layer, so any version difference is reported as a risk.

## Install

```powershell
dotnet --info
dotnet tool install --global VeloxDev.Cli
veloxdev --help
```

**Expected result:** `veloxdev --help` prints the usage text for the `run` and `mcp` verbs and exits 0.

To build the working tree instead:

```powershell
dotnet build Src/Cli/VeloxDev.Cli
dotnet build -c Release -p:VeloxDevLocalCore=true Src/Cli/VeloxDev.Cli
```

**Expected result:** the build produces `veloxdev.dll`; the `veloxdev` shim is the supported entry.

## Produce an archive

Create a small console project. It references `VeloxDev.Core`, builds a tree, and serializes it. The type parameter is concrete on purpose: serializing through a base or interface reference emits a root `$type`, while `tree.Serialize()` does not.

```powershell
dotnet new console -n ArchiveBuilder
cd ArchiveBuilder
dotnet add package VeloxDev.Core --version 12.3.0
```

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

**Expected result:** prints `wrote graph.json with 1 node(s)`, and `graph.json` exists.

## Add a manifest when types live elsewhere

Dependencies are declared in a sidecar named `<archive>.manifest.json`:

```json
{
  "assemblies": [ "lib/MyNodes.dll", "lib/MyNodes.Helpers.dll" ],
  "rootType": "MyCompany.ViewModels.MyTreeViewModel",
  "allowExecution": false
}
```

- `rootType` is needed when the document was serialized through a derived tree's own type; without it the CLI reads the graph into `TreeDefaultViewModel`.
- Assembly paths resolve relative to the manifest and may not escape its directory.
- `allowExecution` is an opt-in; without it (or `--allow-execution`) the execution tools are not on the MCP surface at all.
- `--assembly <path>` adds a dependency without editing the manifest.

**Expected result:** a document that names a type whose assembly was not loaded fails before deserialization with the type name and the remedy (`--assembly` or a manifest entry).

## Check the archive

```powershell
veloxdev run --archive graph.json --start 0 --timeout-ms 30000
```

**Expected result:** a JSON object with `status`, `outcome`, `attempts`, `failures`, the log and `data`; the process exits 0 when `status` is `ok`.
