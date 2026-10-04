# 00 · 前置条件

## 支持的目标

`VeloxDev.Core.Extension`（承载 `Agent/` 的项目）只声明一个目标框架：

```xml
<TargetFramework>netstandard2.0</TargetFramework>
```

来源：`Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。

因此本库可以落入任何消费 `netstandard2.0` 的项目。但它的 AI 依赖仅支持新式 .NET，所以宿主应面向当前版本的 .NET。随附的 demo（`Examples/Workflow/*`，通过 `Examples/Workflow/Common/Lib` 共享 agent 面板）与测试使用：

```xml
<TargetFramework>net10.0</TargetFramework>
```

来源：`Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj`。

`net10.0` 只是**被测试过**的配置，不是最低要求 —— 它是 demo 与测试编译所依据的版本。请把「满足 `Microsoft.Extensions.AI` 10.x 的新式 .NET」视为要求。

## SDK / 运行时与包

- **.NET SDK 10.0**（demo 与测试所用的工具链；参照机器上 `dotnet --version` 报告 `10.0.401`）。
- `VeloxDev.Core.Extension` 传递引入的包（来源：`VeloxDev.Core.Extension.csproj`）：

| 包 | 版本 | 用途 |
|---|---|---|
| `Microsoft.Agents.AI` | 1.22.0 | `AIAgent`、`AIContextProvider`、`ChatClientAgent`、管线中间件 |
| `Microsoft.Extensions.AI` | 10.10.0 | `AITool`、`AIFunction`、`AIFunctionFactory`、`IChatClient` |
| `ModelContextProtocol` | 2.2.0 | MCP 客户端 / stdio 与 HTTP 传输 |
| `Newtonsoft.Json` | 13.0.4 | 每个工具的紧凑 JSON 输出 |
| `CliWrap` | 3.10.5 | 启动本地 MCP 服务器的 `npm` / `pip` / `npx` |

- **`IChatClient` 实现** —— agent 运行在 `Microsoft.Extensions.AI` 之上。demo 构造一个 OpenAI 兼容客户端（`OpenAIClient` → `AsIChatClient()`），指向 `https://api.deepseek.com`；任何 `IChatClient` 都可以。

## 你必须提供的服务

| 服务 | 用于 | 获取 / 启动方式 |
|---|---|---|
| 一棵活的 `IWorkflowTreeViewModel` | 一切 —— 作用域绑定一棵树 | 用「工作流系统」特性构建；工具都作用于这个对象 |
| 一个 `IChatClient` | 运行任何对话 | 构造 OpenAI 兼容客户端；demo 从环境变量 `API_KEY_DEEPSEEK` 读取密钥 |
| `PATH` 上的 `node` / `npm`（npx 模式）或 `python` / `pip`（pip 模式） | 仅本地 MCP 服务器 | 安装 Node.js 或 Python；远程（`Http`）MCP 服务器不需要 |
| `SynchronizationContext` | 组件与 UI 绑定的宿主 | 从 UI 线程把 `SynchronizationContext.Current` 传给 `WithSynchronizationContext` |

## 哪些**不需要**模型

构建作用域（`tree.AsAgentScope()` … `ProvideProgressiveContextPrompt()`）、枚举工具集（`ProvideTools()` / `CreateAllTools()`）、挂载子系统（MCP / 技能 / 子代理）全部离线。**只有真正运行一轮对话** —— 调用 `agent.RunAsync(...)` —— 才会触达模型。验证页的运行声明会如实说明做了哪一件。

**预期结果：** 你有一个 `.NET 10` 宿主项目、一个 `IChatClient`、一棵活的 workflow 树，以及（可选）本地 MCP 服务器所需的 Node 或 Python。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。上面的目标框架与包版本读自 `VeloxDev.Core.Extension.csproj` 与 `VeloxDev.Core.Extension.Test.csproj`；未从本页构建任何宿主项目。
