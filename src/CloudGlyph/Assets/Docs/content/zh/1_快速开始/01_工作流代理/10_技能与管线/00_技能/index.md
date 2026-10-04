# 10.0 · 技能

**技能**是一段指引（外加可选的捆绑资源文件），模型可按需拉入。本库把自己的提示文档作为内嵌技能随附；应用则以磁盘文件夹的形式添加自己的技能。

```csharp
scope.WithSkills("skills");        // 一个磁盘根，相对 AppContext.BaseDirectory 解析
//        ^ 允许暂时不存在 —— 内嵌语料仍会到达
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

`WithSkills(string rootPath)` 与 `WithSkills(SkillScope skills)` 都会挂载该子系统。在 `ProvideProgressiveContextPrompt()` **之前**挂载是让语料交给子系统动态掌控的顺序 —— 骨架随后不含其副本。之后挂载也可行；届时子系统只报告自骨架渲染以来被关闭的技能。

**预期结果：** `WithSkills("skills")` 后向模型提供 `ListSkills`、`load_skill`、`UnloadSkill`、`read_skill_resource`，且内嵌语料（「Skill: …」块）到达提示。

## 1. `SkillScope` —— 子系统

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSkillRoot` | `WithSkillRoot(string path)` | 添加一个磁盘根（相对路径按 `AppContext.BaseDirectory` 解析）。 |
| `WithSource` | `WithSource(ISkillSource source)` | 添加来源；按注册顺序，先声明某名的来源拥有它。 |
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | 技能渲染与读取所用的语言。 |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 编组目标。 |
| `CreateContextProvider` | `CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | 提供器。 |
| `Status` | `SkillsViewModel { get; }` | 可绑定的逐技能状态 + 聚合。 |
| `Version` | `long { get; }` | 渲染缓存键；每次真实变化时前进。 |
| `Names` | `IReadOnlyList<string> { get; }` | 已发现的技能名。 |
| `Refresh` / `SetEnabled` / `Enable` / `Disable` | | 重新发现，或开关某技能（`SetEnabled` 返回是否移动）。 |
| `Find` | `SkillStatusViewModel? Find(string name)` | 某技能的行。 |
| `ReadSkillBody` / `ReadSkillResource` | `string? …(string name, …)` | 读取正文 / 某个捆绑资源。 |

## 2. 四个工具

| 工具 | 必需参数 | 用途 |
|---|---|---|
| `ListSkills` | — | 每个已发现技能：来源（`Embedded`/`File`）、状态、启用标志、资源数、错误，外加聚合。纯查询。 |
| `load_skill` | 技能名 | 读取技能完整文本并把它打开。对**文件**技能这是读取其正文的唯一方式；对**内嵌**技能文本已在指令中，但仍会返回。 |
| `UnloadSkill` | 技能名 | 关闭某技能 —— 它不再贡献指令，但不卸载也不重新发现任何东西。 |
| `read_skill_resource` | 技能名 + 相对路径 | 读取捆绑资源（参考文档、模式或数据文件）。仅对文件技能有意义；内嵌技能不带任何资源。 |

四个工具相对 workflow 图都是只读的（已折入工具包的只读集合，因此永不标脏）。来源：`SkillAgentToolkitTests.CreateTools_RegistersTheFourSkillTools`、`SkillAgentContextProviderTests.BuildContext_ContributesTheFourSkillToolsWrapped`。

对未知名字的 `load_skill` 是**可操作的错误**，其消息点名 `ListSkills`；对内嵌技能的 `read_skill_resource` 说 `no resources`；遍历路径（`"../secret.md"`）被拒绝。来源：`SkillAgentToolkitTests`。

## 3. 内嵌 vs 文件技能

| | 内嵌（`SkillSourceKind.Embedded`） | 文件（`SkillSourceKind.File`） |
|---|---|---|
| 来源 | `Resources/{System}/{lang}/Skills/` 下的程序集资源 | 含 `SKILL.md` + 资源的文件夹 |
| 提示 | 启用时**完整**注入 | **仅广告**（名 + 描述）—— 用 `load_skill` |
| 资源 | 无 | 随技能捆绑；计入 `ResourceCount` |
| 语言 | 按语言，英语回退 | 文件夹的 frontmatter |

`FileSkillSource` 读取 frontmatter（`name`、`description`），从正文中剥离它，并把问题如实报告而非吞掉：文件夹名/`name` 不符、缺 frontmatter（名字回退到文件夹名）、或非 kebab-case 名都会以非空 `Error` 暴露。逃出技能目录的资源路径（`.`/`..`/绝对路径）返回 `null`。来源：`SkillScopeTests.FileSource_*`。

`EmbeddedSkillSource("Workflow")` 发现本库随附的技能（7 个名字 × 2 种语言 = 14 个描述符）；名字由文件名派生为 kebab-case。来源：`SkillScopeTests.EmbeddedSource_DiscoversEveryShippedSkillInBothLanguages`。

## 4. 描述符与状态模型

`ISkillSource` 是接缝：`Discover()` → `IReadOnlyList<SkillDescriptor>`；`ReadBody`；`ReadResource`。`SkillDescriptor` 携带 `Name`、`Description`、`Source`、`Path`、`Language`、`ResourceCount`、`Error`。`SkillState` 为 `NotStarted`、`Loading`、`Ready`、`Error`。

`SkillStatusViewModel`（可绑定）与 `SkillSummary`（不可变）携带同样的事实；`SkillsViewModel` 聚合暴露 `ActiveCount`、`ErrorCount`、`HasError` 与 `Snapshot`。

**预期结果：** 解析失败的技能显示 `State == Error`、非空 `Error` 与 `IsActive == false`。

## 运行声明

- ✅ 实际构建并运行 —— 确定性 agent 测试套件（2026-10-01，`已通过! 失败: 0，通过: 387`）包含 `Skills/**`（`SkillScopeTests`、`SkillAgentToolkitTests`、`SkillAgentContextProviderTests`），覆盖双语发现、启用/撤回块、四个工具、资源遍历拒绝与渲染缓存。
