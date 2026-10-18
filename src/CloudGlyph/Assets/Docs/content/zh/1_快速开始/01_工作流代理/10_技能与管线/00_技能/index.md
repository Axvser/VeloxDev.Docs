# 10.0 · 技能

**技能**是一段指引（外加可选的捆绑资源文件），模型可按需拉取。库自带若干提示文档作为内嵌技能；应用则可以把自己的一批以磁盘文件夹加入。

```csharp
scope.WithSkills("skills");        // 磁盘根，相对 AppContext.BaseDirectory 解析
//        ^ 允许尚不存在 —— 内嵌语料仍会到达
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

`WithSkills(string rootPath)` 与 `WithSkills(SkillScope skills)` 都会挂载该子系统。在 `ProvideProgressiveContextPrompt()` **之前**挂载，是让语料受子系统动态控制的顺序 —— 骨架随后不再带它的副本。之后挂载仍然可用；但子系统此时只会报告哪些技能自那以后被关闭。

**预期结果：** `WithSkills("skills")` 后模型拿到 `ListSkills`、`load_skill`、`UnloadSkill`、`read_skill_resource`，且内嵌语料（“Skill: …”块）到达提示。

## 1. `SkillScope` —— 子系统

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSkillRoot` | `WithSkillRoot(string path)` | 增加磁盘根（相对路径按 `AppContext.BaseDirectory` 解析）。 |
| `WithSource` | `WithSource(ISkillSource source)` | 增加来源；按注册顺序，先声明某名字者拥有它。 |
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | 技能渲染与读取所用的语言。 |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 编组目标。 |
| `CreateContextProvider` | `CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | 提供器。 |
| `Status` | `SkillsViewModel { get; }` | 可绑定的逐技能状态 + 聚合。 |
| `Version` | `long { get; }` | 渲染缓存键；每次真实变化前进。 |
| `Names` | `IReadOnlyList<string> { get; }` | 已发现的技能名。 |
| `Refresh` / `SetEnabled` / `Enable` / `Disable` | | 重新发现，或开关技能（`SetEnabled` 返回是否移动）。 |
| `Find` | `SkillStatusViewModel? Find(string name)` | 单个技能的行。 |
| `ReadSkillBody` / `ReadSkillResource` | `string? …(string name, …)` | 读取正文 / 捆绑资源。 |

## 2. 四个工具

| 工具 | 必需参数 | 用途 |
|---|---|---|
| `ListSkills` | — | 每个已发现技能：来源（`Embedded`/`File`）、状态、启用标志、资源数、错误，外加聚合。纯查询。 |
| `load_skill` | 技能名 | 读取技能全文并打开它。对**文件**技能，这是读取其正文的唯一方式；对**内嵌**技能，文本已在指令中，但仍会返回。 |
| `UnloadSkill` | 技能名 | 关闭技能 —— 它不再向指令贡献内容，且无需重新发现。 |
| `read_skill_resource` | 技能名 + 相对路径 | 读取捆绑资源（参考文档、schema 或数据文件）。只对文件技能有意义；内嵌技能没有。 |

四个工具相对 workflow 图都是只读的（并入工具包的只读集合，因此绝不标脏）。来源：`SkillAgentToolkitTests.CreateTools_RegistersTheFourSkillTools`、`SkillAgentContextProviderTests.BuildContext_ContributesTheFourSkillToolsWrapped`。

未知名字的 `load_skill` 失败是可操作的错误，消息会点名 `ListSkills`；对内嵌技能调用 `read_skill_resource` 会说明 `no resources`；路径穿越（`"../secret.md"`）会被拒绝。来源：`SkillAgentToolkitTests`。

## 3. 内嵌 vs 文件技能

| | 内嵌（`SkillSourceKind.Embedded`） | 文件（`SkillSourceKind.File`） |
|---|---|---|
| 来源 | 程序集资源 `Resources/{System}/{lang}/Skills/` | 带 `SKILL.md` 与资源的文件夹 |
| 提示 | 启用时**整份**注入 | **只宣传**（名字 + 描述）—— 用 `load_skill` 读取 |
| 资源 | 无 | 随技能附带；计入 `ResourceCount` |
| 语言 | 按语言，缺失回退英文 | 文件夹的 frontmatter |

`FileSkillSource` 读取 frontmatter（`name`、`description`），从正文中剥离，并报告问题而不是吞掉：文件夹名/`name` 不匹配、缺 frontmatter（名字回退为文件夹名）、或名字不是 kebab-case，都会以非空 `Error` 呈现。`.`/`..`/绝对路径逃出技能目录时返回 `null`。来源：`SkillScopeTests.FileSource_*`。

`EmbeddedSkillSource("Workflow")` 发现库自带的技能（7 个名字 × 2 种语言 = 14 个描述符）；名字由文件名派生为 kebab-case。来源：`SkillScopeTests.EmbeddedSource_DiscoversEveryShippedSkillInBothLanguages`。

## 4. 描述符与状态模型

`ISkillSource` 是接缝：`Discover()` → `IReadOnlyList<SkillDescriptor>`；`ReadBody`；`ReadResource`。`SkillDescriptor` 携带 `Name`、`Description`、`Source`、`Path`、`Language`、`ResourceCount`、`Error`。`SkillState` 为 `NotStarted`、`Loading`、`Ready`、`Error`。

`SkillStatusViewModel`（可绑定）与 `SkillSummary`（不可变）携带相同事实；`SkillsViewModel` 聚合暴露 `ActiveCount`、`ErrorCount`、`HasError` 与一个 `Snapshot`。

**预期结果：** 解析失败的技能显示 `State == Error`、非空 `Error` 与 `IsActive == false`。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。`Skills/**` 测试存在且在 2026-10-01 的一次记录运行（387 项）中通过，但该运行早于权限模式重构，不作为当前证据。
