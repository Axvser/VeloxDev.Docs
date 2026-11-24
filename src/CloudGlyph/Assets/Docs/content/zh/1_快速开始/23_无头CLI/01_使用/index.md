# 使用

## `run` 动词

```powershell
veloxdev run --archive graph.json --start 0 [--node-result] [--seed <text>] [--timeout-ms <n>] `
             [--redirect-on-error <index>] [--checkpoint-file <path>] [--log-file <path>] `
             [--output-tree <path>] [--workspace <dir>]
```

| 选项 | 作用 |
|---|---|
| `--start` | 0 基的编译入口，与 `ListNodes` 列出的索引一致；必填 |
| `--node-result` | 终端角色：计算该节点及其祖先锥，而不是从它开始跑整条链 |
| `--seed` | 写进会话 `Data` 的负载 |
| `--timeout-ms` | 省略则一直等待；在这条一次性路径上，超时报告 `status: error` 并以 1 退出 |
| `--redirect-on-error` | 对未实现 `IRedirectable` 的失败，提供上游节点作为宿主级回退 |
| `--checkpoint-file` | 通过 `FileCheckpointStore` 写检查点，续跑可跨进程 |
| `--log-file` | 追加运行日志；结果以 `logFile` 点名它 |
| `--output-tree` | 写出运行后的图；结果以 `stateFile` 点名它 |
| `--workspace` | 把一切读写路径沙箱在该目录下 |

进程在 `status` 为 `ok` **且**所有要求的产物都写出时以 **0** 退出；用法错误以 **2** 退出；运行失败或产物缺失以 **1** 退出。`--output-tree` 写不出时结果带 `stateFileError`，即使运行本身成功，退出码也是 1。

**预期结果：** `run` 打印一个 JSON 对象；缺少 `--start` 会以 2 退出并打印用法。

## `mcp` 动词

```powershell
veloxdev mcp --archive graph.json [--manifest <path>] [--assembly <path>]... `
             [--allow-execution] [--in-process-execution] [--strict-plugin-versions] `
             [--single-archive] [--no-assembly-copy] [--no-run-csv] `
             [--redirect-on-error <index>] [--checkpoint-file <path>] [--log-file <path>] `
             [--max-concurrent-runs <n>] [--worker-kill-grace-ms <n>] [--workspace <dir>]
```

标准输出是 JSON-RPC 流；所有日志走标准错误。节点代码绝不能写标准输出：在 worker 里会让结果不是 JSON，在进程内会破坏协议流。请通过 `IRuntimeContext.Log`（或 stderr）记录日志。

**预期结果：** MCP 客户端连上后，`ListNodes` 返回存档中的节点。

## 执行隔离

除非设置 `--in-process-execution`，执行工具会把当前图序列化到临时存档，并用当前程序集、重定向设置、检查点文件与日志文件启动一个 `veloxdev run` 子进程。刚才的编辑就是执行的内容，无需保存。

| 模式 | 性质 |
|---|---|
| 默认（worker） | 节点挂起、调用退出或原生库崩溃都只杀死 worker；服务器继续服务 |
| `--in-process-execution` | 更快，保留句柄/暂停/状态工具；坏节点会连服务器一起带走 |

`--max-concurrent-runs`（默认 2，`0` 表示不限）限制并发 worker。`--worker-kill-grace-ms`（默认 5000）是超时后服务器杀死 worker 树之前的兜底时间，之后回答 `outcome: Cancelled` 与 `timedOut`。

**预期结果：** 无视取消的 worker 仍会在宽限期后得到回应；服务器保持运行。

## 暴露的工具

