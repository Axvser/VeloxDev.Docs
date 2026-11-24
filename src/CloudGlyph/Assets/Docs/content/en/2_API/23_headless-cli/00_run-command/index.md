# run command

`veloxdev run` executes an archive once and prints one JSON object. It is the one-shot entry for a human or CI; the long-lived `mcp` verb is documented separately.

## Syntax

```text
veloxdev run --archive <graph.json> --start <nodeIndex> [options]
```

`--archive` and `--start` are required. `--archive` names a document produced by the library's serializer, not hand-written JSON.

## Options

| Option | Effect |
|---|---|
| `--archive <path>` | Workflow document. Required. |
| `--start <index>` | 0-based compile entry node, as listed by `ListNodes`. Required for `run`. |
| `--manifest <path>` | Archive manifest. Defaults to `<archive>.manifest.json` when that file exists. |
| `--assembly <path>` | A dependency assembly to load before the document is read. Repeatable. |
| `--assemblies <list>` | Semicolon- or comma-separated assembly paths; an alias for repeating `--assembly`. |
| `--root-type <name>` | Concrete tree type the document was serialized from, when it is not `TreeDefaultViewModel`. |
| `--node-result` | Terminal role: compute the node at `--start` and its ancestor cone instead of running the chain from it. |
| `--seed <text>` | Payload written to the session's `Data`. |
| `--timeout-ms <n>` | Omit to wait. On this one-shot path a timeout reports `status: error` and exits 1. |
| `--redirect-on-error <index>` | Host-level fallback to an upstream node for a failure that does not implement `IRedirectable`. |
| `--checkpoint-file <path>` | Write checkpoints through `FileCheckpointStore`, so a continuation survives the process. |
| `--log-file <path>` | Append run log lines; the result names the file as `logFile`. |
| `--output-tree <path>` | Write the post-run graph; the result names it as `stateFile`. |
| `--workspace <dir>` | Sandbox every read and write path under this existing directory. |
| `--help`, `-h` | Print usage and exit 0. |

## Output

A successful run prints a JSON object carrying `status`, `outcome`, `attempts`, `failures`, the log and `data`. With `--output-tree`, `stateFile` names the written graph. When that write fails, `stateFileError` carries the reason.

```text
{"status":"ok","outcome":...,"attempts":...,"failures":[],"log":[],"data":...,"stateFile":"..."}
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | `status` is `ok` **and** every requested output was written. |
| `1` | The run failed, an artifact was missing, or the output tree could not be written. |
| `2` | Usage error: unknown verb or option, missing required option, or a malformed integer. |

A run that succeeds but whose `--output-tree` cannot be written exits 1 and reports `stateFileError`; a CI job cannot be expected to parse stderr to notice a missing artifact.

## Example

```powershell
veloxdev run --archive graph.json --start 0 --log-file run.log
```

**Expected result:** one JSON object with `"status":"ok"`; exit 0.

## Related

- [mcp command](../01_mcp-command/index.md) — the long-lived server.
- [Archive and manifest](../03_archive-and-manifest/index.md) — producing the document.
