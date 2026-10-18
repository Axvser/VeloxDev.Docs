# 00 · 前置条件

## 支持的目标

持有 `Agent/` 的项目 `VeloxDev.Core.Extension` 声明了两个目标框架：

```text
<TargetFrameworks>netstandard2.0;net8.0</TargetFrameworks>
```

来源：`Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。`net8.0` 那一档承载裁剪/AOT 契约（`IsAotCompatible=true`）；`netstandard2.0` 是覆盖面更宽的构建。它的 AI 依赖只支持现代 .NET，因此宿主应面向当前 .NET。仓库内的示例（`Examples/Workflow/*`，通过 `Examples/Workflow/Common/Lib` 共享 agent 面板）与测试使用：

```text
<TargetFramework>net10.0</TargetFramework>
```

来源：`Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`。

该 `net10.0` 构建只是**已测试**配置，不是最低要求 —— 它是示例与测试编译时所用的目标。把「满足 `Microsoft.Extensions.AI` 10.x 的现代 .NET（`net8.0` 或更高）」当作要求。

## SDK / 运行时与包

- **.NET SDK 8.0+** —— `net8.0` 目标承载 AI 栈的现代 API；`netstandard2.0` 面向较旧的消费者。仓库示例与测试用 SDK `10.0.x` 构建（参考机器的 `dotnet --version` 为 `10.0.401`），属**已测试**配置而非最低版本。
- `VeloxDev.Core.Extension` 传递拉取的包（来源：`VeloxDev.Core.Extension.csproj`）：

| 包 | 版本 | 用途 |
|---|---|---|
| `Microsoft.Agents.AI` | 1.22.0 | `AIAgent`、`AIContextProvider`、`ChatClientAgent`、管线中间件 |
| `Microsoft.Extensions.AI` | 10.10.0 | `AITool`、`AIFunction`、`AIFunctionFactory`、`IChatClient` |
| `ModelContextProtocol` | 2.2.0 | MCP 客户端 / stdio + HTTP 传输 |
| `CliWrap` | 3.10.5 | 为本地 MCP 服务器启动 `npm` / `pip` / `npx` |

每个工具的紧凑 JSON 输出由归档引擎自己的 JSON 树（`VeloxJsonObject` / `VeloxJsonValue.ToJson`）构建，它随 `VeloxDev.Core` 提供 —— Agent 不额外引入 JSON 包。

- **`IChatClient` 实现** —— agent 运行在 `Microsoft.Extensions.AI` 之上。示例构造一个 OpenAI 兼容客户端（`OpenAIClient` → `AsIChatClient()`），指向 `https://api.deepseek.com`；任何 `IChatClient` 均可。

## 你必须提供的服务

| 服务 | 用于 | 如何获取 / 启动 |
|---|---|---|
| 一棵活的 `IWorkflowTreeViewModel` | 全部 —— 作用域绑定一棵树 | 用「工作流系统」特性构建；工具作用于该对象 |
| 一个 `IChatClient` | 运行任何对话 | 构造 OpenAI 兼容客户端；示例从环境变量 `API_KEY_DEEPSEEK` 读取密钥 |
| `PATH` 上的 `node` / `npm`（npx 模式）或 `python` / `pip`（pip 模式） | 仅本地 MCP 服务器 | 安装 Node.js 或 Python；远程（`Http`）MCP 服务器无需 |
| `SynchronizationContext` | 组件与 UI 绑定的宿主 | 从 UI 线程把 `SynchronizationContext.Current` 传给 `WithSynchronizationContext` |

## 哪些**不**需要模型

构建作用域（`tree.AsAgentScope()` … `ProvideProgressiveContextPrompt()`）、枚举工具集（`ProvideTools()` / `CreateAllTools()`）、挂载子系统（MCP / 技能 / 子代理）全都离线。**只有真正运行对话** —— 调用 `agent.RunAsync(...)` —— 才会触达模型。验证页的运行声明会如实说明做了哪一项。

**预期结果：** 你有一个 .NET 8+ 宿主项目、一个 `IChatClient`、一棵活的 workflow 树，以及（可选）`PATH` 上的 Node 或 Python 供本地 MCP 服务器使用。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验（2026-10-18）。上述目标框架与包版本读自 `VeloxDev.Core.Extension.csproj` 与 `VeloxDev.Core.Extension.Test.csproj`；未从本页构建任何宿主项目。
