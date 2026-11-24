# Skill tools

The skill subsystem reaches the model through four tools contributed by a context provider. The embedded-resource reader is the package-side accessor that the embedded source and the prompt skeleton share.

## Class: SkillAgentToolkit

`VeloxDev.AI.Skills.SkillAgentToolkit` is the agent-facing view of a `SkillScope`. Its shape mirrors `McpAgentToolkit`: host and agent operate one shared data layer.

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `SkillAgentToolkit(SkillScope scope)` | Binds the tools to a skill set. |
| `Language` | `AgentLanguages Language { get; set; }` | Prompt language skill text is read in. Defaults to English. |
| `ToolNames` | `static readonly string[] ToolNames` | `["ListSkills", "load_skill", "UnloadSkill", "read_skill_resource"]`. |
| `CreateTools()` | `IList<AITool> CreateTools()` | The four tools, unwrapped: no marshalling or accounting. |
| `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | The four tools wrapped so every call is marshalled, gated and reported. This is what a provider contributes. |

The names `load_skill` and `read_skill_resource` follow the Agent Skills convention, so a model already trained on it needs no extra instruction. All four are read-only with respect to the workflow graph, so a workflow host keeps them out of the mutation budget and dirty marking.

### The tools

| Tool | Purpose |
|---|---|
| `ListSkills` | Lists the discovered skills and their switch state. |
| `load_skill` | Loads one skill's body. |
| `UnloadSkill` | Unloads a previously loaded skill. |
| `read_skill_resource` | Reads one bundled resource of a skill. |

Do not also register these with `WithTools`: the framework unions tool lists without deduplicating by name.

## Class: SkillAgentContextProvider

`VeloxDev.AI.Skills.SkillAgentContextProvider : AIContextProvider` contributes a skill scope's current state to an agent invocation: the enabled skills' text, plus the four tools. Attach it to any agent and the model gains skills without the workflow layer.

| Member | Signature | Description |
|---|---|---|
| Constructor | `SkillAgentContextProvider(SkillScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | Creates a provider over a scope. Omit `tools` for standalone use; pass `embeddedCorpusDelivered: true` when the prompt already carries the embedded corpus. |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | The provider's state keys. |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | Renders the skill contribution. |

The render is cached on the scope's `Version` and prompt language. When `embeddedCorpusDelivered` is `true`, the provider contributes the corpus's difference (`BuildWithdrawnBlock`) instead of the corpus itself, which keeps every skill document from reaching the model twice.

## Class: AgentEmbeddedResources

`VeloxDev.AI.AgentEmbeddedResources` reads Markdown embedded in `VeloxDev.Core.Extension` under `Resources/{System}/{LangCode}/`. It is what `EmbeddedSkillSource` and the prompt skeleton use.

| Method | Returns | Description |
|---|---|---|
| `ToLanguageCode(AgentLanguages language)` | `string` | Folder code: `"zh"` or `"en"`. Every other language resolves to `"en"`. |
| `ReadSkill(string system, string name, AgentLanguages language = AgentLanguages.English)` | `string?` | Reads `Skills/{name}.md`, falling back to English; `null` when neither exists. |
| `ListSkills(string system, AgentLanguages language = AgentLanguages.English)` | `IEnumerable<string>` | Base names of all skill files for a system and language. |
| `ListSkillsExact(string system, AgentLanguages language)` | `IEnumerable<string>` | Base names that exist in exactly that language, with no English fallback. |
| `ReadAllSkills(string system, AgentLanguages language = AgentLanguages.English)` | `string` | Concatenates all skill files, separated by blank lines. |
| `ReadAllReferences(string system, AgentLanguages language = AgentLanguages.English)` | `string` | Concatenates all reference files, separated by blank lines. |
| `ReadSafety(string system, string name, AgentLanguages language = AgentLanguages.English)` | `string?` | Reads `Safety/{name}.md`, falling back to English. |

Adding a file under `Resources/{System}/{LangCode}/` is enough: the project glob embeds it.

## Example

```csharp
using VeloxDev.AI.Skills;

var toolkit = scope.CreateSkillToolkit();
foreach (var tool in toolkit.CreateTools())
    Console.WriteLine(tool.Name);
```

## Related

- [Skills scope](../01_skills-scope/index.md) — what the tools operate on.
- [Context scope](../00_context-scope/index.md) — the skeleton that may already carry the corpus.
