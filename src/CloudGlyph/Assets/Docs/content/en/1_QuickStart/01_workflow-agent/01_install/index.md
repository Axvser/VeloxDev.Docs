# Workflow Agent — Install & Add Dependencies

Add the package that carries the agent surface, then the extra packages you need to actually talk to an LLM.

## 1. Add `VeloxDev.Core.Extension`

```bash
dotnet add package VeloxDev.Core.Extension
```

`VeloxDev.Core` (the workflow core and the `CompilerEx` engine) is referenced transitively in Debug builds; in Release the NuGet package is used instead. Reference it explicitly when you only need the core types without the agent:

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** both packages appear in the `.csproj`; `dotnet restore` exits 0. `VeloxDev.Core.Extension` brings in `Microsoft.Extensions.AI`, `Microsoft.Agents.AI`, `ModelContextProtocol` (the MCP SDK), `CliWrap` and `Newtonsoft.Json` transitively (see `VeloxDev.Core.Extension.csproj`).

## 2. Add the LLM client packages (for a real conversation)

To build the `IChatClient` exactly like the demo you need the OpenAI integration on top:

```bash
dotnet add package Microsoft.Agents.AI.OpenAI
dotnet add package OpenAI
```

`Microsoft.Agents.AI.OpenAI` version 1.13.0 and `Microsoft.Bcl.AsyncInterfaces` are what `Examples/Workflow/Common/Lib/Lib.csproj` declares; use versions your chosen target framework supports. You also need an API key for an OpenAI-compatible endpoint (the demo reads `API_KEY_DEEPSEEK` and targets `https://api.deepseek.com`, model `deepseek-v4-flash`).

**Expected result:** the packages are in the `.csproj`; restoring resolves them; the environment variable for your endpoint key is set when you later run a conversation.

## 3. Reference in code

The namespaces you will use in the next pages are:

```csharp
using Microsoft.Agents.AI;              // ChatClientAgent, ChatClientAgentRunOptions, AgentSession
using Microsoft.Extensions.AI;          // IChatClient, AITool, ChatOptions
using VeloxDev.AI;                      // AgentLanguages, AgentToolCallEventArgs
using VeloxDev.AI.MCP;                  // McpScope, McpServerConfiguration, McpServerRunMode, McpAgentToolkit
using VeloxDev.AI.Workflow;             // AsAgentScope(), WorkflowAgentScope
using VeloxDev.WorkflowSystem;          // IWorkflowTreeViewModel
```

**Expected result:** a file with these usings compiles once the packages are restored.

## Run declaration

- ⚠️ Statically verified only. Package names, versions and transitives come from `VeloxDev.Core.Extension.csproj` and `Examples/Workflow/Common/Lib/Lib.csproj`; no build was run in this documentation pass.
