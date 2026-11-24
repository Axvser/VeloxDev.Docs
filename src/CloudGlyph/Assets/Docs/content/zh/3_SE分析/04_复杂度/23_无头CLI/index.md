# 无头CLI

CLI 只有 `mcp` 与 `run` 两个动词，也不做目录发现：它接触的每个文件都是显式命名的。真正重要的代价是启动时的选项扫描、插件加载器的线性列表，以及每次隔离 worker 运行都要在新进程里重载整套插件。下列界均从所引用的控制流读出；若某个运行时或框架辅助函数在所引文件之外，该界标记为推断。

## 代价模型

| 符号 | 含义 |
|---|---|
| $a$ | argv 令牌数 |
| $p$ | 本进程累计加载的插件数 |
| $r$ | 单个插件的程序集引用数 |
| $f$ | 清单中的程序集条目数 |
| $t$ | 会话暴露的工具集工具数 |
| $j$ | 活动 worker 作业数 |
| $A$ | 审计环容量（500） |
| chars | 归档、结果或 CSV 文本量 |

## 选项解析

`CliOptions.Parse` 从下标 1 开始单向前进。`Split` 在第一个 `=` 处切开，内联值时局部 `Value()` 直接取用，否则消费下一个令牌（`Src/Cli/VeloxDev.Cli/CliOptions.cs:113-124`）。

```csharp
for (var i = 1; i < args.Length; i++)
{
    var raw = args[i];
    var (name, inline) = Split(raw);

    string Value()
    {
        if (inline is not null) return inline;
        if (i + 1 >= args.Length) throw new CliUsageException($"Option '{name}' requires a value.");
        return args[++i];
    }
```

解析代价是

$$
T_{\text{parse}} = O(a) + O(\text{值长度})
$$

程序集列表与标量字段占用 $O(a)$ 空间。动词在开头校验，并在 `Program` 中分发（`CliOptions.cs:102-104`；`Src/Cli/VeloxDev.Cli/Program.cs:22-26`）。

## 归档与清单

`WorkflowArchive.Load` 先规范化并读取图，再解析旁车清单并遍历其 `assemblies` 数组（`Src/Cli/VeloxDev.Cli/WorkflowArchive.cs:134-145`）。`ResolveInside` 对每个条目都重新计算一次 `GetFullPath(directory)`，再做前缀判断（`WorkflowArchive.cs:170-188`）。

$$
T_{\text{archive}} = O(\text{chars} + f \cdot L_{\text{path}})
$$

解析后的图文本会在整个会话期间保留。整个 CLI 不做目录枚举，所以没有隐藏的 $O(\text{files})$ 项。

## 插件加载

`PluginLoader.Load` 在一把锁内挂接解析事件（仅一次）、安装 `AssemblyDependencyResolver`、扫描 `AssemblyLoadContext.Default.Assemblies` 查找已加载程序集、把文件复制到暂存目录、加载、强制执行模块构造函数，并检查被引用程序集的版本（`Src/Cli/VeloxDev.Cli/PluginLoader.cs:129-210`）。

```csharp
foreach (var resolver in _resolvers)
{
    var path = resolver.ResolveAssemblyToPath(name);
    if (path is not null && File.Exists(path))
        return LoadResolved(context, path);
}

if (name.Name is { Length: > 0 } simpleName)
{
    foreach (var directory in _directories)
    {
        var candidate = System.IO.Path.Combine(directory, simpleName + ".dll");
        if (File.Exists(candidate))
            return LoadResolved(context, candidate);
```

这些查找全是列表线性扫描 —— 解析器、目录、已加载程序集、警告、版本不匹配。因此加载 $p$ 个插件的代价是

$$
T_{\text{plugins}} = O\left(p^2(1 + r)\right)
$$

未解析的依赖每次触发解析器都要付 $O(p)$ 次文件系统探测。程序集从不卸载，且注册表跨 `LoadArchive` 重载存活，所以 $p$ 会随进程寿命单调增长。

