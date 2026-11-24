# 无头 CLI

`VeloxDev.Cli` 是一个 .NET 工具，在没有界面的情况下承载 VeloxDev 工作流存档。它只有两个动词：

- **`run`**——执行一次存档并以 JSON 打印结果；给人或 CI 用。
- **`mcp`**——通过 stdio 发布库自己的工具面，让 MCP 客户端检查、编辑、编译并运行图。

CLI 不重新实现工作流 API。它装载存档，让 `VeloxDev.Core.Extension` 建立自己的 toolkit，然后把同一批工具发布出去。修一个工具，内嵌智能体与这个服务器会同时受益。

## 命令表面

本功能的公共 API 就是 `veloxdev` 命令行：两个动词、它们的选项、退出码，以及 `mcp` 动词暴露的 MCP 工具。`VeloxDev.Cli` 中的实现类型是 internal，不属于公共表面。

## 页面

- [run 命令](00_运行命令/index.md) —— 一次性执行、选项、输出与退出码。
- [mcp 命令](01_mcp命令/index.md) —— stdio 服务、隔离模式与工作区规则。
- [暴露的工具](02_暴露的工具/index.md) —— MCP 客户端看到的工具分组。
- [存档与清单](03_存档与清单/index.md) —— CLI 装载什么，依赖如何声明。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— CLI 通过 MCP 发布的 toolkit。
- [MCP 集成](../20_MCP集成/index.md) —— 从消费方看 MCP。
