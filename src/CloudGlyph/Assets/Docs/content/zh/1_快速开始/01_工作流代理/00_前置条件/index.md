# 工作流代理 — 前置条件

工作流代理层是一个加在**运行中的工作流树**之上的库表面。它自身没有 GUI，所以下面的一切既能在无头控制台宿主里用，也能在桌面演示里用。

## 1. 支持目标与工具链

- **支持目标**（来自 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`）：`netstandard2.0`。该包可被 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+ 的消费者使用。
- **SDK / 运行时：** 现代 .NET SDK。仓库内演示运行于 `net10.0-windows` —— 只是*被验证过*的配置，不是要求。请选择你所用的 LLM/HTTP 客户端库支持的目标（OpenAI 兼容演示包需要较新的运行时）。
- **包管理器：** NuGet / `dotnet` CLI。
- **LLM 客户端库：** `Microsoft.Extensions.AI` 与 `Microsoft.Agents.AI` 会随本包传递引入；OpenAI 兼容的 `IChatClient` 还需要 `Microsoft.Agents.AI.OpenAI` 与 `OpenAI` SDK（见演示 `Examples/Workflow/Common/Lib/Lib.csproj`）。

**预期结果：** `dotnet --version` 打印出版本；NuGet 源可达。

## 2. 你必须提供的服务

- **一个运行中的工作流树** — 持有你想让代理控制的图的 `IWorkflowTreeViewModel`，也就是工作流系统快速入门（前向编译运行、Terminal 编译、序列化）产出的那个对象。演示用一个 `TreeViewModel` 构建并把它挂到画布上。
- **一个 AI 聊天客户端** — 来自 `Microsoft.Extensions.AI` 的 `IChatClient`。演示在 `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` 中基于 DeepSeek 兼容的 OpenAI 端点构建：读取 `API_KEY_DEEPSEEK` 环境变量，用 `OpenAIClient(...).GetChatClient("deepseek-v4-flash").AsIChatClient()`。
- **可选：MCP 运行时** — 只有当你加载 Model Context Protocol 服务器时才需要。本地 `npx` 服务器需要 Node.js；其它运行模式各自选择自己的运行时（`McpServerRunMode.Npm/Npx/Uvx/Dotnet/Pip/Exe/Http`）。远程 `Http` 服务器完全不需要本地运行时。

**预期结果：** `tree` 非空且其 helper 已安装；能从你的 key/endpoint 构造聊天客户端（或测试已注入一个）。

## 3. 本页范围之外

本快速入门覆盖**代理控制表面**：构建作用域、加固它、加载 MCP 工具、运行一轮对话、驱动三种执行模型。定义工作流组件、连接节点、无头编译运行图属于工作流系统快速入门的内容；本特性直接消费那棵给定的树。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。前置条件来自工程文件（`VeloxDev.Core.Extension.csproj`、`Examples/Workflow/Common/Lib/Lib.csproj`）与演示源码。
