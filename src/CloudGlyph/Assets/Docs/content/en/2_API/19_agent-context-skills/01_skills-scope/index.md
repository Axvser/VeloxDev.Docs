# Skills scope

`VeloxDev.AI.Skills.SkillScope` is the skill data layer: it discovers skills from one or more sources, exposes each as a bindable switch, and renders the prompt shapes a skill can take. Attach it to a workflow scope with `WithSkills`.

## Attachment members on WorkflowAgentScope

| Member | Signature | Description |
|---|---|---|
| `WithSkills` | `WorkflowAgentScope WithSkills(string rootPath)` | Discovers skills from a disk root and moves the library's embedded prompt documents into the same switchable list. |
| `WithSkills` | `WorkflowAgentScope WithSkills(SkillScope skills)` | Attaches an already-built scope, to share one data layer or supply custom sources. |
| `Skills` | `SkillScope? Skills { get; }` | The attached scope, or `null`. Whichever side is attached second owns the embedded corpus. |
| `CreateSkillToolkit()` | `SkillAgentToolkit CreateSkillToolkit()` | The model-facing skill tools, bound to this scope's skill set and prompt language. |

## Class: SkillScope

| Member | Type / Signature | Description |
|---|---|---|
| `Status` | `SkillsViewModel` | Bindable skill list and aggregate counts. |
| `Version` | `long` | Monotonic version of the discovered set and enabled flags. A provider caches its render on it. |
| `PromptLanguage` | `AgentLanguages` | The language skill text is rendered and read in. |
| `WithPromptLanguage` | `SkillScope WithPromptLanguage(AgentLanguages language)` | Sets the prompt language; advances `Version`. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | Creates the provider that contributes skill text and tools. Pass `true` when the prompt already carries the embedded corpus. |
| `WithSynchronizationContext` | `SkillScope WithSynchronizationContext(SynchronizationContext? context)` | Marshals discovery results and flag changes to a UI thread. |
| `WithSkillRoot` | `SkillScope WithSkillRoot(string path)` | Adds a disk-backed root. A relative path resolves against the application base; the directory need not exist yet. |
| `WithSource` | `SkillScope WithSource(ISkillSource source)` | Adds a source. Sources are consulted in order; the first to declare a name owns it. |
| `Refresh` | `void Refresh()` | Rediscovers every source and rebuilds `Status`. Enabled flags are preserved by name. Advances `Version`. |
| `SetEnabled` | `bool SetEnabled(string name, bool enabled)` | Switches a skill on or off; `false` when no skill of that name was discovered. |
| `Enable` | `bool Enable(string name)` | Switches a skill on. |
| `Disable` | `bool Disable(string name)` | Switches a skill off. |
| `BuildEmbeddedBlock` | `string BuildEmbeddedBlock(AgentLanguages language)` | The full text of every enabled **embedded** skill, in name order. |
| `BuildWithdrawnBlock` | `string BuildWithdrawnBlock(AgentLanguages language)` | For a prompt that already carries the corpus: names the skills switched off since, and instructs the model to disregard them. Empty while nothing has drifted. |
| `BuildAdvertisement` | `string BuildAdvertisement()` | Each enabled **file** skill's name and description, plus the instruction to load a body before following it. |
| `ReadSkillBody` | `string? ReadSkillBody(string name, AgentLanguages language)` | A skill's full text, whether enabled or not. |
| `ReadSkillResource` | `string? ReadSkillResource(string name, string relativePath, AgentLanguages language)` | One bundled resource, addressed relative to the skill directory. |
| `Find` | `SkillStatusViewModel? Find(string name)` | A discovered skill by name, or `null`. Call on the bound thread. |
| `Names` | `IReadOnlyList<string> Names` | Discovered names, snapshot-backed and safe off the bound thread. |

### Two injection shapes

- **Embedded** skills are architectural prompt text. When enabled, their body is injected in full. With every skill enabled, `BuildEmbeddedBlock` is byte-for-byte what the prompt carried before skills became switchable.
- **File** skills follow the Agent Skills convention. Only name and description reach the prompt; the body is fetched through `load_skill`. That keeps a large external library from costing every turn.

Switching a skill off does not unload it: `IsEnabled` is independent of `State`, so re-enabling costs no rediscovery. `Disable` advances `Version`, so a provider caching on it re-renders.

`Refresh` is a host action, not a per-turn one: it always advances `Version`, so calling it from a prompt provider every turn would defeat the cache.

## Enum: SkillSourceKind

Where a skill came from; this drives its injection mode.

| Member | Value | Meaning |
|---|---|---|
| `Embedded` | `0` | Shipped in an assembly; injected in full while enabled. |
| `File` | `1` | Discovered on disk; advertised and loaded on demand. |

## Enum: SkillState

Lifecycle of a discovered skill. It mirrors `McpServerStatus` without the Installing/Connecting split.

| Member | Value |
|---|---|
| `NotStarted` | `0` |
| `Loading` | `1` |
| `Ready` | `2` |
| `Error` | `3` |

## Example

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

## Related

- [Skill status](../02_skill-status/index.md) — the bindable rows this scope holds.
- [Skill sources](../03_skill-sources/index.md) — what `WithSource` accepts.
- [Skill tools](../04_skill-tools/index.md) — the model-facing tools.
