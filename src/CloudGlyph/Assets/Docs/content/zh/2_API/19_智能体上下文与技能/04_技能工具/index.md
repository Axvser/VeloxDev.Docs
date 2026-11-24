# 技能工具

技能子系统通过上下文 provider 贡献的四个工具到达模型。嵌入资源读取器是包侧访问器，供嵌入来源与提示骨架共用。

## 类：SkillAgentToolkit

`VeloxDev.AI.Skills.SkillAgentToolkit` 是 `SkillScope` 面向智能体的视图。其形状对应 `McpAgentToolkit`：宿主与智能体操作同一数据层。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `SkillAgentToolkit(SkillScope scope)` | 把工具绑定到技能集。 |
| `Language` | `AgentLanguages Language { get; set; }` | 技能文本读取所用提示语言。默认英语。 |
| `ToolNames` | `static readonly string[] ToolNames` | `["ListSkills", "load_skill", "UnloadSkill", "read_skill_resource"]`。 |
| `CreateTools()` | `IList<AITool> CreateTools()` | 四个工具，未包装：无编组、无记账。 |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 四个工具，已包装，每次调用被编组、闸控并上报。这是 provider 贡献的版本。 |

名称 `load_skill` 与 `read_skill_resource` 遵循 Agent Skills 约定，因此已熟悉该约定的模型无需额外说明。四个工具对工作流图都是只读的，因此工作流宿主把它们排除在变更预算与脏标记之外。

### 工具

| 工具 | 用途 |
|---|---|
| `ListSkills` | 列出已发现技能及其开关状态。 |
| `load_skill` | 加载一个技能的正文。 |
| `UnloadSkill` | 卸载此前加载的技能。 |
| `read_skill_resource` | 读取技能的一个随附资源。 |

不要再 `WithTools` 注册一遍：框架会做并集且不按名去重。

## 类：SkillAgentContextProvider

`VeloxDev.AI.Skills.SkillAgentContextProvider : AIContextProvider` 把技能作用域的当前状态贡献给智能体调用：已启用技能文本与四个工具。把它挂到任意智能体，模型就获得技能，无需工作流层。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `SkillAgentContextProvider(SkillScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | 为作用域创建 provider。独立使用可省略 `tools`；提示已带嵌入语料时传 `embeddedCorpusDelivered: true`。 |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | provider 的状态键。 |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | 渲染技能贡献。 |

渲染基于作用域 `Version` 与提示语言缓存。`embeddedCorpusDelivered` 为 `true` 时，provider 贡献语料的差量（`BuildWithdrawnBlock`）而非语料本身，避免每篇技能文档两次到达模型。

## 类：AgentEmbeddedResources

`VeloxDev.AI.AgentEmbeddedResources` 读取 `VeloxDev.Core.Extension` 中 `Resources/{System}/{LangCode}/` 下嵌入的 Markdown。`EmbeddedSkillSource` 与提示骨架使用它。

| 方法 | 返回 | 说明 |
|---|---|---|
| `ToLanguageCode(AgentLanguages language)` | `string` | 文件夹代码：`"zh"` 或 `"en"`。其他语言解析为 `"en"`。 |
| `ReadSkill(string system, string name, AgentLanguages language = AgentLanguages.English)` | `string?` | 读取 `Skills/{name}.md`，回退英语；都不存在时为 `null`。 |
| `ListSkills(string system, AgentLanguages language = AgentLanguages.English)` | `IEnumerable<string>` | 某系统某语言所有技能文件的基名。 |
| `ListSkillsExact(string system, AgentLanguages language)` | `IEnumerable<string>` | 恰好存在于该语言的基名，无英语回退。 |
| `ReadAllSkills(string system, AgentLanguages language = AgentLanguages.English)` | `string` | 拼接所有技能文件，以空行分隔。 |
| `ReadAllReferences(string system, AgentLanguages language = AgentLanguages.English)` | `string` | 拼接所有参考文件，以空行分隔。 |
| `ReadSafety(string system, string name, AgentLanguages language = AgentLanguages.English)` | `string?` | 读取 `Safety/{name}.md`，回退英语。 |

在 `Resources/{System}/{LangCode}/` 下添加文件即可：项目 glob 会嵌入它。

## 示例

```csharp
using VeloxDev.AI.Skills;

var toolkit = scope.CreateSkillToolkit();
foreach (var tool in toolkit.CreateTools())
    Console.WriteLine(tool.Name);
```

## 相关

- [技能作用域](../01_技能作用域/index.md) —— 工具操作的对象。
- [上下文作用域](../00_上下文作用域/index.md) —— 可能已携带语料的骨架。
