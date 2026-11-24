# 智能体上下文与技能

上下文从编译好的类型树渲染，技能从嵌入资源或磁盘发现。两条路径都把成品文本按版本键缓存，但发现过程本身是同步的、分配密集的，而且每次运行都会重读每份文档。唯一的二次项出现在状态行上，不在文档上。下列界均从所引用的控制流读出；若类型树辅助函数的内部不在所引模块内，该界标记为推断。

## 代价模型

| 符号 | 含义 |
|---|---|
| $s$ | 单个作用域中的技能数 |
| $d$ | 技能根目录下的条目数 |
| $r$ | 单个技能附带的资源数 |
| $R$ | 程序集中的清单资源数 |
| $L$ | 提示语言数（$\le 2$） |
| $n$ | 编译上下文树中的节点数 |
| chars | 文档文本总量 |

## 发现

`FileSkillSource.Discover` 只走两层 —— 根目录的 `SKILL.md` 与下一级目录的 `SKILL.md`（`Src/Core/VeloxDev.Core.Extension/Agent/Skills/FileSkillSource.cs:182-192`）。因为不读全文就无法解析 frontmatter，每个文件都被完整读取；随后递归枚举该技能的资源树，但不打开资源（`FileSkillSource.cs:194-208`）。

```csharp
private static IReadOnlyList<string> EnumerateResources(string skillDirectory)
{
    try
    {
        return
        [
            .. Directory.EnumerateFiles(skillDirectory, "*", SearchOption.AllDirectories)
                .Where(f => !string.Equals(Path.GetFileName(f), SkillFileName, StringComparison.OrdinalIgnoreCase)
                            && ResourceExtensions.Contains(Path.GetExtension(f)))
                .Select(f => f.Substring(skillDirectory.Length)
                    .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                    .Replace(Path.DirectorySeparatorChar, '/'))
                .OrderBy(f => f, StringComparer.OrdinalIgnoreCase)
        ];
    }
```

发现代价为

$$
T_{\text{discover}} = O(d + s \cdot \text{chars} + \sum r)
$$

两次刷新之间除了结果描述符之外没有任何缓存。嵌入发现类似，但每个语言要多付一次清单数组：$O(L \cdot R + s \cdot \text{chars})$。

## 刷新在状态行上是二次的

`SkillScope.Refresh` 先快照来源，逐个发现，按名称分组，再为每个概念跟踪一行状态（`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillScope.cs:429-455`）。`Track` 会调用 `NotifyAggregates`，后者把整个绑定集合重新投影成一份新快照（`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillStatusViewModel.cs:131-137`、`:159-169`）。

```csharp
var previous = Status.Skills.ToDictionary(s => s.Name, s => s.IsEnabled, StringComparer.OrdinalIgnoreCase);

Status.Reset();
foreach (var name in order)
{
    var group = byName[name];
    var primary = group.FirstOrDefault(d => d.Error is null) ?? group[0];
    var errors = group.Where(d => d.Error is not null).Select(d => d.Error!).ToArray();

    Status.Track(new SkillStatusViewModel
    {
        Name = name,
        Description = primary.Description,
        Source = primary.Source,
        Path = primary.Path,
        ResourceCount = group.Max(d => d.ResourceCount),
        // ...
        IsEnabled = !previous.TryGetValue(name, out var wasEnabled) || wasEnabled,
    });
}
```

因此对 $s$ 个技能的一次刷新代价是

$$
T_{\text{refresh}} = O(s^2 + s \cdot \text{chars} + \sum r)
$$

$s$ 较小时文档读取占主导；目录变大后状态行重建占主导。

```plot
{
  "title": "技能刷新：状态行与文档",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "线性发现" },
    { "fn": "x^2", "color": "#f472b6", "title": "状态行重建" }
  ]
}
```

## 查找与开关

`SetEnabled` 先切到 UI 上下文，再调用 `Find`，即对 `ObservableCollection` 的 `Status.Skills.FirstOrDefault`（`SkillScope.cs:207-224`、`:338-339`）。因此每次开关、每次技能工具调用都是 $O(s)$。通过工具启用 $n$ 个技能是 $O(n \cdot s)$；这里没有索引，不同于 MCP 作用域的 `HashSet` 键。

## 上下文树与提示词组装

`AgentContextTreeRenderer.TryEntry` 解析类型路径，然后列出父目录并扫描其子项（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/AgentContextTreeRenderer.cs:254-263`；`Src/Core/VeloxDev.Core/AI/AIContextTreeRegistry.cs:142-155`）。`MembersAcross` 沿记录的基类链逐层走目录。渲染一个类型的代价是

$$
T_{\text{type}} = O(\text{基类深度} \cdot \text{每目录子项数} + \text{chars})
$$

完整骨架 `ProvideAllContexts` 会读取所有嵌入参考，并渲染所有框架类型与已注册的客户类型。源码注释记录骨架每次渲染约 870 KB，并明确禁止按轮运行（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2006-2012`）。`ProvideProgressiveContextPrompt` 保留同样的头部与安全文本，但只输出一行类型摘要，而不是完整属性表（`WorkflowAgentScope.cs:1413-1419`）。

## 每轮缓存

`SkillAgentContextProvider` 按 `(Version, PromptLanguage)` 缓存指令与工具，键不变就返回同一批实例（`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillAgentContextProvider.cs:78-104`）。`WorkflowAgentContextProvider` 按作用域打包的 `ContextKey` 缓存整次渲染，并在只有用量档位变化时复用工具数组（`Agent/Workflow/WorkflowAgentContextProvider.cs:112-132`）。

命中的代价是 $O(1)$ 且零分配。未命中时指令为 $O(\text{chars})$，选中的技能按类别排序为 $O(s \log s)$。

## 技能工具

`SkillAgentToolkit` 暴露四个工具（`Src/Core/VeloxDev.Core.Extension/Agent/Skills/SkillAgentToolkit.cs:48-49`）。`ListSkills` 排序全部技能并序列化所有资源名，$O(s \log s + \text{chars})$。`LoadSkill` 与 `UnloadSkill` 各付一次 $O(s)$ 的 `Find`，前者随后读取正文，$O(\text{chars})$。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 提示词所描述的工具集。
- [MCP集成](../20_MCP集成/index.md) —— 另一个每轮工具来源，使用同样的版本缓存契约。
