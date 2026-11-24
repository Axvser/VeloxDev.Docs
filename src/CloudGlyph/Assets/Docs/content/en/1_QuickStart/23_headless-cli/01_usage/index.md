# Usage

## The `run` verb

```powershell
veloxdev run --archive graph.json --start 0 [--node-result] [--seed <text>] [--timeout-ms <n>] `
             [--redirect-on-error <index>] [--checkpoint-file <path>] [--log-file <path>] `
             [--output-tree <path>] [--workspace <dir>]
```

| Option | Effect |
|---|---|
| `--start` | 0-based compile entry, as listed by `ListNodes`; required |
| `--node-result` | terminal role: compute the node and its ancestor cone instead of running the chain from it |
| `--seed` | payload written to the session's `Data` |
| `--timeout-ms` | omit to wait; on this one-shot path a timeout reports `status: error` and exits 1 |
| `--redirect-on-error` | host-level fallback to an upstream node for a failure that does not implement `IRedirectable` |
| `--checkpoint-file` | write checkpoints through `FileCheckpointStore` so a continuation survives the process |
| `--log-file` | append run log lines; the result names it as `logFile` |
| `--output-tree` | write the post-run graph; the result names it as `stateFile` |
| `--workspace` | sandbox every read and write path under this directory |

The process exits **0** when `status` is `ok` **and** every requested output was written, **2** for a usage error, and **1** for a failed run or a missing artifact. When `--output-tree` cannot be written, the result carries `stateFileError` and the exit code is 1 even if the run itself succeeded.

**Expected result:** `run` prints one JSON object; a missing `--start` exits 2 with the usage text.

## The `mcp` verb

```powershell
veloxdev mcp --archive graph.json [--manifest <path>] [--assembly <path>]... `
             [--allow-execution] [--in-process-execution] [--strict-plugin-versions] `
             [--single-archive] [--no-assembly-copy] [--no-run-csv] `
             [--redirect-on-error <index>] [--checkpoint-file <path>] [--log-file <path>] `
             [--max-concurrent-runs <n>] [--worker-kill-grace-ms <n>] [--workspace <dir>]
```

Standard output is the JSON-RPC stream; all logging goes to standard error. Node code must never write to stdout: in a worker it makes the result non-JSON, and in-process it corrupts the protocol stream. Log through `IRuntimeContext.Log` (or stderr).

**Expected result:** an MCP client connects and `ListNodes` returns the archive's nodes.

## Execution isolation

Unless `--in-process-execution` is set, execution tools serialize the live graph to a temporary archive and run a `veloxdev run` child with the current assemblies, redirect setting, checkpoint file and log file. An edit made a moment ago is what executes, without saving.

| Mode | Property |
|---|---|
| default (worker) | a hanging, exiting or native-crashing node kills only the worker; the server keeps serving |
| `--in-process-execution` | faster and keeps the handle/pause/status tools; a bad node takes the server down |

`--max-concurrent-runs` (default 2, `0` = unlimited) bounds workers. `--worker-kill-grace-ms` (default 5000) is the backstop after a timeout before the server kills the worker tree and answers `outcome: Cancelled` with `timedOut`.

**Expected result:** a worker that ignores cancellation still yields a response after the grace period; the server stays up.

## Tools exposed

