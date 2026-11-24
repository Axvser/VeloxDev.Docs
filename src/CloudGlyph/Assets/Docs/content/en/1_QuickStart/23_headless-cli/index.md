# Headless CLI

`VeloxDev.Cli` is a .NET tool that hosts a VeloxDev workflow archive without a GUI. It has exactly two verbs:

- **`run`** — execute an archive once and print the result as JSON; for a human or CI.
- **`mcp`** — serve the library's own tool surface over stdio, so an MCP client can inspect, edit, compile and run the graph.

The CLI does not reimplement the workflow API. It loads the archive, lets `VeloxDev.Core.Extension` build its toolkit, and publishes those same tools. A fix to a tool is a fix in both the embedded agent and this server.

## What you will build

- an archive produced by `tree.Serialize()` plus a tiny dependency manifest;
- a one-shot `veloxdev run` and its JSON result;
- a stdio MCP server configured in a client's `.mcp.json`.

## Pages

- [Setup](00_setup/index.md) — prerequisites, installation, and producing the archive.
- [Usage](01_usage/index.md) — the `run` and `mcp` verbs, execution isolation, the exposed tools, and the complete sequence.

## Why an archive and not a project

The CLI reads what the library's serializer wrote, plus the assemblies its component types live in. It never reads a project file. That keeps the execution host independent of any GUI framework and makes an edit-and-run loop possible against the same document the editor saves.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the toolkit the CLI publishes over MCP.
- [MCP Integration](../20_mcp-integration/index.md) — MCP from the consuming side.
