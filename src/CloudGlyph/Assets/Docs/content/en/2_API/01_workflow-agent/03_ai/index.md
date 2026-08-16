# Workflow Agent — Namespace: `VeloxDev.AI`

### Attributes

#### `AgentContextAttribute`

**Signature:** `public class AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "") : Attribute`
**Attributes:** `AttributeUsage(AttributeTargets.All, Inherited = false, AllowMultiple = true)`.
**Properties:** `Language` (`AgentLanguages`), `Context` (`string`).
**Notes:** documents any target (type, property, field, method, enum member) for the Agent. Multiple allowed per target. Source: `Src/Core/VeloxDev.Core/AI/AgentContextAttribute.cs`.

#### `AgentCommandParameterAttribute`

**Signature:** `public class AgentCommandParameterAttribute : Attribute` with ctors `() ` (ParameterType null) and `(Type parameterType)`.
**Attributes:** `Property | Method | Field`, `AllowMultiple = false`.
**Property:** `Type? ParameterType` — the concrete .NET type the Agent should construct when invoking the command.
**Source:** `Src/Core/VeloxDev.Core/AI/AgentCommandParameterAttribute.cs`.

#### `SlotSelectorsAttribute`

**Signature:** `public sealed class SlotSelectorsAttribute` with ctors `(params Type[])` and `(params string[])`.
**Attributes:** `Property | Field`, `AllowMultiple = false`.
**Properties:** `Type[] AllowedEnumTypes`, `string[] AllowedEnumTypeNames`.
**Notes:** whitelists the selector types of a `SlotEnumerator<TSlot>` property. Read by `ListSlotProperties` and enforced by `SetEnumSlotCollection`; `PatchNodeProperties` rejects `[SlotSelectors]`-marked properties. Source: `Src/Core/VeloxDev.Core/AI/SlotSelectorsAttribute.cs`.

### `AgentLanguages`

**Signature:** `public enum AgentLanguages : byte` — 33 values: `English`, `ChineseSimplified` (alias `Chinese`), `ChineseTraditional`, `Japanese`, `Korean`, `French`, `German`, `Spanish`, `Portuguese`, `Russian`, `Arabic`, `Hindi`, `Bengali`, `Urdu`, `Indonesian`, `Malay`, `Vietnamese`, `Thai`, `Turkish`, `Italian`, `Dutch`, `Polish`, `Czech`, `Swedish`, `Danish`, `Norwegian`, `Finnish`, `Greek`, `Hebrew`, `Romanian`, `Hungarian`, `Ukrainian`, `Persian`.
**Extensions** (`AgentLanguagesExtensions`): `ToLanguageCode()`, `TryParseLanguageCode(string, out AgentLanguages)`, `ParseLanguageCode(string)`, `GetDisplayName()`.
**Example:** `AgentLanguagesTests`.
**Source:** `Src/Core/VeloxDev.Core/AI/AgentLanguages.cs`.

### Reflection utilities

#### `AgentContextReader`

**Signature:** `public static class AgentContextReader` — `string[] GetContexts(Type, AgentLanguages)`, `string[] GetContexts(MemberInfo, AgentLanguages)`, `bool HasAgentContext(MemberInfo)`.
**Notes:** reads `[AgentContext]` values for a type/member and language.
**Example:** `AgentContextReaderTests`.

#### `AgentCommandDiscoverer`

**Signature:** `public static class AgentCommandDiscoverer` — `IReadOnlyList<CommandDescriptor> DiscoverCommands(object target, AgentLanguages language = English)`, `ExecuteResult Execute(object target, string commandName, object? parameter = null)`, `bool CanExecuteCommand(object target, string commandName, object? parameter = null)`, `string? FindBackingCommand(Type type, string propertyName)`.
**Types:** `CommandDescriptor` (`Name`, `ParameterType`, `AgentDescriptions`, `CanExecute`); `ExecuteResult` (`CommandName`, `Success`, `Error`).
**Notes:** discovers `ICommand`-typed properties (interfaces first — authoritative attributes) and executes them; command-name suffix normalized (appends `"Command"` if missing).
**Example:** `AgentCommandDiscovererTests`.

#### `AgentMethodInvoker`

**Signature:** `public static class AgentMethodInvoker` — `IReadOnlyList<MethodDescriptor> DiscoverMethods(object target, AgentLanguages language = English, bool includeStatic = false, Func<MethodInfo, bool>? filter = null)`, `InvokeResult Invoke(object target, string methodName, params object?[]? args)`, `InvokeResult InvokeStatic(Type type, string methodName, params object?[]? args)`.
**Types:** `MethodDescriptor`, `ParameterDescriptor`, `InvokeResult`.
**Notes:** reflection-based method discovery/invocation with overload resolution by parameter count and best-effort type conversion.
**Example:** `AgentMethodInvokerTests`.

#### `AgentPropertyAccessor`

**Signature:** `public static class AgentPropertyAccessor` — `IReadOnlyList<PropertyDescriptor> DiscoverProperties(object target, AgentLanguages language = English, Func<PropertyInfo, bool>? filter = null, bool includeValues = false)`, `object? GetPropertyValue(object target, string propertyName)`, `SetResult SetPropertyValue(object target, string propertyName, object? value)`, `IReadOnlyList<SetResult> SetProperties(object target, IReadOnlyDictionary<string, object?> properties, ISet<string>? rejected = null)`, `void CopyScalarProperties(object source, object target, Func<PropertyInfo, bool>? skip = null)`.
**Types:** `PropertyDescriptor`, `SetResult`.
**Notes:** generic reflection read/write; `ConvertValue` handles primitives and enums (string → `Enum.Parse`).
**Example:** `AgentPropertyAccessorTests`.

#### `AgentTypeResolver`

**Signature:** `public static class AgentTypeResolver` — `Type? ResolveType(string fullTypeName)`.
**Notes:** resolves a type by full name, first via `Type.GetType`, then by scanning all loaded assemblies.
**Example:** `AgentTypeResolverTests`.

### Event args and notifier interfaces

| Type | Members |
|---|---|
| `AgentSelectionEventArgs` | ctor `(string prompt, string[] options)`; `Prompt`, `Options`, `AllowMultiSelect`, `FreeTextPrompt` (default `"自定义输入（可选）"`), `SelectedOption`, `SelectedOptions`, `FreeTextResponse`. |
| `AgentConfirmationEventArgs` | ctor `(string operationKey, string description)`; `OperationKey`, `Description`, `Result` (default `Deny`). |
| `AgentConfirmationResult` | enum `Deny`, `AllowOnce`, `AllowAlways`. |
| `AgentToolCallEventArgs` | ctor `(string toolName, string result, int callCount)`; `ToolName`, `Result`, `CallCount`. |
| `IAgentSelectionNotifier` | `event EventHandler<AgentSelectionEventArgs> SelectionRequested`. |
| `IAgentConfirmationNotifier` | `event EventHandler<AgentConfirmationEventArgs> ConfirmationRequested`. |
| `IAgentToolCallNotifier` | `event EventHandler<AgentToolCallEventArgs> ToolCalled` (implemented by `WorkflowAgentScope`). |

**Example:** `AgentToolCallEventArgsTests`; dialogs `Examples/Workflow/WinForms/Demo/Dialogs/AgentSelectionDialog.cs` and `AgentConfirmationDialog.cs`.
**Source:** `Src/Core/VeloxDev.Core/AI/*.cs`.