```plot
{
  "title": "插件加载：线性列表与集合",
  "grid": true,
  "xAxis": { "domain": [1, 60] },
  "yAxis": { "domain": [0, 4000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "基于集合" },
    { "fn": "x^2", "color": "#f472b6", "title": "每次加载线性扫描" }
  ]
}
```

## 会话创建

`WorkflowSession.Create` 逐个校验路径、加载归档、加载清单与显式程序集、解析根类型、反序列化整张图、构造智能体作用域、自动发现类型、安装重定向策略与存储，最后把工具集枚举成名称到函数的字典（`Src/Cli/VeloxDev.Cli/WorkflowSession.cs:149-257`、`:325-346`）。

$$
T_{\text{session}} = O\left(\text{chars} + n + l + t + \sum \text{插件加载}\right)
$$

`CreateMcpTools`、`DescribeCapabilities` 与 `IsBatchableTool` 都会再次调用 `BuildExposedFunctions`；批量应用对每个操作调用后者两次，所以 $k$ 个操作的代价是 $O(k \cdot t)$ 次工具构造（`WorkflowSession.cs:294-296`；`Src/Cli/VeloxDev.Cli/ArchiveTools.cs:124-128`）。

## 宿主、审计与重载

`WorkflowSessionHost.Acquire` 在锁内递增租约，`Release` 在计数归零时退役被替换的会话（`Src/Cli/VeloxDev.Cli/WorkflowSessionHost.cs:107-135`）。工具分发是一次字典查找，随后用 `Stopwatch` 计时并写入审计记录；审计列表超过 500 条后用 `RemoveRange` 裁剪，每条记录一次 $O(A)$ 移位（`:161-182`）。

$$
T_{\text{dispatch}} = O(\text{工具代价} + \text{args} + \text{result}) + O(A)
$$

`ReloadAsync` 用信号量串行化重载，先完整构造下一会话再切换（`:254-302`）。最多保留一个已退役会话。

## Worker 与作业

`WorkerJobRegistry` 用短 GUID 在字典中索引作业，启动与查找平均 $O(1)$；列表按启动时间排序为 $O(j \log j)$，清理扫描为 $O(j)$（`Src/Cli/VeloxDev.Cli/WorkerJobRegistry.cs:91-157`）。

```csharp
public WorkerJob? Find(string id)
{
    lock (_gate)
    {
        return _jobs.TryGetValue(id, out var job) ? job : null;
    }
}

public IReadOnlyList<WorkerJob> List()
{
    lock (_gate)
    {
        return [.. _jobs.Values.OrderBy(j => j.StartedAt)];
    }
}
```

`WorkerRunner` 把活树序列化到临时归档，带全部插件路径启动 `dotnet <cli> run`，并完整读取 stdout 与 stderr（`Src/Cli/VeloxDev.Cli/WorkerRunner.cs:41-191`）。子进程会重新走会话创建，所以每次隔离运行都要重付上面的插件代价。

$$
T_{\text{worker}} = O(n + l + \text{chars}) + T_{\text{plugins}}
$$

## CSV 与工作区

`RunLogCsv.TryWrite` 解析结果，用 `StringBuilder` 缓冲整份 CSV，一次写出，随后 `Attach` 再解析并重写结果以加入 `csvFile`（`Src/Cli/VeloxDev.Cli/RunLogCsv.cs:22-108`）。两个方向都是 $O(\text{chars})$，峰值内存 $O(\text{outChars})$ —— 文件从不流式写出。

`WorkspaceRule.Ensure` 规范化每个候选路径，并与“工作区 + 分隔符”做前缀判断（`Src/Cli/VeloxDev.Cli/WorkspaceRule.cs:28-41`）。单次检查是 $O(L_{\text{path}})$，但同一批路径会在启动时检查一次、`Create` 内再检查一次，之后每次加载/保存/程序集操作还要再检查 —— 常数工作被反复支付，从不记忆化。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— CLI 通过 MCP 暴露的工具集。
- [平台适配器契约](../24_平台适配器契约/index.md) —— CLI 在无 GUI 情况下运行的那套共享面。
