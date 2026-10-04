# 10.0 · Skills

A **skill** is a piece of guidance (plus optional bundled resource files) the model can pull in on demand. The library ships its own prompt documents as embedded skills; an application adds its own as folders on disk.

```csharp
scope.WithSkills("skills");        // a disk root, resolved against AppContext.BaseDirectory
//        ^ allowed not to exist yet — the embedded corpus still arrives
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

`WithSkills(string rootPath)` and `WithSkills(SkillScope skills)` both attach the subsystem. Attaching it **before** `ProvideProgressiveContextPrompt()` is the order that leaves the corpus under the subsystem's dynamic control — the skeleton then carries no copy of it. Attaching after still works; the subsystem then only reports which skills have been switched off since.

**Expected result:** after `WithSkills("skills")` the model is offered `ListSkills`, `load_skill`, `UnloadSkill`, `read_skill_resource`, and the embedded corpus ("Skill: …" blocks) reaches the prompt.

## 1. `SkillScope` — the subsystem

| Member | Signature | Notes |
|---|---|---|
| `WithSkillRoot` | `WithSkillRoot(string path)` | Adds a disk-backed root (relative resolved against `AppContext.BaseDirectory`). |
| `WithSource` | `WithSource(ISkillSource source)` | Adds a source; registration order, first to declare a name owns it. |
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | The language skills are rendered and read in. |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | Marshalling target. |
| `CreateContextProvider` | `CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null, bool embeddedCorpusDelivered = false)` | The provider. |
| `Status` | `SkillsViewModel { get; }` | Bindable per-skill status + aggregates. |
| `Version` | `long { get; }` | Render cache key; advances on every real change. |
| `Names` | `IReadOnlyList<string> { get; }` | The discovered skill names. |
| `Refresh` / `SetEnabled` / `Enable` / `Disable` | | Rediscover, or switch a skill on/off (`SetEnabled` returns whether it moved). |
| `Find` | `SkillStatusViewModel? Find(string name)` | One skill's row. |
| `ReadSkillBody` / `ReadSkillResource` | `string? …(string name, …)` | Read a body / a bundled resource. |

## 2. The four tools

| Tool | Required parameters | Purpose |
|---|---|---|
| `ListSkills` | — | Every discovered skill: source (`Embedded`/`File`), state, enabled flag, resource count, error, plus aggregates. Pure query. |
| `load_skill` | `name` (implied) / skill name | Reads a skill's full text and switches it on. For a **file** skill this is the only way to read its body; for an **embedded** skill the text is already in the instructions but is returned anyway. |
| `UnloadSkill` | skill name | Switches a skill off — it stops contributing to the instructions without re-discovering anything. |
| `read_skill_resource` | skill name + relative path | Reads a bundled resource (a reference doc, schema or data file). Only meaningful for file skills; embedded skills ship none. |

All four are read-only with respect to the workflow graph (folded into the toolkit's read-only set, so they never mark the tree dirty). Source: `SkillAgentToolkitTests.CreateTools_RegistersTheFourSkillTools`, `SkillAgentContextProviderTests.BuildContext_ContributesTheFourSkillToolsWrapped`.

A failed `load_skill` for an unknown name is an **actionable error** whose message names `ListSkills`; `read_skill_resource` on an embedded skill says there are `no resources`; a traversal path (`"../secret.md"`) is refused. Source: `SkillAgentToolkitTests`.

## 3. Embedded vs file skills

| | Embedded (`SkillSourceKind.Embedded`) | File (`SkillSourceKind.File`) |
|---|---|---|
| Where from | assembly resources under `Resources/{System}/{lang}/Skills/` | a folder with `SKILL.md` + resources |
| Prompt | injected **in full** when enabled | **advertised only** (name + description) — use `load_skill` |
| Resources | none | shipped beside the skill; counted in `ResourceCount` |
| Language | per language, with English fallback | the folder's frontmatter |

`FileSkillSource` reads frontmatter (`name`, `description`), strips it from the body, and reports problems rather than swallowing them: a folder-name/`name` mismatch, missing frontmatter (name falls back to the folder), or a non-kebab-case name each surface as a non-empty `Error`. `.`/`..`/absolute resource paths that escape the skill directory return `null`. Source: `SkillScopeTests.FileSource_*`.

`EmbeddedSkillSource("Workflow")` discovers the library's shipped skills (7 names × 2 languages = 14 descriptors); names are derived kebab-case from the file names. Source: `SkillScopeTests.EmbeddedSource_DiscoversEveryShippedSkillInBothLanguages`.

## 4. The descriptor and state model

`ISkillSource` is the seam: `Discover()` → `IReadOnlyList<SkillDescriptor>`; `ReadBody`; `ReadResource`. `SkillDescriptor` carries `Name`, `Description`, `Source`, `Path`, `Language`, `ResourceCount`, `Error`. `SkillState` is `NotStarted`, `Loading`, `Ready`, `Error`.

`SkillStatusViewModel` (bindable) and `SkillSummary` (immutable) both carry the same facts; the `SkillsViewModel` aggregate exposes `ActiveCount`, `ErrorCount`, `HasError` and a `Snapshot`.

**Expected result:** a skill that failed to parse shows `State == Error` with a non-empty `Error` and `IsActive == false`.

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite (2026-10-01, `已通过! 失败: 0，通过: 387`) includes `Skills/**` (`SkillScopeTests`, `SkillAgentToolkitTests`, `SkillAgentContextProviderTests`), covering discovery in both languages, the enabled/withdrawn blocks, the four tools, resource traversal refusal, and the render cache.