| Group | Tools |
|---|---|
| Inspection | `GetWorkflowSummary`, `ListNodes`, `GetNodeDetail`, `GetFullTopology`, `GetTypeSchema`, `GetComponentContext`, `FindNodes`, `ListCreatableTypes`, `ValidateWorkflow`, `CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`, traversal and layout preview |
| Editing | `CreateNode`, `DeleteNode`, `CreateSlotOnNode`, `ConnectSlots` / `ConnectByProperty`, `DisconnectSlots`, `PatchNodeProperties`, `SetEnumSlotCollection`, slot collection edits, `Undo` / `Redo` |
| Execution | default: `RunCompiledWorkflow`, `GetNodeResult`, plus background `StartWorkflow` / `GetWorkflowJob` / `CancelWorkflowJob` / `ListWorkflowJobs` / `ClearFinishedJobs` |
| Execution (`--in-process-execution`) | `StartCompiledWorkflow`, `ContinueCompiledWorkflow`, `GetCompiledRunStatus`, `PauseCompiledRun`, `ResumeCompiledRun`, `StopCompiledRun`, `ListCompiledRuns`, `ExecuteNode`, `BroadcastNode` |
| Session | `ArchiveInfo`, `LoadArchive`, `SaveArchive`, `LoadAssemblies`, `GetCapabilities`, `GetAuditLog`, `ApplyBatch`, `SetRedirectOnError`, `ClearRedirectOnError` |
| Context | resources `veloxdev://archive/info` and `veloxdev://archive/manifest`, and the `workflow-operator` prompt |

Execution tools exist only with `--allow-execution` or `"allowExecution": true` in the manifest.

**Expected result:** without `--allow-execution`, `ListNodes` still answers but no execution tool appears in the tool list.

## Saving and switching documents

Editing tools change the in-memory graph. `SaveArchive` writes compact JSON, copies the previous document to `<path>.bak` before replacing it, and accepts `dryRun` to report byte count, format and node/link counts without touching disk.

`LoadArchive` switches documents while the server keeps running; unsaved edits to the old graph are discarded. It is refused under `--in-process-execution`, where run handles belong to the session being replaced. `--single-archive` refuses `LoadArchive` entirely so runtime IDs stay stable.

**Expected result:** `SaveArchive` followed by `LoadArchive` round-trips the graph; `LoadArchive` under `--in-process-execution` returns a refusal naming the mode.

## Client configuration

```json
{
  "mcpServers": {
    "veloxdev": {
      "command": "dotnet",
      "args": [
        "C:/tools/VeloxDev.Cli/veloxdev.dll",
        "mcp",
        "--archive", "C:/work/graph.json",
        "--assembly", "C:/work/lib/MyNodes.dll",
        "--allow-execution"
      ]
    }
  }
}
```

For development, `dotnet run --project Src/Cli/VeloxDev.Cli -- mcp --archive ...` uses the same argument shape.

**Expected result:** the client lists the server's tools and a `ListNodes` call returns the archive's nodes.

## Verification

1. `veloxdev --help` exits 0 and prints both verbs.
2. `veloxdev run --archive graph.json --start 0` prints a JSON object with `"status":"ok"` and exits 0.
3. Start `veloxdev mcp --archive graph.json --allow-execution`, connect a client, call `GetWorkflowSummary`, then `SaveArchive` with `dryRun: true` and read the reported counts.
4. Point `--workspace` at the archive directory and try `SaveArchive` outside it; the call is refused.

## Complete code

Two parts: the archive producer (a console project) and the commands.

```csharp
// ArchiveBuilder/Program.cs
using System.IO;
using VeloxDev.Serialization;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(node);

File.WriteAllText("graph.json", tree.Serialize());
Console.WriteLine($"wrote graph.json with {tree.Nodes.Count} node(s)");
```

```powershell
dotnet add ArchiveBuilder package VeloxDev.Core --version 12.3.0
dotnet run --project ArchiveBuilder
veloxdev run --archive graph.json --start 0 --log-file run.log
veloxdev mcp --archive graph.json --allow-execution
```

The first line targets the `ArchiveBuilder` project; the last two run from its output directory, where `graph.json` was written.

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Cli/VeloxDev.Cli/CliOptions.cs`, `Program.cs`, `WorkflowSession.cs`, `WorkflowArchive.cs`, `McpHost.cs`, the CLI README, and the tests `Src/Test/Unit/Cli/VeloxDev.Cli.Test/CliOptionsTests.cs` and `InProcessExecutionTests.cs`. Installing the tool and connecting an MCP client are environment-dependent, so no run output is recorded.
