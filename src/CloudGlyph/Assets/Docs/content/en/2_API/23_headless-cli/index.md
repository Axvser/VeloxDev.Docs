# Headless CLI

`VeloxDev.Cli` is a .NET tool that hosts a VeloxDev workflow archive without a GUI. It has exactly two verbs:

- **`run`** — execute an archive once and print the result as JSON; for a human or CI.
- **`mcp`** — serve the library's own tool surface over stdio, so an MCP client can inspect, edit, compile and run the graph.

The CLI does not reimplement the workflow API. It loads the archive, lets `VeloxDev.Core.Extension` build its toolkit, and publishes those same tools. A fix to a tool is a fix in both the embedded agent and this server.

## Command surface

The public API of this feature is the `veloxdev` command line: two verbs, their options, exit codes, and the MCP tools the `mcp` verb exposes. The implementation types in `VeloxDev.Cli` are internal and are not part of the public surface.

## Pages

- [run command](00_run-command/index.md) — one-shot execution, options, output and exit codes.
- [mcp command](01_mcp-command/index.md) — stdio serving, isolation modes and workspace rules.
- [Exposed tools](02_exposed-tools/index.md) — the tool groups an MCP client sees.
- [Archive and manifest](03_archive-and-manifest/index.md) — what the CLI loads and how dependencies are declared.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the toolkit the CLI publishes over MCP.
- [MCP Integration](../20_mcp-integration/index.md) — MCP from the consuming side.