| 组 | 工具 |
|---|---|
| 检查 | `GetWorkflowSummary`、`ListNodes`、`GetNodeDetail`、`GetFullTopology`、`GetTypeSchema`、`GetComponentContext`、`FindNodes`、`ListCreatableTypes`、`ValidateWorkflow`、`CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`、图遍历与布局预览 |
| 编辑 | `CreateNode`、`DeleteNode`、`CreateSlotOnNode`、`ConnectSlots` / `ConnectByProperty`、`DisconnectSlots`、`PatchNodeProperties`、`SetEnumSlotCollection`、槽集合编辑、`Undo` / `Redo` |
| 执行 | 默认：`RunCompiledWorkflow`、`GetNodeResult`，以及后台的 `StartWorkflow` / `GetWorkflowJob` / `CancelWorkflowJob` / `ListWorkflowJobs` / `ClearFinishedJobs` |
| 执行（`--in-process-execution`） | `StartCompiledWorkflow`、`ContinueCompiledWorkflow`、`GetCompiledRunStatus`、`PauseCompiledRun`、`ResumeCompiledRun`、`StopCompiledRun`、`ListCompiledRuns`、`ExecuteNode`、`BroadcastNode` |
| 会话 | `ArchiveInfo`、`LoadArchive`、`SaveArchive`、`LoadAssemblies`、`GetCapabilities`、`GetAuditLog`、`ApplyBatch`、`SetRedirectOnError`、`ClearRedirectOnError` |
| 上下文 | 资源 `veloxdev://archive/info` 与 `veloxdev://archive/manifest`，以及携带同一套操作规则的 `workflow-operator` 提示 |

执行工具只有在 `--allow-execution` 或清单中 `"allowExecution": true` 时才存在。

**预期结果：** 没有 `--allow-execution` 时 `ListNodes` 仍能回答，但工具列表里没有任何执行工具。

## 保存与切换文档

编辑工具只改内存中的图。`SaveArchive` 写紧凑 JSON，替换前把旧文档复制到 `<path>.bak`，并接受 `dryRun`：只报告字节数、格式与节点/链接数，不碰磁盘。

`LoadArchive` 在服务器继续运行时切换文档；旧图未保存的编辑会丢弃。它在 `--in-process-execution` 下被拒绝，因为运行句柄属于被替换的会话。`--single-archive` 完全拒绝 `LoadArchive`，让运行期 ID 保持稳定。

**预期结果：** `SaveArchive` 再 `LoadArchive` 能往返图；`--in-process-execution` 下的 `LoadArchive` 返回点名当前模式的拒绝。

## 客户端配置

```json
{
  "mcpServers": {
    "veloxdev": {
      "command": "dotnet",
      "args": [
        "C:/tools/VeloxDev.Cli/veloxdev.dll",
        "mcp",
        "--archive", "C:/work/graph.json",
        "--assembly", "C:/work/lib/MyNodes.dll",
        "--allow-execution"
      ]
    }
  }
}
```

开发时用 `dotnet run --project Src/Cli/VeloxDev.Cli -- mcp --archive ...`，参数形状相同。

**预期结果：** 客户端列出服务器工具，`ListNodes` 返回存档中的节点。

## 验证

1. `veloxdev --help` 以 0 退出并打印两个动词。
2. `veloxdev run --archive graph.json --start 0` 打印含 `"status":"ok"` 的 JSON 并以 0 退出。
3. 启动 `veloxdev mcp --archive graph.json --allow-execution`，连接客户端，调用 `GetWorkflowSummary`，再用 `dryRun: true` 调 `SaveArchive` 并读取报告的数量。
4. 把 `--workspace` 指向存档目录，再尝试保存到目录外；调用被拒绝。

## 完整代码

分两部分：产出存档的控制台工程，以及命令行。

```csharp
// ArchiveBuilder/Program.cs
using System.IO;
using VeloxDev.Serialization;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(node);

File.WriteAllText("graph.json", tree.Serialize());
Console.WriteLine($"wrote graph.json with {tree.Nodes.Count} node(s)");
```

```powershell
dotnet add ArchiveBuilder package VeloxDev.Core --version 12.3.0
dotnet run --project ArchiveBuilder
veloxdev run --archive graph.json --start 0 --log-file run.log
veloxdev mcp --archive graph.json --allow-execution
```

第一行作用于 `ArchiveBuilder` 工程；后两条在它的输出目录运行，`graph.json` 就写在那里。

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Cli/VeloxDev.Cli/CliOptions.cs`、`Program.cs`、`WorkflowSession.cs`、`WorkflowArchive.cs`、`McpHost.cs`、CLI README，以及 `Src/Test/Unit/Cli/VeloxDev.Cli.Test/CliOptionsTests.cs` 与 `InProcessExecutionTests.cs` 做了静态核对。安装工具与连接 MCP 客户端依赖环境，因此没有记录运行输出。
