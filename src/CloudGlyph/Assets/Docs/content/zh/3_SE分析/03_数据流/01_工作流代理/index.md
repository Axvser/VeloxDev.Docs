# 数据流 —— 工作流代理

workflow-agent 特性通过 66 个无条件内置 `AITool`（外加条件交互/计划工具）操作一棵 GUI workflow 树，并在编译运行/结果工具中复用 GUI 自己的 `CompilerEx` 模型（`CompilerViewModel.CompileAsync` + `RuntimeEngine`）。下列每页用 PlantUML 追踪一条时序流，覆盖正常路径及其错误/异步分支。

| # | 流程 | 页面 |
|---|---|---|
| 1 | 宿主 → agent → 上下文提供器 → 作用域 → 工具包 → `TrackedAIFunction` → 共享 `ToolPipeline`（拒绝 / 确认）→ 工具体 → 组件命令；记账 + 对话记录 | [代理工具调用](00_代理工具调用/index.md) |
| 2 | `RequestSelection` / `RequestConfirmation` 交接到宿主 UI | [交互与确认](01_交互与确认/index.md) |
| 3 | MCP 服务器加载：运行时安装 → 传输 → JSON-RPC 握手 → `AITool[]`；单服务器错误隔离 | [MCP 服务器加载](02_MCP服务器加载/index.md) |
| 4 | `RunCompiledWorkflow`：`CompileRole.Root` 编译 + `RuntimeEngine` 驱动整条链 | [根链运行](03_根链运行/index.md) |
| 5 | `GetNodeResult`：`CompileRole.Terminal` 反向编译祖先锥 + “NOT reached”错误契约 | [终结点结果](04_终结点结果执行/index.md) |
| 6 | 工具抛异常 → JSON 错误结果 → Failure Handling Protocol（不静默重试） | [错误与恢复](05_错误与恢复/index.md) |
| 7 | `SpawnSubAgent`：能力收窄 + 向下授予 → 子作用域配置 → 后台运行 → 结算行；随后 `WaitSubAgents` 收集 | [子代理派发](06_子代理派发/index.md) |
| 8 | `StartCompiledWorkflow` → 轮询 `GetCompiledRunStatus` → `Pause`/`Resume` → `Stop` → 结束并退休 → `Continue` | [编译运行句柄生命周期](07_编译运行句柄生命周期/index.md) |

所有结果都是紧凑 JSON。工具绝不绕过组件命令/生命周期管线：变更经 `IWorkflow*ViewModel` 命令，因此 Core 的撤销/重做栈仍是唯一事实源。运行句柄家族增加每作用域的 `CompiledRun` 注册表与后台 `DriveAsync` 任务。

- 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`、`.../Workflow/WorkflowAgentScope.cs`、`.../Workflow/WorkflowStateTracker.cs`、`.../Workflow/WorkflowAgentContextProvider.cs`、`.../Pipelines/*`、`.../MCP/McpScope.cs`、`.../SubAgents/SubAgentScope.cs`、`.../Safety/*`。
