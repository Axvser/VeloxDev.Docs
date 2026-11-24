# 上下文作用域

作用域渲染描述工作流类型与宿主注册类型的提示块。这些成员选择语言、注册类型并生成每种提示形状。

## 语言成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithPromptLanguage` | `WorkflowAgentScope WithPromptLanguage(AgentLanguages language)` | 设置每次调用语言参数为 null 时使用的默认语言。在任何 `With*` 注册之前调用。 |
| `WithOutputLanguage` | `WorkflowAgentScope WithOutputLanguage(AgentLanguages language)` | 设置模型应答所用语言。与提示语言无关。 |
| `PromptLanguage` | `AgentLanguages PromptLanguage { get; }` | 生效的提示语言。 |

## 类型注册

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithComponents` | `WorkflowAgentScope WithComponents(Type[] components, AgentLanguages? language = null)` | 注册组件类型；渲染命令、槽与提升属性。 |
| `WithEnums` | `WorkflowAgentScope WithEnums(Type[] enums, AgentLanguages? language = null)` | 注册枚举；渲染成员及含义。 |
| `WithInterfaces` | `WorkflowAgentScope WithInterfaces(Type[] interfaces, AgentLanguages? language = null)` | 注册接口；渲染其契约。 |
| `WithData` | `WorkflowAgentScope WithData(Type[] dataTypes, AgentLanguages? language = null)` | 注册值对象；渲染属性与标注字段，不带操作噪声。 |
| `WithAutoDiscovery` | `WorkflowAgentScope WithAutoDiscovery(AgentLanguages? language = null)` | 注册编译上下文树在 customer 根下承载的每个类型，按四个组件接口分类。框架类型从不作为客户类型注册。 |

没有标注、没有组件接口可达、也没有成员引用的类型不在树中，也不注册。没有反射回退：未注册类型渲染为空。

## 提示形状

| 方法 | 返回 | 说明 |
|---|---|---|
| `ProvideAllContexts()` | `string` | 默认语言的完整上下文。 |
| `ProvideAllContexts(AgentLanguages language)` | `string` | 指定语言的完整上下文。 |
| `ProvideProgressiveContextPrompt()` | `string` | 一段短骨架，告诉模型通过 `GetWorkflowSummary`、`GetComponentContext` 与 `ListComponentCommands` 发现细节。 |
| `ProvideProgressiveContextPrompt(AgentLanguages language)` | `string` | 指定语言的同一骨架。 |
| `ProvideFrameworkContext(AgentLanguages language = AgentLanguages.English)` | `string` | 框架自身的枚举、接口与组件块，读取自树的 `Framework/` 目录。 |
| `ProvideCustomerContext()` | `string` | 开发者注册类型，各自使用注册时的语言。 |
| `ProvideFrameworkDataContext(AgentLanguages language = AgentLanguages.English)` | `string` | 框架数据类型（`Anchor`、`Offset`、`Size`）的全量模式上下文。 |
| `ProvideCustomerDataContext()` | `string` | 开发者注册数据类型的全量模式上下文。 |

`ProvideProgressiveContextPrompt` 刻意比 `ProvideAllContexts` 短得多；每轮 provider 追加会变化的内容。

## 类：AgentContextCollector

`VeloxDev.AI.Workflow.AgentContextCollector` 从编译上下文树渲染单个类型的上下文块。没有反射，也没有回退：树不承载的类型渲染为空字符串。

| 方法 | 返回 | 说明 |
|---|---|---|
| `GetAgentContext(Type type, AgentLanguages language)` | `string[]` | 类型的 `[AgentContext]` 描述，已应用语言回退。 |
| `GetAgentContext(MemberInfo member, AgentLanguages language)` | `string[]` | 成员的 `[AgentContext]` 描述。 |
| `GetEnumContext(Type enumType, AgentLanguages language)` | `string` | 枚举的 Markdown 块，树无条目时为空。 |
| `GetInterfaceContext(Type type, AgentLanguages language)` | `string` | 接口的 Markdown 块，或空。 |
| `GetClassContext(Type type, AgentLanguages language)` | `string` | 组件的 Markdown 块，或空。 |
| `GetDataContext(Type type, AgentLanguages language)` | `string` | 值对象的紧凑块：仅公共属性与 `[AgentContext]` 字段。 |

## 类：AgentContextAttribute

`VeloxDev.AI.AgentContextAttribute` 为类型或成员附加自然语言描述，每种语言一条。可重复，不继承。

```csharp
[AgentContext(AgentLanguages.English, "A node that runs a Python script.")]
[AgentContext(AgentLanguages.Chinese, "运行 Python 脚本的节点。")]
public sealed class ScriptNodeViewModel { }
```

| 成员 | 类型 | 说明 |
|---|---|---|
| 构造函数 | `AgentContextAttribute(AgentLanguages language = AgentLanguages.English, string context = "")` | 一种语言的一条描述。 |
| `Language` | `AgentLanguages` | 描述书写所用语言。 |
| `Context` | `string` | 描述文本。 |

## 枚举：AgentLanguages

`VeloxDev.AI.AgentLanguages : byte` 列出上下文系统可渲染的语言。

| 值 | 名称 | 值 | 名称 |
|---|---|---|---|
| 0 | `English` | 17 | `Thai` |
| 1 | `ChineseSimplified`（别名 `Chinese`） | 18 | `Turkish` |
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

## 类：AgentLanguagesExtensions

| 成员 | 签名 | 说明 |
|---|---|---|
| `AllLanguages` | `static IReadOnlyList<AgentLanguages> AllLanguages { get; }` | 所有已定义语言。 |
| `ToLanguageCode` | `static string ToLanguageCode(this AgentLanguages language)` | 短代码，如 `zh` 或 `en`。 |
| `TryParseLanguageCode` | `static bool TryParseLanguageCode(string languageCode, out AgentLanguages language)` | 不区分大小写解析代码；接受 `zh-cn` 等别名。 |
| `ParseLanguageCode` | `static AgentLanguages ParseLanguageCode(string languageCode)` | 解析代码或抛异常。 |
| `GetDisplayName` | `static string GetDisplayName(this AgentLanguages language)` | 人类可读名称。 |

只有 `en` 与 `zh` 提示文件夹被嵌入；其他语言回退到 `en`。

## 相关

- [技能作用域](../01_技能作用域/index.md) —— 挂载可开关的流程文档。
- [WorkflowAgentScope](../../17_工作流智能体工具/00_工作流作用域/index.md) —— 这些成员扩展的作用域。
