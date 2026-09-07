# 数据流分析 — 工作流代理

工作流代理功能通过约 60 个 `AITool` 操作一张 GUI 工作流树；其编译 run/result 工具复用 GUI 自身的 `CompilerEx` 模型（`CompilerViewModel.CompileAsync` + `RuntimeEngine`）。下面每一页用 PlantUML 追踪一条时序流，覆盖正常路径及其错误/异步分支。

| # | 流程 | 页面 |
|---|---|---|
| 1 | 工具调用 → 受追踪包装 → 恰好一个组件命令 → 框架撤销栈；状态快照/差异 | [Agent 工具调用](00_工具调用与撤销/index.md) |
| 2 | `RequestSelection` / `RequestConfirmation` 与宿主 UI 的交互交接 | [交互与确认](01_交互与确认/index.md) |
| 3 | MCP 服务器加载：运行时安装 → 传输 → JSON-RPC 握手 → `AITool[]`；单服务器错误隔离 | [MCP 服务器加载](02_MCP服务器加载/index.md) |
| 4 | `RunCompiledWorkflow`：`CompileRole.Root` 编译 + `RuntimeEngine` 驱动整条链 | [Root 链运行](03_Root链运行/index.md) |
| 5 | `GetNodeResult`：`CompileRole.Terminal` 反向编译祖先锥 + “未到达”错误契约 | [Terminal 结果](04_Terminal结果执行/index.md) |
| 6 | 工具抛错 → JSON 错误结果 → 失败处理协议（不静默重试循环） | [错误与恢复](05_错误与恢复/index.md) |

所有结果都是紧凑 JSON（`Formatting.None`）。工具绝不绕过组件命令/生命周期管线：变更都经 `IWorkflow*ViewModel` 命令，使 Core 的撤销/重做栈保持唯一真相源。

- 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`、`.../Workflow/WorkflowAgentScope.cs`、`.../Workflow/WorkflowStateTracker.cs`、`.../Agent/MCP/McpScope.cs`。
