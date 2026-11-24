# Usage

## Render the prompt layers

The scope splits the prompt by how often it changes. This is the reason `ProvideProgressiveContextPrompt()` is short: it carries the stable skeleton, and the per-turn providers append what moves.

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
});
```

`CreateContextProviders()` returns the workflow provider, the skill provider and the MCP provider, in that order (compaction, if attached, comes first).

**Expected result:** the model receives the skeleton once, and on each turn receives only the capability envelope and the current skill and MCP state.

## Discover the embedded skills

The package embeds seven workflow procedures under `Resources/Workflow/{lang}/Skills/`:

| Name | Procedure |
|---|---|
| `compiler-usage` | compile plans, terminal cones, pruned nodes, routing modes |
| `connection-validation` | recover from a rejected connection instead of retrying |
| `discovery-flow` | choose a state-refresh strategy before mutating |
| `node-creation` | create a node in the shipped order |
| `operation-ordering` | the mutation lifecycle that avoids silent slot loss |
| `slot-enumerator` | wire enum/bool selectors and conditional slots |
| `smart-layout` | preview and apply the tree's layout solver |

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Skills;

var skills = new SkillScope().WithSource(new EmbeddedSkillSource("Workflow"));
skills.Refresh();

foreach (var skill in skills.Status.Skills)
    Console.WriteLine($"{skill.Name,-22} {skill.Source,-9} {skill.IsActive}");

Console.WriteLine(skills.BuildEmbeddedBlock(AgentLanguages.English).Length);
```

**Expected result:** seven rows, all `Embedded`, all active, followed by a character count for the rendered block.

## Switch a skill off

```csharp
skills.Disable("smart-layout");
Console.WriteLine(skills.Status.Skills.Count(s => s.IsActive)); // 6
Console.WriteLine(skills.BuildEmbeddedBlock(AgentLanguages.English).Contains("smart-layout")); // False
```

`Disable` advances `Version`, so a prompt provider caching on that version re-renders. The skill is not unloaded — an `IsEnabled` switch is independent of `State`, so re-enabling costs no rediscovery.

**Expected result:** six active skills and the disabled name absent from the block. `skills.Enable("smart-layout")` restores the original block exactly.

## Add your own skills on disk

`FileSkillSource` follows the Agent Skills convention: one folder per skill, containing `SKILL.md` and an optional `references/` tree.

```text
skills/
└── invoice-review/
    ├── SKILL.md
    └── references/
        └── policy.md
```

`SKILL.md` starts with YAML frontmatter:

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

`WithSkillRoot` adds a `FileSkillSource` over the resolved path; the directory is allowed not to exist yet. File skills are advertised with their name and description, and their body is read only when the model calls `load_skill`.

**Expected result:** `skills.Names` contains `invoice-review`, and `skills.ReadSkillBody("invoice-review", AgentLanguages.English)` returns the Markdown below the frontmatter.

## Attach the subsystem to a workflow agent

```csharp
scope.WithSkills("skills");          // embedded corpus + a disk root
// or: scope.WithSkills(new SkillScope().WithSource(...));

var toolkit = scope.CreateSkillToolkit();
foreach (var tool in toolkit.CreateTools())
    Console.WriteLine(tool.Name);
```

The four tools are `ListSkills`, `load_skill`, `UnloadSkill`, `read_skill_resource`. They are contributed by the skill provider, so do not also register them with `WithTools` — the framework would send them twice.

**Expected result:** four tool names. `scope.WithSkills` also advances `scope.Version`, so the next turn sees the change.

## Verification

1. Run the complete program. The skill block lists seven names and a non-zero character count.
2. Disable `smart-layout` and re-render; the count drops and the name is absent.
3. Re-enable it; the block matches the first rendering exactly.
4. Print `scope.ProvideFrameworkContext().Length`; it is non-zero for a `TreeDefaultViewModel` scope, which proves discovery found the framework tree.

## Complete code

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

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`, `Agent/Workflow/AgentContextCollector.cs`, `Agent/Skills/SkillScope.cs`, `EmbeddedSkillSource.cs`, `FileSkillSource.cs`, `SkillAgentToolkit.cs`, and the embedded files under `Resources/Workflow/en/Skills/`. The seven skill names are read from those files; no run output is recorded.
