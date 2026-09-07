# 工作流代理 — 命名空间：`VeloxDev.AI`

工作流代理共用的通用（非工作流）AI 管线：用于向 LLM 描述类型/成员的 `[AgentContext]` 特性、`AgentLanguages` 枚举、读取上下文并发现/调用命令、属性与方法的反射工具，以及作用域会触发的事件参数与通知契约。Core 类型实现在 `Src/Core/VeloxDev.Core/AI/`；通用对象工具包与内嵌资源读取器位于 `Src/Core/VeloxDev.Core.Extension/Agent/`。框架无关——适用于任意对象。

**证据：** **测试**（`Src/Core/VeloxDev.Core.Test/AI/*`）。

## 特性

### `AgentContextAttribute`

`public class AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "") : Attribute`。`AttributeUsage(All, Inherited = false, AllowMultiple = true)`。属性 `Language`（`AgentLanguages`）与 `Context`（`string`）。为 Agent 描述任意目标（类型、属性、字段、方法、枚举成员）；同一目标可多个。源：`AgentContextAttribute.cs`。

### `AgentCommandParameterAttribute`

`public class AgentCommandParameterAttribute : Attribute`，ctor `()`（无参数）与 `(Type parameterType)`。`AttributeUsage(Property | Method | Field, AllowMultiple = false)`。属性 `Type? ParameterType`——Agent 调用该命令时应构造的具体 .NET 类型。源：`AgentCommandParameterAttribute.cs`。

### `SlotSelectorsAttribute`

`public sealed class SlotSelectorsAttribute`，ctor `(params Type[])` 与 `(params string[])`（字符串形式为序列化友好，存完全限定类型名）。`AttributeUsage(Property | Field, AllowMultiple = false)`。属性 `Type[] AllowedEnumTypes`、`string[] AllowedEnumTypeNames`。为 `SlotEnumerator<TSlot>` 属性白名单化其选择器类型；由 `ListSlotProperties`/`SetEnumSlotCollection` 读取，`PatchNodeProperties` 会拒绝带 `[SlotSelectors]` 的属性。源：`SlotSelectorsAttribute.cs`。

## AgentLanguages

`public enum AgentLanguages : byte`——`English`、`ChineseSimplified`（别名 `Chinese`）、`ChineseTraditional`、`Japanese`、`Korean`、`French`、`German`、`Spanish`、`Portuguese`、`Russian`、`Arabic`、`Hindi`、`Bengali`、`Urdu`、`Indonesian`、`Malay`、`Vietnamese`、`Thai`、`Turkish`、`Italian`、`Dutch`、`Polish`、`Czech`、`Swedish`、`Danish`、`Norwegian`、`Finnish`、`Greek`、`Hebrew`、`Romanian`、`Hungarian`、`Ukrainian`、`Persian`。

`AgentLanguagesExtensions`（同一文件）：`string ToLanguageCode(this AgentLanguages)`、`bool TryParseLanguageCode(string, out AgentLanguages)`、`AgentLanguages ParseLanguageCode(string)`（不支持的语言代码抛 `ArgumentException`）、`string GetDisplayName(this AgentLanguages)`。由 `AgentLanguagesTests` 覆盖。

## 反射工具（Core）

### `AgentContextReader`

`public static class AgentContextReader`——按语言读取 `[AgentContext]` 值：`string[] GetContexts(Type, AgentLanguages)`、`string[] GetContexts(MemberInfo, AgentLanguages)`、`bool HasAgentContext(MemberInfo)`。由 `AgentContextReaderTests` 覆盖。

### `AgentCommandDiscoverer`

`public static class AgentCommandDiscoverer`——面向任意对象的泛型 `ICommand` 发现/执行。

| 成员 | 签名 | 说明 |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object target, AgentLanguages language = English)` | 先接口命令属性（属性权威），再具体类型属性（去重）。 |
| `Execute` | `ExecuteResult Execute(object target, string commandName, object? parameter = null)` | 执行命名命令；缺 `"Command"` 时补齐。 |
| `CanExecuteCommand` | `bool CanExecuteCommand(object target, string commandName, object? parameter = null)` | 命名命令当前的 `CanExecute`。 |
| `FindBackingCommand` | `string? FindBackingCommand(Type type, string propertyName)` | 寻找 `Set{Name}Command`/`{Name}Command`（属性或接口）。 |

内嵌 `sealed CommandDescriptor`（`Name`、`Type? ParameterType`、`IReadOnlyList<string> AgentDescriptions`、`bool CanExecute`）与 `sealed ExecuteResult`（`CommandName`、`bool Success`、`string? Error`）。由 `AgentCommandDiscovererTests` 覆盖。

### `AgentMethodInvoker`

`public static class AgentMethodInvoker`——反射方法发现/调用。

| 成员 | 签名 | 说明 |
|---|---|---|
| `DiscoverMethods` | `IReadOnlyList<MethodDescriptor> DiscoverMethods(object target, AgentLanguages language = English, bool includeStatic = false, Func<MethodInfo, bool>? filter = null)` | 公开方法，排除属性访问器与 `object` 方法。 |
| `Invoke` | `InvokeResult Invoke(object target, string methodName, params object?[]? args)` | 按参数个数做重载解析；尽力类型转换；补齐可选参数。 |
| `InvokeStatic` | `InvokeResult InvokeStatic(Type type, string methodName, params object?[]? args)` | 静态重载。 |

内嵌 `MethodDescriptor`、`ParameterDescriptor`、`InvokeResult`（`Success`/`ReturnValue`/`Error`）。由 `AgentMethodInvokerTests` 覆盖。

### `AgentPropertyAccessor`

`public static class AgentPropertyAccessor`——泛型属性读写。

| 成员 | 签名 | 说明 |
|---|---|---|
| `DiscoverProperties` | `IReadOnlyList<PropertyDescriptor> DiscoverProperties(object target, AgentLanguages language = English, Func<PropertyInfo, bool>? filter = null, bool includeValues = false)` | 公开实例属性 + `[AgentContext]` 描述。 |
| `GetPropertyValue` | `object? GetPropertyValue(object target, string propertyName)` | 读取属性；缺失/不可读返回 `null`。 |
| `SetPropertyValue` | `SetResult SetPropertyValue(object target, string propertyName, object? value)` | 经 `ConvertValue`（原始类型、`Enum.Parse` 枚举、可空处理）写入。 |
| `SetProperties` | `IReadOnlyList<SetResult> SetProperties(object target, IReadOnlyDictionary<string, object?> properties, ISet<string>? rejected = null)` | 批量写入；被拒绝的名字带错误跳过。 |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target, Func<PropertyInfo, bool>? skip = null)` | 复制可写标量/枚举属性。 |

