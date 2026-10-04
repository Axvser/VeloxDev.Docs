# 数据流分析 —— 工作流代理

workflow-agent 通过 68 个内置 `AITool` 操控一棵 GUI workflow 树，且对其编译运行/结果工具复用 GUI 自有的 `CompilerEx` 模型（`CompilerViewModel.CompileAsync` + `RuntimeEngine`）。以下每页用 PlantUML 追踪一条序列流，覆盖正常路径与其错误/异步分支。

| # | 流 | 页 |
|---|---|---|
| 1 | 宿主 → agent → 上下文提供器 → 作用域 → 工具包 → `TrackedAIFunction` → 共享 `ToolPipeline`（拒绝/确认）→ 工具函数体 → 组件命令；记账 + 对话记录 | [工具调用与撤销](00_工具调用与撤销/index.md) |
| 2 | `RequestSelection` / `RequestConfirmation` 交互移交到宿主 UI | [交互与确认](01_交互与确认/index.md) |
| 3 | MCP 服务器加载：运行时安装 → 传输 → JSON-RPC 握手 → `AITool[]`；逐服务器错误隔离 | [MCP服务器加载](02_MCP服务器加载/index.md) |
| 4 | `RunCompiledWorkflow`：`CompileRole.Root` 编译 + `RuntimeEngine` 驱动整条链 | [Root链运行](03_Root链运行/index.md) |
| 5 | `GetNodeResult`：`CompileRole.Terminal` 反向编译祖先锥 + 「NOT reached」错误契约 | [Terminal结果执行](04_Terminal结果执行/index.md) |
| 6 | 工具抛异常 → JSON 错误结果 → 失败处理协议（不静默重试） | [错误与恢复](05_错误与恢复/index.md) |
| 7 | `SpawnSubAgent`：能力收窄 + 递减授予 → 子作用域配置 → 后台运行 → 落定行；然后 `WaitSubAgents` 收集 | [子代理派发](06_子代理派发/index.md) |
| 8 | `StartCompiledWorkflow` → 轮询 `GetCompiledRunStatus` → `Pause`/`Resume` → `Stop` → 结束并退休 → `Continue` | [编译运行句柄生命周期](07_编译运行句柄生命周期/index.md) |

所有结果都是紧凑 JSON（`Formatting.None`）。工具绝不绕过组件命令/生命周期管线：变更经 `IWorkflow*ViewModel` 命令，Core 的撤销/重做栈因此保持唯一事实源。运行句柄家族增加了一个每作用域的 `CompiledRun` 注册表与后台 `DriveAsync` 任务。

- 来源：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`、`.../Workflow/WorkflowAgentScope.cs`、`.../Workflow/WorkflowStateTracker.cs`、`.../Workflow/WorkflowAgentContextProvider.cs`、`.../Pipelines/*`、`.../MCP/McpScope.cs`、`.../SubAgents/SubAgentScope.cs`。
