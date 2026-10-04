# 01 · Install & Add Dependencies

## Option A — NuGet package

The agent lives in the optional companion package `VeloxDev.Core.Extension` (version `10.0.0`), which pulls the AI stack transitively.

```xml
<ItemGroup>
    <PackageReference Include="VeloxDev.Core.Extension" Version="10.0.0" />
</ItemGroup>
```

```bash
dotnet add package VeloxDev.Core.Extension --version 10.0.0
```

**Expected result:** the command exits `0` and `VeloxDev.Core.Extension` (plus its transitive AI packages) appears in the project's package list / `project.assets.json`. No source changes are needed yet — the package alone compiles.

## Option B — Project reference (the repository itself)

Inside this repository every demo and test references the source project directly, which is what makes the Debug build use the source generator instead of the published one:

```xml
<ItemGroup>
    <ProjectReference Include="..\..\..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj" />
</ItemGroup>
```

Source: `Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`.

The library's own `Description` still says "60+ function-calling tools" — that is the README's understated figure. The exact, verifiable count in the current source is **68 built-in tools** across the ten `WorkflowToolCategory` groups — 66 unconditional plus up to two `Interaction` tools registered only when handlers are configured — and `ResetToolCallLimit` is always added on top of that.

## Namespaces you will use

| Namespace | Contains |
|---|---|
| `VeloxDev.AI` | attributes and reflection helpers, `AgentLanguages`, `AgentObjectToolkit`, `AgentEmbeddedResources`, `AgentTelemetryExtensions`, event args + notifier interfaces |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope`, `AgentEx.AsAgentScope`, `WorkflowStateTracker`, `WorkflowAgentContextProvider`, `AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`, `WorkflowToolCategory`, `CommandInvoker`, `ComponentPatcher`, `TypeIntrospector` |
| `VeloxDev.AI.MCP` | `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpServerStatus`, `McpSelfServiceLevel`, status view-models, `McpAgentToolkit` |
| `VeloxDev.AI.Skills` | `SkillScope`, `SkillAgentToolkit`, `SkillDescriptor`, `SkillState`, `SkillSourceKind`, `ISkillSource`, status view-models |
| `VeloxDev.AI.SubAgents` | `SubAgentScope`, `SubAgentAgentToolkit`, `SubAgentAgentContextProvider`, `SubAgentState`/`SubAgentSummary`, the tree view-models |
| `VeloxDev.AI.Pipelines` | `AgentPipeline`, `AgentEvent` (+ its subclasses), `AgentTranscript`, `AgentTranscriptEntry`, `ToolPipeline`, `AgentPipelineAgent` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`, `AgentMemberViewModel` and its four concrete members |

Keys: **`VeloxDev.AI` is a single namespace shared by both `VeloxDev.Core` (attributes/reflection) and `VeloxDev.Core.Extension` (everything else).** The `Agent/` folder under `VeloxDev.Core.Extension` is an implementation detail; the public types it declares live in the namespaces above, not in a `VeloxDev.Core.Extension` namespace.

**Expected result:** a file that adds `using VeloxDev.AI.Workflow;` compiles.

## Run declaration

- ⚠️ Not actually run — statically verified only. The package id/version and dependency versions are read from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`; the `dotnet add package` / build were not executed from this page.
