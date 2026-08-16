# Workflow Agent — 命名空间：`VeloxDev.AI`

### 属性

#### `AgentContextAttribute`

**签名：** `public class AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "") : Attribute`
**特性：** `AttributeUsage(AttributeTargets.All, Inherited = false, AllowMultiple = true)`。
**属性：** `Language`（`AgentLanguages`）、`Context`（`string`）。
**说明：** 为 Agent 描述任意目标（类型、属性、字段、方法、枚举成员）。同一目标可多段。源码：`Src/Core/VeloxDev.Core/AI/AgentContextAttribute.cs`。

#### `AgentCommandParameterAttribute`

**签名：** `public class AgentCommandParameterAttribute : Attribute`，构造 `()`（ParameterType 为 null）与 `(Type parameterType)`。
**特性：** `Property | Method | Field`，`AllowMultiple = false`。
**属性：** `Type? ParameterType` —— Agent 调用命令时应构造的具体 .NET 类型。
**源码：** `Src/Core/VeloxDev.Core/AI/AgentCommandParameterAttribute.cs`。

#### `SlotSelectorsAttribute`

**签名：** `public sealed class SlotSelectorsAttribute`，构造 `(params Type[])` 与 `(params string[])`。
**特性：** `Property | Field`，`AllowMultiple = false`。
**属性：** `Type[] AllowedEnumTypes`、`string[] AllowedEnumTypeNames`。
**说明：** 白名单某 `SlotEnumerator<TSlot>` 属性的选择器类型。由 `ListSlotProperties` 读取、`SetEnumSlotCollection` 强制；`PatchNodeProperties` 拒绝带 `[SlotSelectors]` 的属性。源码：`Src/Core/VeloxDev.Core/AI/SlotSelectorsAttribute.cs`。

### `AgentLanguages`

**签名：** `public enum AgentLanguages : byte` —— 33 个值：`English`、`ChineseSimplified`（别名 `Chinese`）、`ChineseTraditional`、`Japanese`、`Korean`、`French`、`German`、`Spanish`、`Portuguese`、`Russian`、`Arabic`、`Hindi`、`Bengali`、`Urdu`、`Indonesian`、`Malay`、`Vietnamese`、`Thai`、`Turkish`、`Italian`、`Dutch`、`Polish`、`Czech`、`Swedish`、`Danish`、`Norwegian`、`Finnish`、`Greek`、`Hebrew`、`Romanian`、`Hungarian`、`Ukrainian`、`Persian`。
**扩展**（`AgentLanguagesExtensions`）：`ToLanguageCode()`、`TryParseLanguageCode(string, out AgentLanguages)`、`ParseLanguageCode(string)`、`GetDisplayName()`。
**示例：** `AgentLanguagesTests`。
**源码：** `Src/Core/VeloxDev.Core/AI/AgentLanguages.cs`。

### 反射工具

#### `AgentContextReader`

**签名：** `public static class AgentContextReader` —— `string[] GetContexts(Type, AgentLanguages)`、`string[] GetContexts(MemberInfo, AgentLanguages)`、`bool HasAgentContext(MemberInfo)`。
**说明：** 读取某类型/成员/语言的 `[AgentContext]` 值。
**示例：** `AgentContextReaderTests`。

#### `AgentCommandDiscoverer`

**签名：** `public static class AgentCommandDiscoverer` —— `IReadOnlyList<CommandDescriptor> DiscoverCommands(object target, AgentLanguages language = English)`、`ExecuteResult Execute(object target, string commandName, object? parameter = null)`、`bool CanExecuteCommand(object target, string commandName, object? parameter = null)`、`string? FindBackingCommand(Type type, string propertyName)`。
**类型：** `CommandDescriptor`（`Name`、`ParameterType`、`AgentDescriptions`、`CanExecute`）；`ExecuteResult`（`CommandName`、`Success`、`Error`）。
**说明：** 发现并执行 `ICommand` 类型属性（接口优先 —— 属性权威）；命令名规范化（缺 `"Command"` 时补上）。
**示例：** `AgentCommandDiscovererTests`。

#### `AgentMethodInvoker`

**签名：** `public static class AgentMethodInvoker` —— `IReadOnlyList<MethodDescriptor> DiscoverMethods(object target, AgentLanguages language = English, bool includeStatic = false, Func<MethodInfo, bool>? filter = null)`、`InvokeResult Invoke(object target, string methodName, params object?[]? args)`、`InvokeResult InvokeStatic(Type type, string methodName, params object?[]? args)`。
**类型：** `MethodDescriptor`、`ParameterDescriptor`、`InvokeResult`。
**说明：** 基于反射的方法发现/调用，按参数个数解析重载并尽力做类型转换。
**示例：** `AgentMethodInvokerTests`。

#### `AgentPropertyAccessor`

**签名：** `public static class AgentPropertyAccessor` —— `IReadOnlyList<PropertyDescriptor> DiscoverProperties(object target, AgentLanguages language = English, Func<PropertyInfo, bool>? filter = null, bool includeValues = false)`、`object? GetPropertyValue(object target, string propertyName)`、`SetResult SetPropertyValue(object target, string propertyName, object? value)`、`IReadOnlyList<SetResult> SetProperties(object target, IReadOnlyDictionary<string, object?> properties, ISet<string>? rejected = null)`、`void CopyScalarProperties(object source, object target, Func<PropertyInfo, bool>? skip = null)`。
**类型：** `PropertyDescriptor`、`SetResult`。
**说明：** 通用反射读/写；`ConvertValue` 处理基元与枚举（string → `Enum.Parse`）。
**示例：** `AgentPropertyAccessorTests`。

#### `AgentTypeResolver`

**签名：** `public static class AgentTypeResolver` —— `Type? ResolveType(string fullTypeName)`。
**说明：** 先经 `Type.GetType` 解析类型，失败则扫描所有已加载程序集。
**示例：** `AgentTypeResolverTests`。

### 事件参数与通知接口

| 类型 | 成员 |
|---|---|
| `AgentSelectionEventArgs` | 构造 `(string prompt, string[] options)`；`Prompt`、`Options`、`AllowMultiSelect`、`FreeTextPrompt`（默认 `"自定义输入（可选）"`）、`SelectedOption`、`SelectedOptions`、`FreeTextResponse`。 |
| `AgentConfirmationEventArgs` | 构造 `(string operationKey, string description)`；`OperationKey`、`Description`、`Result`（默认 `Deny`）。 |
| `AgentConfirmationResult` | 枚举 `Deny`、`AllowOnce`、`AllowAlways`。 |
| `AgentToolCallEventArgs` | 构造 `(string toolName, string result, int callCount)`；`ToolName`、`Result`、`CallCount`。 |
| `IAgentSelectionNotifier` | `event EventHandler<AgentSelectionEventArgs> SelectionRequested`。 |
| `IAgentConfirmationNotifier` | `event EventHandler<AgentConfirmationEventArgs> ConfirmationRequested`。 |
| `IAgentToolCallNotifier` | `event EventHandler<AgentToolCallEventArgs> ToolCalled`（由 `WorkflowAgentScope` 实现）。 |

**示例：** `AgentToolCallEventArgsTests`；对话框 `Examples/Workflow/WinForms/Demo/Dialogs/AgentSelectionDialog.cs` 与 `AgentConfirmationDialog.cs`。
**源码：** `Src/Core/VeloxDev.Core/AI/*.cs`。
