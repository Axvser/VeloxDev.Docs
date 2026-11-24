# Skill sources

A source is the seam that lets `SkillScope` treat embedded prompt documents and on-disk Agent Skills folders uniformly. Discovery never produces a skill's text; that is `ReadBody`'s job, which keeps a large skill free until the model asks for it.

## Interface: ISkillSource

| Member | Signature | Description |
|---|---|---|
| `Kind` | `SkillSourceKind Kind { get; }` | Which loader this is; decides the skill's injection mode. |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | Enumerates the skills this source can serve. May yield the same name more than once when the text exists in several languages. |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | Reads a skill's full text for the requested language; `null` when unavailable. |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | Reads one bundled resource, addressed relative to the skill directory. |

Discovery is side-effect free. A file skill's `SKILL.md` is read in full because the frontmatter cannot be parsed otherwise, but its bundled resources are only enumerated, never opened.

## Class: EmbeddedSkillSource

Discovers prompt documents embedded in an assembly under `Resources/{System}/{lang}/Skills/{Name}.md`. Names come from YAML frontmatter when present and from the file name otherwise.

| Member | Signature | Description |
|---|---|---|
| Constructor | `EmbeddedSkillSource(string system)` | Creates a source over the embedded skills of a system, e.g. `"Workflow"`. |
| `Kind` | `SkillSourceKind` | Always `Embedded`. |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | One descriptor per (name, language) because the same skill normally exists once per supported language. |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | Reads the embedded body. |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | Always returns `null`: embedded skills carry no per-skill resources; the shared References corpus is separate. |

## Class: FileSkillSource

Discovers skills on disk as `<root>/<name>/SKILL.md`, following the Agent Skills convention. A `references/` tree beside `SKILL.md` ships extra documents that are counted at discovery but read only on demand.

| Member | Signature | Description |
|---|---|---|
| Constructor | `FileSkillSource(string rootPath)` | Creates a source over a root. Discovery is deferred to `Discover`; the directory need not exist yet. |
| `Kind` | `SkillSourceKind` | Always `File`. |
| `Root` | `string` | The resolved root directory. |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | Finds the skill folders (or a single `SKILL.md` directly in the root). |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | Reads `SKILL.md` below the frontmatter. |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | Reads one file under the skill's `references/` tree. |

File skills are language-neutral, so the `language` argument is accepted for interface uniformity and ignored.

## Related

- [Skills scope](../01_skills-scope/index.md) — consuming these sources.
- [Skill status](../02_skill-status/index.md) — the descriptors a source yields.
