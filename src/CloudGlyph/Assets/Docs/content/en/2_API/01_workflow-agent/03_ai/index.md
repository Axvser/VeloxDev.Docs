# Workflow Agent — Namespace: `VeloxDev.AI`

Generic (non-workflow) AI plumbing shared by the workflow agent: `[AgentContext]` attributes that document types/members for the LLM, the `AgentLanguages` enum, reflection utilities that read context / discover and invoke commands, properties and methods, plus the interaction event args and notifier contracts the scope raises. Core types are implemented in `Src/Core/VeloxDev.Core/AI/`; the generic object toolkit and embedded-resource reader live in `Src/Core/VeloxDev.Core.Extension/Agent/`. Framework-agnostic — usable with any object.

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Test/AI/*`).

## Attributes

### `AgentContextAttribute`

`public class AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "") : Attribute`. `AttributeUsage(All, Inherited = false, AllowMultiple = true)`. Properties `Language` (`AgentLanguages`) and `Context` (`string`). Documents any target (type, property, field, method, enum member) for the Agent; multiple allowed per target. Source: `AgentContextAttribute.cs`.

### `AgentCommandParameterAttribute`

`public class AgentCommandParameterAttribute : Attribute` with ctors `()` (no parameter) and `(Type parameterType)`. `AttributeUsage(Property | Method | Field, AllowMultiple = false)`. Property `Type? ParameterType` — the concrete .NET type the Agent should construct when invoking the command. Source: `AgentCommandParameterAttribute.cs`.

### `SlotSelectorsAttribute`

`public sealed class SlotSelectorsAttribute` with ctors `(params Type[])` and `(params string[])` (the string form stores fully-qualified type names for serialization). `AttributeUsage(Property | Field, AllowMultiple = false)`. Properties `Type[] AllowedEnumTypes`, `string[] AllowedEnumTypeNames`. Whitelists the selector types of a `SlotEnumerator<TSlot>` property; read by `ListSlotProperties`/`SetEnumSlotCollection`, and `PatchNodeProperties` rejects `[SlotSelectors]`-marked properties. Source: `SlotSelectorsAttribute.cs`.

## AgentLanguages

`public enum AgentLanguages : byte` — `English`, `ChineseSimplified` (alias `Chinese`), `ChineseTraditional`, `Japanese`, `Korean`, `French`, `German`, `Spanish`, `Portuguese`, `Russian`, `Arabic`, `Hindi`, `Bengali`, `Urdu`, `Indonesian`, `Malay`, `Vietnamese`, `Thai`, `Turkish`, `Italian`, `Dutch`, `Polish`, `Czech`, `Swedish`, `Danish`, `Norwegian`, `Finnish`, `Greek`, `Hebrew`, `Romanian`, `Hungarian`, `Ukrainian`, `Persian`.

`AgentLanguagesExtensions` (same file): `string ToLanguageCode(this AgentLanguages)`, `bool TryParseLanguageCode(string, out AgentLanguages)`, `AgentLanguages ParseLanguageCode(string)` (throws `ArgumentException` on unsupported codes), `string GetDisplayName(this AgentLanguages)`. Tested by `AgentLanguagesTests`.

## Reflection utilities (Core)

### `AgentContextReader`

`public static class AgentContextReader` — reads `[AgentContext]` values by language: `string[] GetContexts(Type, AgentLanguages)`, `string[] GetContexts(MemberInfo, AgentLanguages)`, `bool HasAgentContext(MemberInfo)`. Tested by `AgentContextReaderTests`.

### `AgentCommandDiscoverer`

`public static class AgentCommandDiscoverer` — generic `ICommand` discovery/execution for any object.

| Member | Signature | Notes |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object target, AgentLanguages language = English)` | Interface command properties first (authoritative attributes), then concrete-type properties (deduplicated). |
| `Execute` | `ExecuteResult Execute(object target, string commandName, object? parameter = null)` | Executes a named command; appends `"Command"` if missing. |
| `CanExecuteCommand` | `bool CanExecuteCommand(object target, string commandName, object? parameter = null)` | Current `CanExecute` for the named command. |
| `FindBackingCommand` | `string? FindBackingCommand(Type type, string propertyName)` | Finds `Set{Name}Command`/`{Name}Command` (property or interface). |

Nested `sealed CommandDescriptor` (`Name`, `Type? ParameterType`, `IReadOnlyList<string> AgentDescriptions`, `bool CanExecute`) and `sealed ExecuteResult` (`CommandName`, `bool Success`, `string? Error`). Tested by `AgentCommandDiscovererTests`.

### `AgentMethodInvoker`

`public static class AgentMethodInvoker` — reflection method discovery/invocation.

| Member | Signature | Notes |
|---|---|---|
| `DiscoverMethods` | `IReadOnlyList<MethodDescriptor> DiscoverMethods(object target, AgentLanguages language = English, bool includeStatic = false, Func<MethodInfo, bool>? filter = null)` | Public methods, excluding property accessors and `object` methods. |
| `Invoke` | `InvokeResult Invoke(object target, string methodName, params object?[]? args)` | Overload resolution by parameter count; best-effort type conversion; pads optional params. |
| `InvokeStatic` | `InvokeResult InvokeStatic(Type type, string methodName, params object?[]? args)` | Static overload. |

Nested `MethodDescriptor`, `ParameterDescriptor`, `InvokeResult` (`Success`/`ReturnValue`/`Error`). Tested by `AgentMethodInvokerTests`.

### `AgentPropertyAccessor`

`public static class AgentPropertyAccessor` — generic property read/write.

| Member | Signature | Notes |
|---|---|---|
| `DiscoverProperties` | `IReadOnlyList<PropertyDescriptor> DiscoverProperties(object target, AgentLanguages language = English, Func<PropertyInfo, bool>? filter = null, bool includeValues = false)` | Public instance properties + `[AgentContext]` descriptions. |
| `GetPropertyValue` | `object? GetPropertyValue(object target, string propertyName)` | Reads a property; `null` when missing/not readable. |
| `SetPropertyValue` | `SetResult SetPropertyValue(object target, string propertyName, object? value)` | Writes a property with `ConvertValue` (primitives, enums via `Enum.Parse`, nullable handling). |
| `SetProperties` | `IReadOnlyList<SetResult> SetProperties(object target, IReadOnlyDictionary<string, object?> properties, ISet<string>? rejected = null)` | Batch set; rejected names are skipped with an error. |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target, Func<PropertyInfo, bool>? skip = null)` | Copies scalar/enum writable properties. |

Nested `PropertyDescriptor`, `SetResult`. Tested by `AgentPropertyAccessorTests`.

### `AgentTypeResolver`

`public static class AgentTypeResolver` — `Type? ResolveType(string fullTypeName)`; resolves via `Type.GetType`, then by scanning all loaded assemblies. Tested by `AgentTypeResolverTests`.

## Event args and notifier contracts

| Type | Members |
|---|---|
| `AgentSelectionEventArgs` | `sealed`; ctor `(string prompt, string[] options)`. `Prompt`, `Options` (`IReadOnlyList<string>`), `AllowMultiSelect` (default `false`), `FreeTextPrompt` (default `"Custom input (optional)"`), `SelectedOption` (`string?`), `SelectedOptions` (`IReadOnlyList<string>?`), `FreeTextResponse` (`string?`). |
| `AgentConfirmationEventArgs` | `sealed`; ctor `(string operationKey, string description)`. `OperationKey`, `Description`, `Result` (default `Deny`). |
| `AgentConfirmationResult` | `enum { Deny, AllowOnce, AllowAlways }` — allow-always is persisted per `operationKey` for the session. |
| `AgentToolCallEventArgs` | ctor `(string toolName, string result, int callCount)`. `ToolName`, `Result`, `CallCount`. |
| `IAgentSelectionNotifier` | `event EventHandler<AgentSelectionEventArgs> SelectionRequested`. |
| `IAgentConfirmationNotifier` | `event EventHandler<AgentConfirmationEventArgs> ConfirmationRequested`. |
| `IAgentToolCallNotifier` | `event EventHandler<AgentToolCallEventArgs> ToolCalled` — implemented by `WorkflowAgentScope` and `AgentObjectToolkit`. |

Tested by `AgentToolCallEventArgsTests`; host dialogs in `Examples/Workflow/WinForms/Demo/Dialogs/AgentSelectionDialog.cs` and `AgentConfirmationDialog.cs`.

## Generic object toolkit (Extension)

### `AgentObjectToolkit`

`public sealed class AgentObjectToolkit(object target, AgentLanguages language = English, ISet<string>? rejectedProperties = null) : IAgentToolCallNotifier`. Wraps any .NET object as MAF tools via the Core utilities above; the non-workflow counterpart to `WorkflowAgentToolkit`.

| Member | Signature | Notes |
|---|---|---|
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | Raised after each tool call. |
| `MaxToolCalls` | `int? { get; set; }` | Tool-call cap; `null` = unlimited. |
| `CreateTools` | `IList<AITool> CreateTools()` | Ten tools: `GetComponentInfo`, `ListProperties`, `GetProperty`, `SetProperty`, `PatchProperties`, `ListCommands`, `ExecuteCommand`, `ListMethods`, `InvokeMethod`, `ResolveType`. |

`AgentObjectToolkitExtensions` (same file): `AgentObjectToolkit AsAgentToolkit(this object target, ...)` and `IList<AITool> AsAgentTools(this object target, ...)`.

### `AgentEmbeddedResources`

`public static class AgentEmbeddedResources` — reads the Markdown prompts embedded in the `VeloxDev.Core.Extension` assembly under `Resources/{System}/{Lang}/Skills|References|Safety/{Name}.md` and `Resources/{System}/Scripts/{Name}`. Falls back to the English variant for a missing localized file.

| Member | Signature |
|---|---|
| `ReadSkill` / `ListSkills` / `ReadAllSkills` | `string?` / `IEnumerable<string>` / `string`, param `(string system, string name, AgentLanguages language = English)` |
| `ReadReference` / `ListReferences` / `ReadAllReferences` | Same shape over the `References/` category |
| `ReadSafety` / `ReadSafetyFiles` | Same shape over the `Safety/` category; `ReadSafetyFiles(system, language, params string[] names)` concatenates in order |
| `ReadScript` / `ListScripts` / `ReadAllScripts` | Same shape over the language-neutral `Scripts/` category |
