# 工作流代理 — 安装依赖

先添加承载代理表面的包，再添加你真正与 LLM 对话所需的额外包。

## 1. 添加 `VeloxDev.Core.Extension`

```bash
dotnet add package VeloxDev.Core.Extension
```

`VeloxDev.Core`（工作流核心与 `CompilerEx` 引擎）在 Debug 下传递引用；Release 下改用 NuGet 包。当只需要核心类型而不需要代理时显式引用：

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 两个包出现在 `.csproj` 中；`dotnet restore` 退出码为 0。`VeloxDev.Core.Extension` 会传递引入 `Microsoft.Extensions.AI`、`Microsoft.Agents.AI`、`ModelContextProtocol`（MCP SDK）、`CliWrap` 与 `Newtonsoft.Json`（见 `VeloxDev.Core.Extension.csproj`）。

## 2. 添加 LLM 客户端包（进行真实对话时）

要像演示那样构建 `IChatClient`，需要在其上加一层 OpenAI 集成：

```bash
dotnet add package Microsoft.Agents.AI.OpenAI
dotnet add package OpenAI
```

`Microsoft.Agents.AI.OpenAI` 1.13.0 与 `Microsoft.Bcl.AsyncInterfaces` 正是 `Examples/Workflow/Common/Lib/Lib.csproj` 声明的依赖；请使用你的目标框架支持的版本。此外需要一个 OpenAI 兼容端点的 API key（演示读取 `API_KEY_DEEPSEEK`，目标是 `https://api.deepseek.com`，模型 `deepseek-v4-flash`）。

**预期结果：** 包出现在 `.csproj` 中；还原成功；稍后运行对话时已设置好端点 key 的环境变量。

## 3. 在代码中引用

后续页面会用到的命名空间如下：

```csharp
using Microsoft.Agents.AI;              // ChatClientAgent、ChatClientAgentRunOptions、AgentSession
using Microsoft.Extensions.AI;          // IChatClient、AITool、ChatOptions
using VeloxDev.AI;                      // AgentLanguages、AgentToolCallEventArgs
using VeloxDev.AI.MCP;                  // McpScope、McpServerConfiguration、McpServerRunMode、McpAgentToolkit
using VeloxDev.AI.Workflow;             // AsAgentScope()、WorkflowAgentScope
using VeloxDev.WorkflowSystem;          // IWorkflowTreeViewModel
```

**预期结果：** 还原完成后，含这些 using 的文件可以编译。

## 运行声明

- ⚠️ 仅静态核验。包名、版本与传递依赖取自 `VeloxDev.Core.Extension.csproj` 与 `Examples/Workflow/Common/Lib/Lib.csproj`；本次文档编写未做任何构建。
