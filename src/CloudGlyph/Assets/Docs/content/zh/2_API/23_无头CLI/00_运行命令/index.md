# run 命令

`veloxdev run` 执行一次存档并打印一个 JSON 对象。它是给人或 CI 用的一次性入口；长期运行的 `mcp` 动词另见其页。

## 语法

```text
veloxdev run --archive <graph.json> --start <nodeIndex> [options]
```

`--archive` 与 `--start` 必填。`--archive` 指向由库序列化器产出的文档，而非手写 JSON。

## 选项

| 选项 | 效果 |
|---|---|
| `--archive <path>` | 工作流文档。必填。 |
| `--start <index>` | 0 起始的编译入口节点，由 `ListNodes` 列出。`run` 必填。 |
| `--manifest <path>` | 存档清单。该文件存在时默认为 `<archive>.manifest.json`。 |
| `--assembly <path>` | 读取文档前装载的依赖程序集。可重复。 |
| `--assemblies <list>` | 分号或逗号分隔的程序集路径；重复 `--assembly` 的别名。 |
| `--root-type <name>` | 文档序列化所用的具体树类型（不是 `TreeDefaultViewModel` 时）。 |
| `--node-result` | 终止角色：计算 `--start` 节点及其祖先锥，而不是从它运行整条链。 |
| `--seed <text>` | 写入会话 `Data` 的负载。 |
| `--timeout-ms <n>` | 省略则等待。在此一次性路径上，超时报告 `status: error` 并退出 1。 |
| `--redirect-on-error <index>` | 对不实现 `IRedirectable` 的失败，宿主级回退到某上游节点。 |
| `--checkpoint-file <path>` | 通过 `FileCheckpointStore` 写检查点，使延续能跨进程存活。 |
| `--log-file <path>` | 追加运行日志行；结果把文件命名为 `logFile`。 |
| `--output-tree <path>` | 写出运行后的图；结果把它命名为 `stateFile`。 |
| `--workspace <dir>` | 把每个读写路径沙盒在此已存在目录下。 |
| `--help`、`-h` | 打印用法并退出 0。 |

## 输出

成功运行打印一个 JSON 对象，携带 `status`、`outcome`、`attempts`、`failures`、日志与 `data`。使用 `--output-tree` 时，`stateFile` 命名写出的图。写入失败时，`stateFileError` 携带原因。

```text
{"status":"ok","outcome":...,"attempts":...,"failures":[],"log":[],"data":...,"stateFile":"..."}
```

## 退出码

| 代码 | 含义 |
|---|---|
| `0` | `status` 为 `ok` **且**每个请求的输出都已写出。 |
| `1` | 运行失败、产物缺失，或输出树无法写出。 |
| `2` | 用法错误：未知动词或选项、缺少必填选项、或整数格式错误。 |

运行成功但 `--output-tree` 无法写出时退出 1 并报告 `stateFileError`；CI 任务不能指望解析 stderr 才发现产物缺失。

## 示例

```powershell
veloxdev run --archive graph.json --start 0 --log-file run.log
```

**预期结果：** 一个带 `"status":"ok"` 的 JSON 对象；退出 0。

## 相关

- [mcp 命令](../01_mcp命令/index.md) —— 长期运行的服务器。
- [存档与清单](../03_存档与清单/index.md) —— 产出文档。
