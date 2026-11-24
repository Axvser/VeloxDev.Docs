# 技能作用域

`VeloxDev.AI.Skills.SkillScope` 是技能数据层：它从一个或多个来源发现技能，把每个技能暴露为可绑定的开关，并渲染技能可采用的提示形状。用 `WithSkills` 把它挂到工作流作用域。

## WorkflowAgentScope 上的挂载成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSkills` | `WorkflowAgentScope WithSkills(string rootPath)` | 从磁盘根发现技能，并把库的嵌入提示文档移入同一可开关列表。 |
| `WithSkills` | `WorkflowAgentScope WithSkills(SkillScope skills)` | 挂载已建好的作用域，以共享数据层或提供自定义来源。 |
| `Skills` | `SkillScope? Skills { get; }` | 已挂载的作用域，或 `null`。后挂载的一方持有嵌入语料。 |
| `CreateSkillToolkit()` | `SkillAgentToolkit CreateSkillToolkit()` | 面向模型的技能工具，绑定此作用域的技能集与提示语言。 |

## 类：SkillScope

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Status` | `SkillsViewModel` | 可绑定的技能列表与聚合计数。 |
| `Version` | `long` | 已发现集合与开关状态的单调版本号。provider 基于它缓存渲染。 |
| `PromptLanguage` | `AgentLanguages` | 技能文本渲染与读取所用语言。 |
| `WithPromptLanguage` | `SkillScope WithPromptLanguage(AgentLanguages language)` | 设置提示语言；推进 `Version`。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | 创建贡献技能文本与工具的 provider。提示已带嵌入语料时传 `true`。 |
| `WithSynchronizationContext` | `SkillScope WithSynchronizationContext(SynchronizationContext? context)` | 把发现结果与开关变化编组到 UI 线程。 |
| `WithSkillRoot` | `SkillScope WithSkillRoot(string path)` | 添加磁盘根。相对路径相对应用基目录解析；目录可以尚不存在。 |
| `WithSource` | `SkillScope WithSource(ISkillSource source)` | 添加来源。来源按顺序查询；首个声明某个名称的来源拥有它。 |
| `Refresh` | `void Refresh()` | 重新发现所有来源并重建 `Status`。开关状态按名称保留。推进 `Version`。 |
| `SetEnabled` | `bool SetEnabled(string name, bool enabled)` | 开关一个技能；未发现该名称时为 `false`。 |
| `Enable` | `bool Enable(string name)` | 打开一个技能。 |
| `Disable` | `bool Disable(string name)` | 关闭一个技能。 |
| `BuildEmbeddedBlock` | `string BuildEmbeddedBlock(AgentLanguages language)` | 所有已启用的**嵌入**技能全文，按名称排序。 |
| `BuildWithdrawnBlock` | `string BuildWithdrawnBlock(AgentLanguages language)` | 对已携带语料的提示：列出此后被关闭的技能，并指示模型忽略它们。无漂移时为空。 |
| `BuildAdvertisement` | `string BuildAdvertisement()` | 每个已启用**文件**技能的名称与描述，外加「先加载正文再遵循」的指示。 |
| `ReadSkillBody` | `string? ReadSkillBody(string name, AgentLanguages language)` | 技能全文，无论是否启用。 |
| `ReadSkillResource` | `string? ReadSkillResource(string name, string relativePath, AgentLanguages language)` | 一个随附资源，相对于技能目录寻址。 |
| `Find` | `SkillStatusViewModel? Find(string name)` | 按名称查找已发现技能，或 `null`。在绑定线程调用。 |
| `Names` | `IReadOnlyList<string> Names` | 已发现名称，基于快照，可在绑定线程外读取。 |

### 两种注入形状

- **嵌入**技能是架构提示文本。启用时正文完整注入。全部启用时，`BuildEmbeddedBlock` 与技能可开关之前提示携带的内容逐字节一致。
- **文件**技能遵循 Agent Skills 约定。只有名称与描述进入提示；正文通过 `load_skill` 获取。这让大型外部技能库不会每轮都消耗 token。

关闭技能不会卸载它：`IsEnabled` 独立于 `State`，因此重新启用无需重新发现。`Disable` 推进 `Version`，基于它缓存的 provider 会重渲染。

`Refresh` 是宿主动作而非每轮动作：它总是推进 `Version`，若从提示 provider 每轮调用会破坏缓存。

## 枚举：SkillSourceKind

技能来源；决定其注入模式。

| 成员 | 值 | 含义 |
|---|---|---|
| `Embedded` | `0` | 随程序集发布；启用时完整注入。 |
| `File` | `1` | 从磁盘发现；通告并按需加载。 |

## 枚举：SkillState

已发现技能的生命周期。对应 `McpServerStatus`，但没有安装/连接的拆分。

| 成员 | 值 |
|---|---|
| `NotStarted` | `0` |
| `Loading` | `1` |
| `Ready` | `2` |
| `Error` | `3` |

## 示例

```csharp
using VeloxDev.AI.Skills;

var skills = new SkillScope()
    .WithSource(new EmbeddedSkillSource("Workflow"))
    .WithSkillRoot("skills");
skills.Refresh();

skills.Disable("smart-layout");
Console.WriteLine(skills.Status.Skills.Count(s => s.IsActive)); // 6
skills.Enable("smart-layout");
```

## 相关

- [技能状态](../02_技能状态/index.md) —— 此作用域持有的可绑定行。
- [技能来源](../03_技能来源/index.md) —— `WithSource` 接受什么。
- [技能工具](../04_技能工具/index.md) —— 面向模型的工具。
