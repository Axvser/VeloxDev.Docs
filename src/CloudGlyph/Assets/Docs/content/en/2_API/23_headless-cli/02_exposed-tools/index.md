# Exposed tools

The `mcp` verb publishes the workflow toolkit plus a small session-management layer. The tool names match the embedded agent's, so a model trained on the library recognizes them.

## Tool groups

| Group | Tools |
|---|---|
| Inspection | `GetWorkflowSummary`, `ListNodes`, `GetNodeDetail`, `GetFullTopology`, `GetTypeSchema`, `GetComponentContext`, `FindNodes`, `ListCreatableTypes`, `ValidateWorkflow`, `CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`, traversal and layout preview |
| Editing | `CreateNode`, `DeleteNode`, `CreateSlotOnNode`, `ConnectSlots` / `ConnectByProperty`, `DisconnectSlots`, `PatchNodeProperties`, `SetEnumSlotCollection`, slot collection edits, `Undo` / `Redo` |
| Execution (default) | `RunCompiledWorkflow`, `GetNodeResult`, and background `StartWorkflow` / `GetWorkflowJob` / `CancelWorkflowJob` / `ListWorkflowJobs` / `ClearFinishedJobs` |
| Execution (`--in-process-execution`) | `StartCompiledWorkflow`, `ContinueCompiledWorkflow`, `GetCompiledRunStatus`, `PauseCompiledRun`, `ResumeCompiledRun`, `StopCompiledRun`, `ListCompiledRuns`, `ExecuteNode`, `BroadcastNode` |
| Session | `ArchiveInfo`, `LoadArchive`, `SaveArchive`, `LoadAssemblies`, `GetCapabilities`, `GetAuditLog`, `ApplyBatch`, `SetRedirectOnError`, `ClearRedirectOnError` |
| Context | resources `veloxdev://archive/info` and `veloxdev://archive/manifest`, and the `workflow-operator` prompt |

## Gating

Execution tools exist only when `--allow-execution` is passed or the manifest sets `"allowExecution": true`. Without either, `ListNodes` still answers but no execution tool appears in the tool list.

Execution tools exist in two shapes because the isolation mode changes what can be done safely:

- **Worker mode** (default) runs each execution in a child process, so a crash kills only the worker. It exposes the job/handle tools and the synchronous run tools.
- **`--in-process-execution`** runs inside the server, which enables pause/resume/status on a live handle but means a bad node can take the server down.

## Session tools

| Tool | Effect |
|---|---|
| `ArchiveInfo` | Archive path, manifest state and counts. |
| `LoadArchive` | Switches the served document; unsaved edits are discarded. Refused under `--in-process-execution` and `--single-archive`. |
| `SaveArchive` | Writes compact JSON, backs the previous file up to `<path>.bak`, and accepts `dryRun`. |
| `LoadAssemblies` | Loads additional dependency assemblies. |
| `GetCapabilities` | Reports what the server allows: execution, in-process mode, workspace, redirect, plugins. |
| `GetAuditLog` | The tool-audit trail for the session. |
| `ApplyBatch` | Applies several edits under one call. |
| `SetRedirectOnError` / `ClearRedirectOnError` | Configures the host-level upstream fallback. |

## Context resources and prompt

| Name | Kind | Content |
|---|---|---|
| `veloxdev://archive/info` | resource | Archive summary. |
| `veloxdev://archive/manifest` | resource | The dependency manifest, when present. |
| `workflow-operator` | prompt | Operating instructions for the exposed tools. |

## Related

- [mcp command](../01_mcp-command/index.md) — the options that gate these tools.
- [Workflow Agent Toolkit](../../17_workflow-agent-tools/01_workflow-agent-toolkit/index.md) — the library toolkit these mirror.
