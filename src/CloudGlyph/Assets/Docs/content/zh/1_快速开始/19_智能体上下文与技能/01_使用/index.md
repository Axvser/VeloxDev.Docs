# 使用

## 渲染提示词分层

scope 按变化频率拆分提示词。这就是 `ProvideProgressiveContextPrompt()` 很短的原因：它只携带稳定的骨架，每轮变化的内容由各 provider 追加。

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
});
```

`CreateContextProviders()` 依次返回工作流 provider、技能 provider 与 MCP provider（若挂了压缩，它排在最前）。

**预期结果：** 模型只收到一次骨架；每轮只收到能力包络以及当前的技能与 MCP 状态。

## 发现内置技能

包在 `Resources/Workflow/{lang}/Skills/` 下嵌入了七个工作流流程：

| 名称 | 流程 |
|---|---|
| `compiler-usage` | 编译计划、终端锥、被剪枝的节点、路由模式 |
| `connection-validation` | 连接被拒后如何恢复，而不是重试 |
| `discovery-flow` | 修改前先选好状态刷新策略 |
| `node-creation` | 按出厂顺序创建节点 |
| `operation-ordering` | 避免槽静默丢失的修改生命周期 |
| `slot-enumerator` | 接枚举/布尔选择器与条件槽 |
| `smart-layout` | 预览并应用树注册的布局求解器 |

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Skills;

var skills = new SkillScope().WithSource(new EmbeddedSkillSource("Workflow"));
skills.Refresh();

foreach (var skill in skills.Status.Skills)
    Console.WriteLine($"{skill.Name,-22} {skill.Source,-9} {skill.IsActive}");

Console.WriteLine(skills.BuildEmbeddedBlock(AgentLanguages.English).Length);
```

**预期结果：** 七行记录，全部为 `Embedded`、全部启用，随后是渲染块的字数。

## 关闭一个技能

```csharp
skills.Disable("smart-layout");
Console.WriteLine(skills.Status.Skills.Count(s => s.IsActive)); // 6
Console.WriteLine(skills.BuildEmbeddedBlock(AgentLanguages.English).Contains("smart-layout")); // False
```

`Disable` 会推进 `Version`，按该版本缓存的提示词 provider 因此会重渲染。技能不会被卸载——`IsEnabled` 开关与 `State` 独立，因此重新启用不需要重新发现。

**预期结果：** 六个启用技能，且块中不再出现该名称。`skills.Enable("smart-layout")` 会精确恢复原来的块。

## 在磁盘上添加自己的技能

`FileSkillSource` 遵循 Agent Skills 约定：每个技能一个文件夹，里面有 `SKILL.md` 和可选的 `references/`。

```text
skills/
└── invoice-review/
    ├── SKILL.md
    └── references/
        └── policy.md
```

`SKILL.md` 以 YAML frontmatter 开头：

```markdown
---
name: invoice-review
description: Review an invoice against the company policy before approving it.
---
```

```csharp
var skills = new SkillScope().WithSkillRoot("skills");
skills.Refresh();
```

`WithSkillRoot` 在解析后的路径上添加一个 `FileSkillSource`；该目录允许尚不存在。文件技能只先广告名称与描述，正文要等模型调用 `load_skill` 时才读取。

**预期结果：** `skills.Names` 包含 `invoice-review`，`skills.ReadSkillBody("invoice-review", AgentLanguages.English)` 返回 frontmatter 下方的 Markdown。

## 把子系统接到工作流智能体

```csharp
scope.WithSkills("skills");          // 内嵌语料 + 一个磁盘根
// 或：scope.WithSkills(new SkillScope().WithSource(...));

var toolkit = scope.CreateSkillToolkit();
foreach (var tool in toolkit.CreateTools())
    Console.WriteLine(tool.Name);
```

四个工具是 `ListSkills`、`load_skill`、`UnloadSkill`、`read_skill_resource`。它们由技能 provider 贡献，所以不要再 `WithTools` 注册一遍——框架会把它们送两次。

**预期结果：** 四个工具名。`scope.WithSkills` 同时推进 `scope.Version`，下一轮就能看到变化。

## 验证

1. 运行完整程序。技能块列出七个名称和非零字数。
2. 关闭 `smart-layout` 再渲染；字数下降，名称消失。
3. 重新启用；块与第一次渲染完全一致。
4. 打印 `scope.ProvideFrameworkContext().Length`；对 `TreeDefaultViewModel` scope 它非零，证明发现确实找到了框架树。

## 完整代码

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Skills;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithAutoDiscovery();

Console.WriteLine($"framework context: {scope.ProvideFrameworkContext().Length} chars");
Console.WriteLine($"customer context:  {scope.ProvideCustomerContext().Length} chars");

var skills = new SkillScope()
    .WithSource(new EmbeddedSkillSource("Workflow"))
    .WithSkillRoot("skills");
skills.Refresh();

Console.WriteLine("Skills:");
foreach (var skill in skills.Status.Skills)
    Console.WriteLine($"  {skill.Name,-24} {skill.Source,-9} active={skill.IsActive}");

var before = skills.BuildEmbeddedBlock(AgentLanguages.English);
Console.WriteLine($"embedded block: {before.Length} chars");

skills.Disable("smart-layout");
Console.WriteLine($"after disable:  {skills.BuildEmbeddedBlock(AgentLanguages.English).Length} chars");
Console.WriteLine($"contains smart-layout: {skills.BuildEmbeddedBlock(AgentLanguages.English).Contains("smart-layout")}");

skills.Enable("smart-layout");
Console.WriteLine($"restored: {skills.BuildEmbeddedBlock(AgentLanguages.English) == before}");

scope.WithSkills(skills);
foreach (var tool in scope.CreateSkillToolkit().CreateTools())
    Console.WriteLine($"tool: {tool.Name}");
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`、`Agent/Workflow/AgentContextCollector.cs`、`Agent/Skills/SkillScope.cs`、`EmbeddedSkillSource.cs`、`FileSkillSource.cs`、`SkillAgentToolkit.cs`，以及 `Resources/Workflow/en/Skills/` 下的内嵌文件做了静态核对。七个技能名来自这些文件；没有记录运行输出。
