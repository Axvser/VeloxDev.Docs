# 00 · Prerequisites

## Supported targets

`VeloxDev.Core.Extension` (the project that holds `Agent/`) declares a single target framework:

```
<TargetFramework>netstandard2.0</TargetFramework>
```

Source: `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.

The library therefore drops into anything that consumes `netstandard2.0`. Its AI dependencies, however, are modern-only, so a host should target a current .NET. The shipped demo (`Examples/Workflow/*`, which share the agent pane through `Examples/Workflow/Common/Lib`) and the tests build with:

```
<TargetFramework>net10.0</TargetFramework>
```

Source: `Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`.

That `net10.0` build is only the *tested* configuration, not the minimum — it is what the demo and tests were compiled against. Treat "a modern .NET that satisfies `Microsoft.Extensions.AI` 10.x" as the requirement.

## SDK / runtime and packages

- **.NET SDK 10.0** (the toolchain the demo and tests were built with; `dotnet --version` on the reference machine reports `10.0.401`).
- The packages `VeloxDev.Core.Extension` pulls transitively (Source: `VeloxDev.Core.Extension.csproj`):

| Package | Version | Why it is here |
|---|---|---|
| `Microsoft.Agents.AI` | 1.22.0 | `AIAgent`, `AIContextProvider`, `ChatClientAgent`, the pipeline middlewares |
| `Microsoft.Extensions.AI` | 10.10.0 | `AITool`, `AIFunction`, `AIFunctionFactory`, `IChatClient` |
| `ModelContextProtocol` | 2.2.0 | the MCP client / stdio + HTTP transports |
| `Newtonsoft.Json` | 13.0.4 | every tool's compact JSON output |
| `CliWrap` | 3.10.5 | launching `npm` / `pip` / `npx` for local MCP servers |

- **`IChatClient` implementation** — the agent runs over `Microsoft.Extensions.AI`. The demo constructs an OpenAI-compatible client (`OpenAIClient` → `AsIChatClient()`) pointed at `https://api.deepseek.com`; any `IChatClient` works.

## Services you must supply

| Service | Needed for | How to obtain / start it |
|---|---|---|
| A live `IWorkflowTreeViewModel` | everything — the scope binds one tree | build it with the workflow-system feature; the tools operate on this object |
| An `IChatClient` | running any conversation | construct an OpenAI-compatible client; the demo reads the key from the environment variable `API_KEY_DEEPSEEK` |
| `node` / `npm` (npx mode) or `python` / `pip` (pip mode) on `PATH` | local MCP servers only | install Node.js or Python; remote (`Http`) MCP servers need none |
| `SynchronizationContext` | hosts whose components are UI-bound | pass `SynchronizationContext.Current` from the UI thread to `WithSynchronizationContext` |

## What does **not** need a model

Building the scope (`tree.AsAgentScope()` … `ProvideProgressiveContextPrompt()`), enumerating the tool set (`ProvideTools()` / `CreateAllTools()`), and attaching subsystems (MCP / Skills / Sub-agents) are all offline. **Only actually running a conversation** — calling `agent.RunAsync(...)` — reaches the model. The Run Declaration on the verification page states honestly which of the two was done.

**Expected result:** you have a `.NET 10` host project, an `IChatClient`, a live workflow tree, and (optionally) Node or Python on `PATH` for local MCP servers.

## Run declaration

- ⚠️ Not actually run — statically verified only. The target framework and package versions above are read from `VeloxDev.Core.Extension.csproj` and `VeloxDev.Core.Extension.Test.csproj`; no host project was built from this page.
