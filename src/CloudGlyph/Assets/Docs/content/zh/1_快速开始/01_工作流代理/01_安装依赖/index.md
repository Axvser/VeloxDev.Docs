# 01 · 安装依赖

## 方案 A —— NuGet 包

agent 位于可选伴随包 `VeloxDev.Core.Extension`（版本 `10.0.0`）中，它会传递拉取 AI 栈。

```xml
<ItemGroup>
    <PackageReference Include="VeloxDev.Core.Extension" Version="10.0.0" />
</ItemGroup>
```

```bash
dotnet add package VeloxDev.Core.Extension --version 10.0.0
```

**预期结果：** 命令以 `0` 退出，且 `VeloxDev.Core.Extension`（连同其传递 AI 包）出现在项目的包列表 / `project.assets.json` 中。此时无需改动源码 —— 仅包本身即可编译。

## 方案 B —— 项目引用（本仓库内）

在本仓库内，每个示例与测试都直接引用源码项目，这也是 Debug 构建使用源码生成器而非已发布版本的原因：

```xml
<ItemGroup>
    <ProjectReference Include="..\..\..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj" />
</ItemGroup>
```

来源：`Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`。

库自身的 `Description` 仍写着 “60+ function-calling tools” —— 那是 README 的保守说法。当前源码中可核验的准确数量是 **66 个无条件分类工具** —— Query 20 + State 3 + Mutation 23 + Execution 12 + Command 2 + Graph 5 + Analytics 1 —— 外加至多两个 `Interaction` 工具和两个计划模式工具（仅在对应处理器配置时注册），再加始终添加的 `ResetToolCallLimit`。两个处理器都注册时，`ProvideTools()` 返回 **71**。

## 你会用到的命名空间

| 命名空间 | 内容 |
|---|---|
| `VeloxDev.AI` | 特性与反射辅助、`AgentLanguages`、`AgentObjectToolkit`、`AgentEmbeddedResources`、`AgentTelemetryExtensions`、事件参数 + 通知接口 |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope`、`AgentEx.AsAgentScope`、`WorkflowStateTracker`、`WorkflowAgentContextProvider`、`AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`、`WorkflowToolCategory`、`CommandInvoker`、`ComponentPatcher`、`TypeIntrospector` |
| `VeloxDev.AI.Safety` | `AgentPermissionMode`、`AgentPermissionPolicy`、`AgentPermissionRule`、`PermissionDecision`、`AgentActionCategory`、`ToolInvocation` |
| `VeloxDev.AI.MCP` | `McpScope`、`McpServerConfiguration`、`McpServerRunMode`、`McpServerStatus`、状态视图模型、`McpAgentToolkit` |
| `VeloxDev.AI.Skills` | `SkillScope`、`SkillAgentToolkit`、`SkillDescriptor`、`SkillState`、`SkillSourceKind`、`ISkillSource`、状态视图模型 |
| `VeloxDev.AI.SubAgents` | `SubAgentScope`、`SubAgentAgentToolkit`、`SubAgentAgentContextProvider`、`SubAgentState`/`SubAgentSummary`、树视图模型 |
| `VeloxDev.AI.Pipelines` | `AgentPipeline`、`AgentEvent`（及其子类）、`AgentTranscript`、`AgentTranscriptEntry`、`ToolPipeline`、`AgentPipelineAgent` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`、`AgentMemberViewModel` 及其四个具体成员 |

要点：**`VeloxDev.AI` 是由 `VeloxDev.Core`（特性/反射）与 `VeloxDev.Core.Extension`（其余）共用的单一命名空间。** `VeloxDev.Core.Extension` 下的 `Agent/` 文件夹是实现细节；它声明的公开类型位于上述命名空间，而不是 `VeloxDev.Core.Extension` 命名空间。

**预期结果：** 一个添加了 `using VeloxDev.AI.Workflow;` 的文件可以编译。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验（2026-10-18）。包 id/版本与依赖版本读自 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`；未从本页执行 `dotnet add package` / 构建。
