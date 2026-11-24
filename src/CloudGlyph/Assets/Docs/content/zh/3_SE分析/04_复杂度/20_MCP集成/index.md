# MCP集成

MCP 的代价主要来自 I/O 与列表维护，而不是图规模。服务器握手是串行的；工具列表每次访问都重新展平并重新过滤；两个服务器注册表在逐行更新时重建状态快照。工具面本身只是扁平拼接，没有跨服务器限定。下列界均从所引用的控制流读出；若某条组合路径依赖所引文件之外的辅助函数，该界标记为推断。

## 代价模型

| 符号 | 含义 |
|---|---|
| $m$ | 已配置或已加载的服务器数 |
| $k_i$ | 服务器 $i$ 提供的工具数 |
| $r$ | 单个服务器的资源数 |
| $p$ | 单个服务器的提示词数 |
| args | 提示词/资源参数 |
| chars | 配置或负载文本量 |

## 配置解析

`McpConfigurationFile.Load` 读取并解析整份文档，随后每个条目经 `ParseServer` 把 `url` 映射为 HTTP、把 `command` 映射为 stdio 启动，并用一条编译正则展开环境变量引用（美元花括号名，可带 `:-default` 回退）（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpConfigurationFile.cs:44-201`）。

```csharp
if (!root.TryGetProperty(ServersProperty, out var servers) || servers.ValueKind != JsonValueKind.Object)
    throw new InvalidDataException($"The document has no object-valued '{ServersProperty}' property.");

var result = new List<McpServerConfiguration>();
foreach (var entry in servers.EnumerateObject())
{
    var config = ParseServer(entry.Name, entry.Value);
    if (config is not null) result.Add(config);
}

return result;
```

解析代价是 $O(\text{chars} + m + \sum \text{args} + \sum \text{env})$。没有任何缓存：重复调用 `WithServersFromFile` 会重读并重新解析文件。

## 注册是二次的

`WithServers` 对每个配置调用 `Remember`，而 `Remember` 在添加前执行 `_registered.RemoveAll(...)` —— 每个服务器一次全表扫描（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs:341-360`、`:383-391`）。

$$
T_{\text{register}} = O(m^2)
$$

同样的形状出现在 `ListServers`：每一行状态都要在锁内复制已注册列表并线性查找自己的配置（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpAgentToolkit.cs:760`、`:415-419`；`McpScope.cs:328-335`）。

```plot
{
  "title": "服务器注册",
  "grid": true,
  "xAxis": { "domain": [1, 60] },
  "yAxis": { "domain": [0, 4000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "线性" },
    { "fn": "x^2", "color": "#f472b6", "title": "逐服务器 Remember" }
  ]
}
```

## 服务器加载

`LoadAsync` 是替换语义：先重置状态、分离并释放全部现有宿主，然后用 `foreach` + `await` 逐个加载（`McpScope.cs:778-806`、`:897-955`）。每次 `LoadOneAsync` 还会调用 `TrackServerAsync`，后者扫描状态行。

$$
T_{\text{load}} = O\left(m^2 + \sum_i (\text{handshake}_i + k_i)\right)
$$

实际耗时会按服务器累加，因为循环从不并行发起两次握手。`AddAsync` 只加载一个服务器，不影响其余。失败的服务器会被记录，但不会中断整批。只有 HTTP 连接受连接超时限制（联动取消令牌）；这条路径上的 stdio 安装与启动没有等价上限。

## 工具展平

`LoadedTools` 与 `LoadedToolsByServer` 每次访问都从每个服务器的集合重建列表，并过滤禁用服务器与禁用的 `server/tool` 键（`McpScope.cs:152-188`）。

```csharp
public IReadOnlyList<AITool> LoadedTools
{
    get
    {
        lock (_loadedToolsLock)
            return
            [
                .. _loadedToolSets
                    .Where(kv => !_disabledServers.Contains(kv.Key))
                    .SelectMany(kv => kv.Value.Where(t => !_disabledServerTools.Contains(ToolKey(kv.Key, t.Name))))
            ];
    }
}
```

`ToolKey` 在每次判断时拼接 `server + "/" + tool`（`McpScope.cs:196`），所以一次访问的代价是

$$
T_{\text{flatten}} = O\left(\sum k_i\right)
$$

时间、同等数量的临时字符串，以及一个新列表。上下文提供方每次渲染调用一次 `LoadedToolsByServer`，因此版本变化会重付整次展平，并为每个工具新建一个 `TrackedAIFunction` 包装。

启停是廉价路径：锁内一次哈希集合增删，然后一次 $O(m)$ 的状态行扫描以同步镜像（`McpScope.cs:217-243`）。

## 宿主服务器协调

`HostedMcpServer` 持有一个客户端和每服务器一把闸。`Adopt` 用 `ToDictionary(t => t.Name, ...)` 构造 `_live`，因此同一服务器内的重名工具会在连接时抛异常（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/HostedMcpServer.cs:343-349`）。`Reconcile` 按名称复用已有的 `McpToolProxy` 实例，并克隆每个工具的 JSON 模式（`HostedMcpServer.cs:355-371`）。

$$
T_{\text{reconcile}} = O\left(k + \sum \text{模式大小}\right)
$$

重建是惰性的：`RebuildOwed` 比较已构建与已尝试的修订号，所以失败配置不会在每次调用时重试（`HostedMcpServer.cs:293-297`）。

## 授权视图与状态行

`CreateGrantedView` 只复制被授权服务器已提供的工具，并逐个调用 `IsToolEnabled` 过滤 —— 这会重入锁并为每个工具分配一个键（`McpScope.cs:518-534`、`:291-296`）。随后跟踪这些行是二次的，因为 `McpStatusViewModel.Track` 会调用 `NotifyAggregates`，后者重新投影所有行（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpStatusViewModel.cs:165-171`、`:202-217`）。

## 跨服务器命名

`McpToolProxy.Name` 原样返回服务器自己的工具名，提供方则把所有服务器的列表直接拼接（`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpToolProxy.cs:24-27`；`McpAgentContextProvider.cs:107-125`）。因此两个服务器暴露同名工具时，会产生两个同名工具；`mcp:{server}` 来源字符串只存在于包装器上，不在工具名里。代码没有限定名处理，冲突只能由调用方自行分辨。

## 提供方缓存

`McpAgentContextProvider` 只按作用域 `Version` 缓存指令与工具（`McpAgentContextProvider.cs:78-100`）。未命中时构造新工具集、至多十个管理工具，然后追加并包装每个已加载服务器工具。命中时除提供方自身的锁外无额外加锁，直接返回同一个 `AIContext`。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— MCP 工具同样要经过的每次调用闸门与账本。
- [智能体上下文与技能](../19_智能体上下文与技能/index.md) —— 另一个每轮贡献者，使用同样的缓存契约。
