# Skill status

`VeloxDev.AI.Skills` exposes three related views of the discovered skills: a bindable row per skill, an immutable summary safe off the UI thread, and the aggregate collection `SkillScope.Status` holds. `SkillDescriptor` is the discovery-time record behind them.

## Class: SkillStatusViewModel

One skill as a bindable row, following the framework's `[VeloxProperty]` conventions. `IsEnabled` is deliberately independent of `State`: a skill can be readable and switched off, and switching it off must not unload it.

### Generated properties

| Name | Type | Description |
|---|---|---|
| `Name` | `string` | Skill name. |
| `Description` | `string` | One-line description used to match a request. |
| `State` | `SkillState` | Lifecycle state. |
| `Source` | `SkillSourceKind` | Which loader produced it. |
| `Path` | `string?` | Emitted resource name or file path; reporting only. |
| `IsEnabled` | `bool` | Whether the skill may contribute to the prompt. Default `true`. |
| `ResourceCount` | `int` | Number of bundled resource files. |
| `Error` | `string?` | Why the skill is unusable, or `null`. |

### Computed members

| Name | Type | Description |
|---|---|---|
| `IsReady` | `bool` | `State == Ready`. |
| `IsError` | `bool` | `State == Error`. |
| `IsActive` | `bool` | `IsReady && IsEnabled` — it contributes to the prompt. |
| `HasResources` | `bool` | `ResourceCount > 0`. |
| `ResourceNames` | `IReadOnlyList<string>` | Bundled resource paths, relative to the skill directory, using `/` separators — exactly what `read_skill_resource` takes. |
| `StateText` | `string` | Display text for the state. |

## Class: SkillSummary

An immutable copy of one skill's identity and switch state, safe to read from any thread.

| Member | Type | Description |
|---|---|---|
| `Name` | `string` | Skill name. |
| `Description` | `string` | One-line description. |
| `Source` | `SkillSourceKind` | Which loader produced it. |
| `IsActive` | `bool` | Readable and switched on. |

## Class: SkillsViewModel

The globally bindable skill view-model held by `SkillScope.Status`.

| Member | Type / Signature | Description |
|---|---|---|
| `Skills` | `ObservableCollection<SkillStatusViewModel>` | The bindable rows, generated from the tracked collection. |
| `Snapshot` | `IReadOnlyList<SkillSummary>` | An immutable copy, republished on the bound thread whenever a tracked skill changes. Read this from any other thread. |
| `ActiveCount` | `int` | Skills that are readable and switched on. |
| `ErrorCount` | `int` | Skills that failed to load. |
| `HasError` | `bool` | Whether at least one skill failed. |
| `Track` | `void Track(SkillStatusViewModel skill)` | Registers a skill and subscribes to its changes so the aggregates refresh. |
| `Reset` | `void Reset()` | Removes every tracked skill. |

An agent invocation renders its prompt on a thread of the framework's choosing, so enumerating `Skills` there races the host's UI. Use `Snapshot` off the bound thread.

## Class: SkillDescriptor

What a source knows about a skill before its body is read. A source may yield several descriptors for the same name — one per language — because a skill is toggled as one concept while its text is rendered per prompt language.

| Member | Type | Description |
|---|---|---|
| `Name` | `string` | Skill name. For file skills this must match the parent directory name. |
| `Description` | `string` | One-line description. |
| `Source` | `SkillSourceKind` | Which loader produced this descriptor. |
| `Path` | `string?` | File path or embedded resource name; reporting only. |
| `Language` | `AgentLanguages?` | The text's language, or `null` for language-neutral file skills. |
| `ResourceCount` | `int` | Number of bundled resource files, counted but not opened at discovery. |
| `ResourceNames` | `IReadOnlyList<string>` | Relative resource paths using `/` separators — the form `read_skill_resource` accepts. |
| `Error` | `string?` | Why the skill is unusable, or `null`. A malformed skill is reported, not thrown or dropped. |

## Related

- [Skills scope](../01_skills-scope/index.md) — discovery and toggling.
- [Skill sources](../03_skill-sources/index.md) — where descriptors come from.
