# 02 · 构建作用域

作用域是把一棵 workflow 树绑定到一套 agent 配置的对象。每个 `With*` 调用都返回同一个作用域，因此整套配置就是一条链。

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Workflow;

WorkflowAgentScope scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)     // 提示 / [AgentContext] 文档的语言
    .WithOutputLanguage(AgentLanguages.Chinese)     // 模型必须使用的回答语言
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithAutoMarkDirty(false);
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

**预期结果：** `scope` 构造成功、不抛异常。构建作用域从不触网、不调用模型 —— 它只记录配置。

## 1. 入口

| 成员 | 签名 | 说明 |
|---|---|---|
| `AgentEx.AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | 唯一入口 —— 没有树就无法使用作用域。 |

## 2. 语言、发现、预算

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | 当每次调用的 `language` 为 `null` 时，提示与 `[AgentContext]` 文档的全局默认语言。应先调用；它也会传播到已挂载的 `SkillScope`。 |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` | LLM 必须回答所用的语言（与提示语言无关）。 |
| `WithAutoDiscovery` | `WithAutoDiscovery(Assembly assembly, AgentLanguages? language = null)` | 对一个程序集做两趟扫描。 |
| `WithAutoDiscovery` | `WithAutoDiscovery(string assemblyName, AgentLanguages? language = null)` | 同上，按简单程序集名；程序集未加载时抛 `ArgumentException`。 |
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `(Type[] …, AgentLanguages? language = null)` | 显式注册类型，而不是扫描。 |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` | 累计工具调用上限。 |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` | 只读（查询）调用的独立上限。 |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` | 变更（非查询）调用的独立上限。 |

`AgentLanguages` 是一个 `byte` 枚举，含 33 个成员（`English = 0`、`ChineseSimplified = 1`（别名 `Chinese`）…… `Persian = 32`），另有 `AgentLanguagesExtensions`（`ToLanguageCode`、`TryParseLanguageCode`、`ParseLanguageCode`、`GetDisplayName`）。

## 3. 类型发现的细节

`WithAutoDiscovery` 跑两趟：

1. **第 1 趟 —— 程序集扫描。** 枚举程序集中的每个类型，注册具体 workflow 组件（`IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel`）、带 `[AgentContext]` 的枚举，以及带 `[AgentContext]` 的数据类/结构体。
2. **第 2 趟 —— 深度成员扫描。** 对每个已注册组件，反射其公开属性、后备字段与方法，按语言推断 —— 枚举类型（经 `[SlotSelectors]` 与成员类型）、用作成员类型的接口、`[AgentCommandParameter]` 的参数类型，以及非基元值对象结构体。

框架命名空间的类型（`System*`、`Microsoft*`、`VeloxDev.WorkflowSystem`、`VeloxDev.MVVM`、`VeloxDev.Core.WorkflowSystem`，外加 `FrameworkEnums` / `FrameworkInterfaces` / `FrameworkComponents` / `FrameworkData` 白名单）永不重复添加。一个全局 `HashSet` 保证每个类型跨所有语言只被深扫一次。

**预期结果：** 两次 `WithAutoDiscovery` 后，作用域持有两个程序集注册的并集；询问一个你从未注册的程序集中的类型，得不到任何上下文块。

## 4. 提示提供器

| 成员 | 签名 | 作用 |
|---|---|---|
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | 精简系统提示。 |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `(AgentLanguages)` | 完整自包含提示。 |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages = English)` | 内置枚举/接口/组件的上下文块。 |
| `ProvideCustomerContext` | `string ProvideCustomerContext(AgentLanguages = English)` | 已注册客户类型的上下文块。 |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages = English)` | `Anchor`、`Offset`、`Size`、`IAccessContext`、`ITaskContext`、`TaskContext`、`ICompileContext`、`IRuntimeContext` 的数据块。 |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext(AgentLanguages = English)` | 已注册客户数据类型的数据块。 |

`ProvideProgressiveContextPrompt` 让初始提示保持精简：行为约束、失败处理协议、内置参考、带一行摘要的已注册类型清单、自定义工具、交互安全策略、技能与输出语言指令。完整的属性/命令表**不**预载 —— 模型被告知在操作某类型前先用完整类型名调用 `GetComponentContext`。

```csharp
var skeleton = scope.ProvideProgressiveContextPrompt();   // 静态骨架 —— 冻进 ChatOptions.Instructions
var providers = scope.CreateContextProviders();           // 每轮：能力包络 + 技能 + MCP + 子代理 + 框架
```

**预期结果：** `skeleton` 是非空 markdown 字符串，含「Interaction Safety Policy」小节；`providers` 至少包含一个 `WorkflowAgentContextProvider`。

## 5. 工具产出

| 成员 | 签名 | 作用 |
|---|---|---|
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | 本作用域的工具包（每个作用域缓存一个实例）。 |
| `ProvideTools` | `IList<AITool> ProvideTools()` | 全部工具，遵守逐工具开关。 |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | 按类别位标志限制。 |

经 `WithTools` / `WithQueryTools` 注册的自定义工具始终包含，与类别标志无关。工具被关闭时的行为见「工具预算与宿主策略」页。

**预期结果：** 对于启用了节点执行并注册了两个交互处理器的作用域，`scope.ProvideTools().Count` 为 `69` —— 即 68 个内置工具加上始终追加的 `ResetToolCallLimit`（精确的按类别拆分见第 06 页）。`Execution` 与 `Command` 的闸门在每个工具体内检查，因此不会从计数中移除工具；没有交互处理器时会少去 `Interaction` 的那些工具。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验。签名与两趟发现行为读自 `WorkflowAgentScope.cs` 与 `AgentHelper.cs`；未从本页构造任何作用域。
