# Context scope

The scope renders prompt blocks describing the workflow's types and the host's own registered types. These members select the language, register types and produce each prompt shape.

## Language members

| Member | Signature | Description |
|---|---|---|
| `WithPromptLanguage` | `WorkflowAgentScope WithPromptLanguage(AgentLanguages language)` | Sets the default language used when a per-call language argument is null. Call it before the `With*` registrations. |
| `WithOutputLanguage` | `WorkflowAgentScope WithOutputLanguage(AgentLanguages language)` | Sets the language the model should answer in. Independent of the prompt language. |
| `PromptLanguage` | `AgentLanguages PromptLanguage { get; }` | The prompt language in force. |

## Type registration

| Member | Signature | Description |
|---|---|---|
| `WithComponents` | `WorkflowAgentScope WithComponents(Type[] components, AgentLanguages? language = null)` | Registers component types; renders commands, slots and promoted properties. |
| `WithEnums` | `WorkflowAgentScope WithEnums(Type[] enums, AgentLanguages? language = null)` | Registers enums; renders members and their meanings. |
| `WithInterfaces` | `WorkflowAgentScope WithInterfaces(Type[] interfaces, AgentLanguages? language = null)` | Registers interfaces; renders their contract. |
| `WithData` | `WorkflowAgentScope WithData(Type[] dataTypes, AgentLanguages? language = null)` | Registers value objects; renders properties and annotated fields with no operational noise. |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(AgentLanguages? language = null)` | Registers every type the compiled context tree carries under the customer root, classified by the four component interfaces. Framework types are never registered as customer types. |

A type nothing annotated, no component interface reaches and no member references is not in the tree, and is not registered. There is no reflection fallback: an unregistered type renders as nothing.

## Prompt shapes

| Method | Returns | Description |
|---|---|---|
| `ProvideAllContexts()` | `string` | Full context in the default language. |
| `ProvideAllContexts(AgentLanguages language)` | `string` | Full context in the given language. |
| `ProvideProgressiveContextPrompt()` | `string` | A short skeleton that tells the model to discover details through `GetWorkflowSummary`, `GetComponentContext` and `ListComponentCommands`. |
| `ProvideProgressiveContextPrompt(AgentLanguages language)` | `string` | The same skeleton in the given language. |
| `ProvideFrameworkContext(AgentLanguages language = AgentLanguages.English)` | `string` | The framework's own enum, interface and component blocks, read from the tree's `Framework/` directories. |
| `ProvideCustomerContext()` | `string` | Developer-registered types, each in the language it was registered under. |
| `ProvideFrameworkDataContext(AgentLanguages language = AgentLanguages.English)` | `string` | All-mode context for framework data types (`Anchor`, `Offset`, `Size`). |
| `ProvideCustomerDataContext()` | `string` | All-mode context for developer-registered data types. |

`ProvideProgressiveContextPrompt` is deliberately much shorter than `ProvideAllContexts`; the per-turn providers append what changes.

## Class: AgentContextCollector

`VeloxDev.AI.Workflow.AgentContextCollector` renders one type's context block from the compiled context tree. There is no reflection and no fallback: a type the tree does not carry renders as an empty string.

| Method | Returns | Description |
|---|---|---|
| `GetAgentContext(Type type, AgentLanguages language)` | `string[]` | The `[AgentContext]` descriptions of a type, with language fallback applied. |
| `GetAgentContext(MemberInfo member, AgentLanguages language)` | `string[]` | The `[AgentContext]` descriptions of a member. |
| `GetEnumContext(Type enumType, AgentLanguages language)` | `string` | A Markdown block for an enum, or empty when the tree has no entry. |
| `GetInterfaceContext(Type type, AgentLanguages language)` | `string` | A Markdown block for an interface, or empty. |
| `GetClassContext(Type type, AgentLanguages language)` | `string` | A Markdown block for a component, or empty. |
| `GetDataContext(Type type, AgentLanguages language)` | `string` | A compact block for a value object: public properties and `[AgentContext]` fields only. |

## Class: AgentContextAttribute

`VeloxDev.AI.AgentContextAttribute` attaches a natural-language description to a type or member, one entry per language. It is repeatable and not inherited.

```csharp
[AgentContext(AgentLanguages.English, "A node that runs a Python script.")]
[AgentContext(AgentLanguages.Chinese, "运行 Python 脚本的节点。")]
public sealed class ScriptNodeViewModel { }
```

| Member | Type | Description |
|---|---|---|
| Constructor | `AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "")` | One description in one language. |
| `Language` | `AgentLanguages` | The language the description is written in. |
| `Context` | `string` | The description text. |

## Enum: AgentLanguages

`VeloxDev.AI.AgentLanguages : byte` lists the languages the context system can render.

| Value | Name | Value | Name |
|---|---|---|---|
| 0 | `English` | 17 | `Thai` |
| 1 | `ChineseSimplified` (`Chinese` alias) | 18 | `Turkish` |
| 2 | `ChineseTraditional` | 19 | `Italian` |
| 3 | `Japanese` | 20 | `Dutch` |
| 4 | `Korean` | 21 | `Polish` |
| 5 | `French` | 22 | `Czech` |
| 6 | `German` | 23 | `Swedish` |
| 7 | `Spanish` | 24 | `Danish` |
| 8 | `Portuguese` | 25 | `Norwegian` |
| 9 | `Russian` | 26 | `Finnish` |
| 10 | `Arabic` | 27 | `Greek` |
| 11 | `Hindi` | 28 | `Hebrew` |
| 12 | `Bengali` | 29 | `Romanian` |
| 13 | `Urdu` | 30 | `Hungarian` |
| 14 | `Indonesian` | 31 | `Ukrainian` |
| 15 | `Malay` | 32 | `Persian` |
| 16 | `Vietnamese` | | |

## Class: AgentLanguagesExtensions

| Member | Signature | Description |
|---|---|---|
| `AllLanguages` | `static IReadOnlyList<AgentLanguages> AllLanguages { get; }` | Every defined language. |
| `ToLanguageCode` | `static string ToLanguageCode(this AgentLanguages language)` | The short code, e.g. `zh` or `en`. |
| `TryParseLanguageCode` | `static bool TryParseLanguageCode(string languageCode, out AgentLanguages language)` | Parses a code case-insensitively; accepts aliases such as `zh-cn`. |
| `ParseLanguageCode` | `static AgentLanguages ParseLanguageCode(string languageCode)` | Parses a code or throws. |
| `GetDisplayName` | `static string GetDisplayName(this AgentLanguages language)` | The human-readable name. |

Only `en` and `zh` prompt folders are embedded; every other language falls back to `en`.

## Related

- [Skills scope](../01_skills-scope/index.md) — attaching switchable procedures.
- [WorkflowAgentScope](../../17_workflow-agent-tools/00_workflow-agent-scope/index.md) — the scope these members extend.
