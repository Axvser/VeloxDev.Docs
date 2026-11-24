# mcp 命令

`veloxdev mcp` 通过 stdio 发布库自己的工具面，让 MCP 客户端检查、编辑、编译并运行图。标准输出是 JSON-RPC 流；所有日志走标准错误。

## 语法

```text
veloxdev mcp --archive <graph.json> [options]
```

## 选项

| 选项 | 效果 |
|---|---|
| `--archive <path>` | 工作流文档。必填。 |
| `--manifest <path>` | 存档清单；存在时默认为 `<archive>.manifest.json`。 |
| `--assembly <path>` | 先装载的依赖程序集。可重复。 |
| `--allow-execution` | 暴露运行节点业务代码的工具。没有它时执行工具不在表面上。 |
| `--in-process-execution` | 在服务器内运行节点代码而非子进程。更快，保留句柄/暂停/状态工具；坏节点会拖垮服务器。 |
| `--single-archive` | 进程生命周期内只服务一个文档；`LoadArchive` 被拒绝，运行时 id 保持稳定。 |
| `--no-assembly-copy` | 从源目录装载依赖 DLL，而非逐进程副本。 |
| `--no-run-csv` | 不把执行结果写入 `tasks/<task>/runs/<timestamp>.csv`（默认开启）。 |
| `--strict-plugin-versions` | 拒绝 Core / Core.Extension 引用主版本不同的插件；默认装载并警告。 |
| `--redirect-on-error <index>` | 对不实现 `IRedirectable` 的节点提供宿主级上游回退。 |
| `--checkpoint-file <path>` | 把运行检查点写入文件而非内存；仅进程内执行。 |
| `--log-file <path>` | 追加每次运行的日志行。 |
| `--workspace <dir>` | 把每个读写路径限制在此已存在目录。 |
| `--max-concurrent-runs <n>` | 同时允许的 worker 进程数（默认 2；`0` = 不限）。多余调用等待槽位。 |
| `--worker-kill-grace-ms <n>` | 运行超时后杀死 worker 前的额外时间（默认 5000）。 |

## 输出纪律

标准输出是协议流。节点代码绝不能写 stdout：在 worker 中会让结果非 JSON，在进程内会破坏协议。通过 `IRuntimeContext.Log` 或标准错误记录日志。

## 执行隔离

除非设置 `--in-process-execution`，执行工具会把实时图序列化到临时存档，并用当前程序集、重定向设置、检查点文件与日志文件运行一个 `veloxdev run` 子进程。片刻前的编辑就是执行的内容，无需保存。

| 模式 | 性质 |
|---|---|
| 默认（worker） | 挂起、退出或原生崩溃的节点只杀死 worker；服务器继续服务。 |
| `--in-process-execution` | 更快，保留句柄/暂停/状态工具；坏节点会拖垮服务器。 |

忽略取消的 worker 在 `--worker-kill-grace-ms` 后仍会给出响应；服务器随后回答 `outcome: Cancelled` 并带 `timedOut`，继续运行。

## 保存与切换文档

编辑工具改变内存中的图。`SaveArchive` 写出紧凑 JSON，替换前把原文档复制到 `<path>.bak`，并接受 `dryRun` 以在不碰磁盘的情况下报告字节数、格式与节点/连线数。

`LoadArchive` 在服务器继续运行时切换文档；旧图的未保存编辑被丢弃。在 `--in-process-execution` 下被拒绝，因为运行句柄属于被替换的会话。`--single-archive` 完全拒绝 `LoadArchive`。

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

**预期结果：** 客户端列出服务器工具，`ListNodes` 调用返回存档的节点。

## 相关

- [暴露的工具](../02_暴露的工具/index.md) —— 客户端能调用什么。
- [run 命令](../00_运行命令/index.md) —— 一次性路径。
- [存档与清单](../03_存档与清单/index.md) —— 装载规则。