内嵌 `PropertyDescriptor`、`SetResult`。由 `AgentPropertyAccessorTests` 覆盖。

### `AgentTypeResolver`

`public static class AgentTypeResolver`——`Type? ResolveType(string fullTypeName)`；先经 `Type.GetType`，再扫描所有已加载程序集。由 `AgentTypeResolverTests` 覆盖。

## 事件参数与通知契约

| 类型 | 成员 |
|---|---|
| `AgentSelectionEventArgs` | `sealed`；ctor `(string prompt, string[] options)`。`Prompt`、`Options`（`IReadOnlyList<string>`）、`AllowMultiSelect`（默认 `false`）、`FreeTextPrompt`（默认 `"Custom input (optional)"`）、`SelectedOption`（`string?`）、`SelectedOptions`（`IReadOnlyList<string>?`）、`FreeTextResponse`（`string?`）。 |
| `AgentConfirmationEventArgs` | `sealed`；ctor `(string operationKey, string description)`。`OperationKey`、`Description`、`Result`（默认 `Deny`）。 |
| `AgentConfirmationResult` | `enum { Deny, AllowOnce, AllowAlways }`——allow-always 按 `operationKey` 在会话内记忆。 |
| `AgentToolCallEventArgs` | ctor `(string toolName, string result, int callCount)`。`ToolName`、`Result`、`CallCount`。 |
| `IAgentSelectionNotifier` | `event EventHandler<AgentSelectionEventArgs> SelectionRequested`。 |
| `IAgentConfirmationNotifier` | `event EventHandler<AgentConfirmationEventArgs> ConfirmationRequested`。 |
| `IAgentToolCallNotifier` | `event EventHandler<AgentToolCallEventArgs> ToolCalled`——由 `WorkflowAgentScope` 与 `AgentObjectToolkit` 实现。 |

由 `AgentToolCallEventArgsTests` 覆盖；宿主对话框位于 `Examples/Workflow/WinForms/Demo/Dialogs/AgentSelectionDialog.cs` 与 `AgentConfirmationDialog.cs`。

## 通用对象工具包（Extension）

### `AgentObjectToolkit`

`public sealed class AgentObjectToolkit(object target, AgentLanguages language = English, ISet<string>? rejectedProperties = null) : IAgentToolCallNotifier`。经上述 Core 工具把任意 .NET 对象包装为 MAF 工具；是 `WorkflowAgentToolkit` 的非工作流对应物。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | 每次工具调用后触发。 |
| `MaxToolCalls` | `int? { get; set; }` | 工具调用上限；`null` = 不限制。 |
| `CreateTools` | `IList<AITool> CreateTools()` | 十个工具：`GetComponentInfo`、`ListProperties`、`GetProperty`、`SetProperty`、`PatchProperties`、`ListCommands`、`ExecuteCommand`、`ListMethods`、`InvokeMethod`、`ResolveType`。 |

`AgentObjectToolkitExtensions`（同一文件）：`AgentObjectToolkit AsAgentToolkit(this object target, ...)` 与 `IList<AITool> AsAgentTools(this object target, ...)`。

### `AgentEmbeddedResources`

`public static class AgentEmbeddedResources`——读取内嵌在 `VeloxDev.Core.Extension` 程序集中的 Markdown 提示词，目录为 `Resources/{System}/{Lang}/Skills|References|Safety/{Name}.md` 与 `Resources/{System}/Scripts/{Name}`。本地化文件缺失时回退到英文变体。

| 成员 | 签名 |
|---|---|
| `ReadSkill` / `ListSkills` / `ReadAllSkills` | `string?` / `IEnumerable<string>` / `string`，参数 `(string system, string name, AgentLanguages language = English)` |
| `ReadReference` / `ListReferences` / `ReadAllReferences` | 同构，作用于 `References/` 类别 |
| `ReadSafety` / `ReadSafetyFiles` | 同构，作用于 `Safety/` 类别；`ReadSafetyFiles(system, language, params string[] names)` 依序拼接 |
| `ReadScript` / `ListScripts` / `ReadAllScripts` | 同构，作用于语言无关的 `Scripts/` 类别 |
