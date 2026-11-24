# 安装准备

## 前置条件

- **运行时：** .NET 8.0 或更新。工具以 `net8.0` 为目标并设置 `RollForward=LatestMajor`，只装了 .NET 9 或 10 的机器也能运行。用 `dotnet --list-runtimes` 检查。
- **包：** `VeloxDev.Cli` 12.0.0，内含 `VeloxDev.Core` 与 `VeloxDev.Core.Extension`。
- **存档：** 由 `tree.Serialize()` 产出的文档，不是手写 JSON。
- **组件程序集：** 声明存档里节点、槽与链接类型的文件。装载程序集会运行其模块初始化器并注册序列化读写器——只装载你信任的文件。
- **兼容性：** 用比 CLI 内嵌版本更新的 Core 构建组件没有问题；更旧的 Core 最低支持到 10.0.1。`VeloxDev.Core.Extension` 不是统一的模型层，任何版本差异都会被报告为风险。

## 安装

```powershell
dotnet --info
dotnet tool install --global VeloxDev.Cli
veloxdev --help
```

**预期结果：** `veloxdev --help` 打印 `run` 与 `mcp` 的用法并以 0 退出。

也可以直接从工作树构建：

```powershell
dotnet build Src/Cli/VeloxDev.Cli
dotnet build -c Release -p:VeloxDevLocalCore=true Src/Cli/VeloxDev.Cli
```

**预期结果：** 构建产出 `veloxdev.dll`；`veloxdev` shim 是受支持的入口。

## 产出存档

建一个小控制台工程，引用 `VeloxDev.Core`，建树并序列化。类型参数刻意写成具体类型：经基类或接口引用序列化会写出根 `$type`，而 `tree.Serialize()` 不会。

```powershell
dotnet new console -n ArchiveBuilder
cd ArchiveBuilder
dotnet add package VeloxDev.Core --version 12.3.0
```

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

**预期结果：** 输出 `wrote graph.json with 1 node(s)`，并且 `graph.json` 存在。

## 类型在别处时加清单

依赖声明在同名的旁路文件 `<archive>.manifest.json` 里：

```json
{
  "assemblies": [ "lib/MyNodes.dll", "lib/MyNodes.Helpers.dll" ],
  "rootType": "MyCompany.ViewModels.MyTreeViewModel",
  "allowExecution": false
}
```

- 文档是经派生树的自身类型序列化时，需要 `rootType`；否则 CLI 会把图读成 `TreeDefaultViewModel`。
- 程序集路径相对清单解析，且不得逃出清单所在目录。
- `allowExecution` 是显式同意；没有它（或 `--allow-execution`）时，执行工具根本不在 MCP 工具面上。
- `--assembly <path>` 无需修改清单就能追加依赖。

**预期结果：** 文档点名了未装载程序集里的类型时，进程会在反序列化之前失败，并给出类型名与补救方式（`--assembly` 或清单条目）。

## 检查存档

```powershell
veloxdev run --archive graph.json --start 0 --timeout-ms 30000
```

**预期结果：** 一个包含 `status`、`outcome`、`attempts`、`failures`、日志与 `data` 的 JSON 对象；`status` 为 `ok` 时进程以 0 退出。
