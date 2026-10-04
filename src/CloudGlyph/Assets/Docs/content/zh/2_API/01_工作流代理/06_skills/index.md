# 工作流代理 —— 命名空间：`VeloxDev.AI.Skills`

技能子系统：一个模型可发现、加载、关闭并读取其资源的 Agent Skills 库。宿主用 `WorkflowAgentScope.WithSkills(...)` 挂载它；`SkillAgentContextProvider` 每轮贡献四个技能工具与技能语料，`SkillScope` 是管理表面。所有类型位于 `VeloxDev.AI.Skills`（实现在 `Src/Core/VeloxDev.Core.Extension/Agent/Skills/`）。

**证据：** **Test**（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Skills/*` —— `SkillScopeTests`、`SkillAgentToolkitTests`、`SkillAgentContextProviderTests`）+ **Demo**（`AgentHelper.ProvideAgent` —— `.WithSkills("skills")`）。

## SkillScope

`public class SkillScope`。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Status` | `SkillsViewModel { get; }` | 可绑定的逐技能状态 + 聚合。 |
| `Version` | `long { get; }` | 渲染缓存键；每次真实变化（含语言）时前进。 |
| `PromptLanguage` | `AgentLanguages { get; private set; }` | 默认 `English`。 |
| `Names` | `IReadOnlyList<string> { get; }` | 已发现的技能名。 |
| `WithPromptLanguage` | `SkillScope WithPromptLanguage(AgentLanguages)` | 设置渲染/读取语言；推进 `Version`。 |
| `WithSkillRoot` | `SkillScope WithSkillRoot(string path)` | 添加磁盘根（委托 `WithSource(new FileSkillSource(...))`）。 |
| `WithSource` | `SkillScope WithSource(ISkillSource source)` | 添加来源（按注册顺序；先声明某名的来源拥有它）。 |
| `WithSynchronizationContext` | `SkillScope WithSynchronizationContext(SynchronizationContext?)` | UI 编组目标。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | 提供器。 |
| `Refresh` | `void Refresh()` | 重新发现；保留启用标志。 |
| `SetEnabled` / `Enable` / `Disable` | `bool …(string name, …)` | 开关技能；`SetEnabled` 返回是否移动。 |
| `Find` | `SkillStatusViewModel? Find(string name)` | 某技能的行。 |
| `BuildEmbeddedBlock` / `BuildWithdrawnBlock` / `BuildAdvertisement` | `string …(AgentLanguages language)` | 提示片段（已启用正文 / 已撤回名字 / 文件技能广告）。 |
| `ReadSkillBody` / `ReadSkillResource` | `string? …(string name, …)` | 读取正文 / 某个捆绑资源。 |

## 工具包与提供器

`public sealed class SkillAgentToolkit(SkillScope scope)`：

| 成员 | 签名 | 说明 |
|---|---|---|
| `Language` | `AgentLanguages { get; set; }` | 默认 `English`；取自作用域的提示语言。 |
| `ToolNames` | `public static readonly string[]` | `["ListSkills", "load_skill", "UnloadSkill", "read_skill_resource"]`。 |
| `CreateTools` | `IList<AITool> CreateTools()` / `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 四个工具，给出管线时被包装。 |

`public sealed class SkillAgentContextProvider : AIContextProvider` —— 构造函数 `(SkillScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)`。每轮贡献（被包装的）四个工具与语料/撤回/广告文本；以其缓存的渲染按 `SkillScope.Version` 键控；`StateKeys` 按作用域。无任何启用项时它不贡献指令，但仍贡献工具。

## 描述符 / 状态模型

| 类型 | 种类 | 成员 |
|---|---|---|
| `ISkillSource` | interface | `SkillSourceKind Kind { get; }`、`IReadOnlyList<SkillDescriptor> Discover()`、`string? ReadBody(string skillName, AgentLanguages language)`、`string? ReadResource(string skillName, string relativePath, AgentLanguages language)` |
| `SkillDescriptor` | sealed class | `Name`、`Description`、`Source`、`Path`、`Language`、`ResourceCount`、`Error` |
| `EmbeddedSkillSource` | sealed class | `EmbeddedSkillSource(string system)` —— 读取程序集内嵌技能 |
| `FileSkillSource` | sealed class | `FileSkillSource(string rootPath)` —— 读取 `SKILL.md` 文件夹；暴露 `Root` |
| `SkillState` | enum | `NotStarted = 0`、`Loading = 1`、`Ready = 2`、`Error = 3` |
| `SkillSourceKind` | enum | `Embedded = 0`、`File = 1` |
| `SkillStatusViewModel` | partial class | `Name`、`Description`、`State`、`Source`、`Path`、`IsEnabled`、`ResourceCount`、`Error`、`IsReady`、`IsError`、`IsActive`、`HasResources`、`StateText` |
| `SkillSummary` | sealed class | `Name`、`Description`、`Source`、`IsActive` |
| `SkillsViewModel` | partial class | `Skills`、`Snapshot`、`ActiveCount`、`ErrorCount`、`HasError`、`Track(...)`、`Reset()` |

## 工具

| 工具 | 用途 |
|---|---|
| `ListSkills` | 每个已发现技能：来源、状态、启用标志、资源数、错误 + 聚合。纯查询。 |
| `load_skill` | 读取技能完整文本并打开它。读取**文件**技能正文的唯一方式。 |
| `UnloadSkill` | 关闭某技能（不重新发现）。 |
| `read_skill_resource` | 读取捆绑资源；遍历路径被拒绝；内嵌技能没有资源。 |

四个工具相对 workflow 图都是只读的。`SkillFrontmatter`（internal）执行 `name`（≤ 64）/ `description`（≤ 1024）限制并从正文剥离 frontmatter。
