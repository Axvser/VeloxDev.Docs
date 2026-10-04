# Workflow Agent — Namespace: `VeloxDev.AI.Skills`

The skill subsystem: a library of Agent Skills the model can discover, load, switch off and read resources from. A host attaches it with `WorkflowAgentScope.WithSkills(...)`; `SkillAgentContextProvider` contributes the four skill tools and the skill corpus per turn, and `SkillScope` is the management surface. All types live in `VeloxDev.AI.Skills` (implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Skills/`).

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Skills/*` — `SkillScopeTests`, `SkillAgentToolkitTests`, `SkillAgentContextProviderTests`) + **Demo** (`AgentHelper.ProvideAgent` — `.WithSkills("skills")`).

## SkillScope

`public class SkillScope`.

| Member | Type / Signature | Notes |
|---|---|---|
| `Status` | `SkillsViewModel { get; }` | Bindable per-skill status + aggregates. |
| `Version` | `long { get; }` | Render cache key; advances on every real change (including language). |
| `PromptLanguage` | `AgentLanguages { get; private set; }` | Default `English`. |
| `Names` | `IReadOnlyList<string> { get; }` | Discovered skill names. |
| `WithPromptLanguage` | `SkillScope WithPromptLanguage(AgentLanguages)` | Sets the render/read language; bumps `Version`. |
| `WithSkillRoot` | `SkillScope WithSkillRoot(string path)` | Adds a disk root (delegates to `WithSource(new FileSkillSource(...))`). |
| `WithSource` | `SkillScope WithSource(ISkillSource source)` | Adds a source (registration order; first to declare a name owns it). |
| `WithSynchronizationContext` | `SkillScope WithSynchronizationContext(SynchronizationContext?)` | UI marshalling target. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | The provider. |
| `Refresh` | `void Refresh()` | Rediscover; enabled flags are preserved. |
| `SetEnabled` / `Enable` / `Disable` | `bool …(string name, …)` | Switch a skill; `SetEnabled` returns whether it moved. |
| `Find` | `SkillStatusViewModel? Find(string name)` | One skill's row. |
| `BuildEmbeddedBlock` / `BuildWithdrawnBlock` / `BuildAdvertisement` | `string …(AgentLanguages language)` | The prompt fragments (enabled bodies / withdrawn names / file-skill advertisement). |
| `ReadSkillBody` / `ReadSkillResource` | `string? …(string name, …)` | Read a body / a bundled resource. |

## Toolkit and provider

`public sealed class SkillAgentToolkit(SkillScope scope)`:

| Member | Signature | Notes |
|---|---|---|
| `Language` | `AgentLanguages { get; set; }` | Default `English`; set from the scope's prompt language. |
| `ToolNames` | `public static readonly string[]` | `["ListSkills", "load_skill", "UnloadSkill", "read_skill_resource"]`. |
| `CreateTools` | `IList<AITool> CreateTools()` / `CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | The four tools, wrapped when a pipeline is given. |

`public sealed class SkillAgentContextProvider : AIContextProvider` — constructor `(SkillScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)`. Contributes the (wrapped) four tools and the corpus/withdrawn/advertisement text per turn; caches its render on `SkillScope.Version`; `StateKeys` is per scope. When nothing is enabled it contributes no instructions but still contributes the tools.

## Descriptor / state model

| Type | Kind | Members |
|---|---|---|
| `ISkillSource` | interface | `SkillSourceKind Kind { get; }`, `IReadOnlyList<SkillDescriptor> Discover()`, `string? ReadBody(string skillName, AgentLanguages language)`, `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` |
| `SkillDescriptor` | sealed class | `Name`, `Description`, `Source`, `Path`, `Language`, `ResourceCount`, `Error` |
| `EmbeddedSkillSource` | sealed class | `EmbeddedSkillSource(string system)` — reads the assembly's embedded skills |
| `FileSkillSource` | sealed class | `FileSkillSource(string rootPath)` — reads `SKILL.md` folders; `Root` exposed |
| `SkillState` | enum | `NotStarted = 0`, `Loading = 1`, `Ready = 2`, `Error = 3` |
| `SkillSourceKind` | enum | `Embedded = 0`, `File = 1` |
| `SkillStatusViewModel` | partial class | `Name`, `Description`, `State`, `Source`, `Path`, `IsEnabled`, `ResourceCount`, `Error`, `IsReady`, `IsError`, `IsActive`, `HasResources`, `StateText` |
| `SkillSummary` | sealed class | `Name`, `Description`, `Source`, `IsActive` |
| `SkillsViewModel` | partial class | `Skills`, `Snapshot`, `ActiveCount`, `ErrorCount`, `HasError`, `Track(...)`, `Reset()` |

## Tools

| Tool | Purpose |
|---|---|
| `ListSkills` | Every discovered skill: source, state, enabled flag, resource count, error + aggregates. Pure query. |
| `load_skill` | Reads a skill's full text and switches it on. The only way to read a **file** skill's body. |
| `UnloadSkill` | Switches a skill off (no re-discovery). |
| `read_skill_resource` | Reads a bundled resource; a traversal path is refused; embedded skills have none. |

All four are read-only with respect to the workflow graph. `SkillFrontmatter` (internal) enforces the `name` (≤ 64) / `description` (≤ 1024) limits and strips frontmatter from the body.
