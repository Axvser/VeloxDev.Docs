# mcp command

`veloxdev mcp` serves the library's own tool surface over stdio, so an MCP client can inspect, edit, compile and run the graph. Standard output is the JSON-RPC stream; all logging goes to standard error.

## Syntax

```text
veloxdev mcp --archive <graph.json> [options]
```

## Options

| Option | Effect |
|---|---|
| `--archive <path>` | Workflow document. Required. |
| `--manifest <path>` | Archive manifest; defaults to `<archive>.manifest.json` when present. |
| `--assembly <path>` | A dependency assembly to load first. Repeatable. |
| `--allow-execution` | Expose the tools that run node business code. Without it, execution tools are absent from the surface. |
| `--in-process-execution` | Run node code inside the server instead of a child process. Faster, keeps the handle/pause/status tools; a bad node takes the server down. |
| `--single-archive` | Serve exactly one document for the process's life; `LoadArchive` is refused, so runtime ids stay stable. |
| `--no-assembly-copy` | Load dependency DLLs from their source directory instead of a per-process copy. |
| `--no-run-csv` | Do not write execution results to `tasks/<task>/runs/<timestamp>.csv` (on by default). |
| `--strict-plugin-versions` | Refuse a plugin whose Core / Core.Extension reference has a different major version; the default loads it and warns. |
| `--redirect-on-error <index>` | Host-level upstream fallback for a node that does not implement `IRedirectable`. |
| `--checkpoint-file <path>` | Keep run checkpoints in a file instead of memory; in-process execution only. |
| `--log-file <path>` | Append every run's log lines. |
| `--workspace <dir>` | Restrict every read and write path to this existing directory. |
| `--max-concurrent-runs <n>` | Worker processes allowed at once (default 2; `0` = unlimited). Excess calls wait for a slot. |
| `--worker-kill-grace-ms <n>` | Extra time after a run's timeout before the worker is killed (default 5000). |

## Output discipline

Standard output is the protocol stream. Node code must never write to stdout: in a worker it makes the result non-JSON, and in-process it corrupts the protocol. Log through `IRuntimeContext.Log` or standard error.

## Execution isolation

Unless `--in-process-execution` is set, execution tools serialize the live graph to a temporary archive and run a `veloxdev run` child with the current assemblies, redirect setting, checkpoint file and log file. An edit made a moment ago is what executes, without saving.

| Mode | Property |
|---|---|
| default (worker) | A hanging, exiting or native-crashing node kills only the worker; the server keeps serving. |
| `--in-process-execution` | Faster and keeps the handle/pause/status tools; a bad node takes the server down. |

A worker that ignores cancellation still yields a response after `--worker-kill-grace-ms`; the server then answers `outcome: Cancelled` with `timedOut` and stays up.

## Saving and switching documents

Editing tools change the in-memory graph. `SaveArchive` writes compact JSON, copies the previous document to `<path>.bak` before replacing it, and accepts `dryRun` to report byte count, format and node/link counts without touching disk.

`LoadArchive` switches documents while the server keeps running; unsaved edits to the old graph are discarded. It is refused under `--in-process-execution`, where run handles belong to the session being replaced. `--single-archive` refuses `LoadArchive` entirely.

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

**Expected result:** the client lists the server's tools and a `ListNodes` call returns the archive's nodes.

## Related

- [Exposed tools](../02_exposed-tools/index.md) — what the client can call.
- [run command](../00_run-command/index.md) — the one-shot path.
- [Archive and manifest](../03_archive-and-manifest/index.md) — loading rules.
