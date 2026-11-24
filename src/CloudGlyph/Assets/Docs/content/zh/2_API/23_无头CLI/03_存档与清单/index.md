# 存档与清单

CLI 读取库序列化器写出的文档，以及组件类型所在的程序集。它从不读工程文件。这让执行宿主独立于任何 GUI 框架，也让你能对编辑器保存的同一份文档做「改一下再跑」的循环。

## 存档

存档是由 `tree.Serialize()` 产出的文档，不是手写 JSON。通过具体树类型序列化可避免写出根 `$type`；通过基类或接口引用序列化会加上它。

```csharp
using System.IO;
using VeloxDev.Serialization;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(node);

File.WriteAllText("graph.json", tree.Serialize());
Console.WriteLine($"wrote graph.json with {tree.Nodes.Count} node(s)");
```

## 清单

依赖声明在名为 `<archive>.manifest.json` 的旁挂文件中。

```json
{
  "assemblies": [ "lib/MyNodes.dll", "lib/MyNodes.Helpers.dll" ],
  "rootType": "MyCompany.ViewModels.MyTreeViewModel",
  "allowExecution": false
}
```

| 字段 | 效果 |
|---|---|
| `assemblies` | 声明存档中节点、槽与连线类型的文件。路径相对清单解析，不得逃出清单目录。 |
| `rootType` | 文档序列化所用的具体树类型。不是 `TreeDefaultViewModel` 时需要；没有它时 CLI 把图读入 `TreeDefaultViewModel`。 |
| `allowExecution` | 执行工具的选择性加入。没有它（或 `--allow-execution`）时执行工具不在 MCP 表面。 |

`--assembly <path>` 无需编辑清单即可添加依赖。文档命名了未装载程序集中的类型时，会在反序列化前失败，并给出类型名与补救方式（`--assembly` 或清单条目）。

装载程序集会运行其模块初始化器，从而注册序列化读取器。因此清单与 `--assembly` 都是特权输入：只装载你信任的文件。

## 兼容性

- 针对比 CLI 自带更新 Core 构建的组件没问题。
- 较旧的组件支持到 Core 10.0.1。
- `VeloxDev.Core.Extension` 不是统一模型层，因此任何版本差异都作为风险报告。
- `--strict-plugin-versions` 拒绝 Core / Core.Extension 引用主版本不同的插件；默认装载并警告。

## 产出与运行

```powershell
dotnet new console -n ArchiveBuilder
cd ArchiveBuilder
dotnet add package VeloxDev.Core --version 12.3.0
dotnet run
veloxdev run --archive graph.json --start 0 --log-file run.log
veloxdev mcp --archive graph.json --allow-execution
```

**预期结果：** `ArchiveBuilder` 打印 `wrote graph.json with 1 node(s)`；两条 `veloxdev` 命令针对该文件运行。

## 相关

- [run 命令](../00_运行命令/index.md) —— 一次性消费存档。
- [mcp 命令](../01_mcp命令/index.md) —— 通过 stdio 服务它。
