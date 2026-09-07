# Workflow Agent — Prerequisites

The workflow-agent layer is a library surface you add on top of a **running workflow tree**. It has no GUI of its own, so everything below is usable from a headless console host as well as from a desktop demo.

## 1. Supported targets & tooling

- **Supported target** (from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`): `netstandard2.0`. The package is consumable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+ consumers.
- **SDK / runtime:** a modern .NET SDK. The in-repo demos run on `net10.0-windows` — a *tested* configuration, not a requirement. Pick a target the LLM/HTTP client libraries you use support (the OpenAI-compatible demo packages require a recent runtime).
- **Package manager:** NuGet / the `dotnet` CLI.
- **LLM client libraries:** `Microsoft.Extensions.AI` and `Microsoft.Agents.AI` arrive transitively with the package; an OpenAI-compatible `IChatClient` additionally needs `Microsoft.Agents.AI.OpenAI` and the `OpenAI` SDK (see the demo `Examples/Workflow/Common/Lib/Lib.csproj`).

**Expected result:** `dotnet --version` prints a version; a NuGet feed is reachable.

## 2. Services you must supply

- **A running workflow tree** — an `IWorkflowTreeViewModel` holding the graph you want the agent to control, exactly the object produced by the Workflow System Quick Start (compile & run forward, terminal compile, serialization). The demo builds one via a `TreeViewModel` and mounts it on a canvas.
- **An AI chat client** — an `IChatClient` from `Microsoft.Extensions.AI`. The demo builds one over the DeepSeek-compatible OpenAI endpoint (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`) using an `API_KEY_DEEPSEEK` environment variable, `OpenAIClient(...).GetChatClient("deepseek-v4-flash").AsIChatClient()`.
- **Optional: an MCP runtime** — only needed when you load Model Context Protocol servers. A local `npx` server requires Node.js; other run modes select their own runtime (`McpServerRunMode.Npm/Npx/Uvx/Dotnet/Pip/Exe/Http`). A remote `Http` server requires no local runtime at all.

**Expected result:** `tree` is non-null and its helper is installed; a chat client can be constructed from your key/endpoint (or is already injected for the tests).

## 3. What is out of scope here

This Quick Start covers the **agent control surface**: building the scope, hardening it, loading MCP tools, running a conversation, and driving the three execution models. Defining workflow components, connecting nodes and compiling graphs headlessly is the Workflow System Quick Start's job; this feature consumes that tree as given.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Prerequisite claims come from the project files (`VeloxDev.Core.Extension.csproj`, `Examples/Workflow/Common/Lib/Lib.csproj`) and the demo source.
