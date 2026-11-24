# 暴露的工具

`mcp` 动词发布工作流 toolkit 以及一小层会话管理。工具名与内嵌智能体一致，因此熟悉本库的模型能认出它们。

## 工具分组

| 分组 | 工具 |
|---|---|
| 检查 | `GetWorkflowSummary`、`ListNodes`、`GetNodeDetail`、`GetFullTopology`、`GetTypeSchema`、`GetComponentContext`、`FindNodes`、`ListCreatableTypes`、`ValidateWorkflow`、`CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`、遍历与布局预览 |
| 编辑 | `CreateNode`、`DeleteNode`、`CreateSlotOnNode`、`ConnectSlots` / `ConnectByProperty`、`DisconnectSlots`、`PatchNodeProperties`、`SetEnumSlotCollection`、槽集合编辑、`Undo` / `Redo` |
| 执行（默认） | `RunCompiledWorkflow`、`GetNodeResult`，以及后台 `StartWorkflow` / `GetWorkflowJob` / `CancelWorkflowJob` / `ListWorkflowJobs` / `ClearFinishedJobs` |
| 执行（`--in-process-execution`） | `StartCompiledWorkflow`、`ContinueCompiledWorkflow`、`GetCompiledRunStatus`、`PauseCompiledRun`、`ResumeCompiledRun`、`StopCompiledRun`、`ListCompiledRuns`、`ExecuteNode`、`BroadcastNode` |
| 会话 | `ArchiveInfo`、`LoadArchive`、`SaveArchive`、`LoadAssemblies`、`GetCapabilities`、`GetAuditLog`、`ApplyBatch`、`SetRedirectOnError`、`ClearRedirectOnError` |
| 上下文 | 资源 `veloxdev://archive/info` 与 `veloxdev://archive/manifest`，以及 `workflow-operator` 提示 |

## 闸控

执行工具仅在传入 `--allow-execution` 或清单设置 `"allowExecution": true` 时存在。两者都没有时，`ListNodes` 仍回答，但执行工具不出现在工具列表里。

执行工具有两种形状，因为隔离模式改变了能安全做什么：

- **worker 模式**（默认）在子进程中运行每次执行，崩溃只杀死 worker。它暴露作业/句柄工具与同步运行工具。
- **`--in-process-execution`** 在服务器内运行，从而启用活动句柄上的暂停/恢复/状态，但坏节点可能拖垮服务器。

## 会话工具

| 工具 | 效果 |
|---|---|
| `ArchiveInfo` | 存档路径、清单状态与计数。 |
| `LoadArchive` | 切换所服务的文档；未保存编辑被丢弃。在 `--in-process-execution` 与 `--single-archive` 下被拒绝。 |
| `SaveArchive` | 写出紧凑 JSON，把原文件备份到 `<path>.bak`，接受 `dryRun`。 |
| `LoadAssemblies` | 装载额外依赖程序集。 |
| `GetCapabilities` | 报告服务器允许什么：执行、进程内模式、工作区、重定向、插件。 |
| `GetAuditLog` | 会话的工具审计轨迹。 |
| `ApplyBatch` | 在一次调用中应用多个编辑。 |
| `SetRedirectOnError` / `ClearRedirectOnError` | 配置宿主级上游回退。 |

## 上下文资源与提示

| 名称 | 种类 | 内容 |
|---|---|---|
| `veloxdev://archive/info` | 资源 | 存档摘要。 |
| `veloxdev://archive/manifest` | 资源 | 依赖清单（存在时）。 |
| `workflow-operator` | 提示 | 暴露工具的操作说明。 |

## 相关

- [mcp 命令](../01_mcp命令/index.md) —— 闸控这些工具的选项。
- [工作流智能体 Toolkit](../../17_工作流智能体工具/01_工作流工具集/index.md) —— 这些工具对应的库 toolkit。
