# 02 · 构建作用域

作用域是把一棵 workflow 树绑定到一份 agent 配置的对象。每个 `With*` 调用都返回同一作用域，因此整份配置就是一条链。

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Workflow;

WorkflowAgentScope scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)     // 提示 / [AgentContext] 文档的语言
    .WithOutputLanguage(AgentLanguages.Chinese)     // 模型必须用哪种语言回答
    .WithAutoDiscovery()                            // 注册编译上下文树携带的类型
    .WithMaxToolCalls(200)
    .WithAllowNodeExecution(true)
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithAutoMarkDirty(false);
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

**预期结果：** `scope` 构造成功、不抛异常。构造作用域从不触网、不接触模型 —— 它只记录配置。

## 1. 入口

| 成员 | 签名 | 说明 |
|---|---|---|
| `AgentEx.AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | 唯一入口 —— 没有树就无法使用作用域。 |

## 2. 语言、发现、预算

| 成员 | 签名 | 作用 |
|---|---|---|
| `WithPromptLanguage` | `WithPromptLanguage(AgentLanguages language)` | 当逐次调用的 `language` 为 `null` 时，提示与 `[AgentContext]` 文档的全局默认语言。先调用它；它也会传播到已挂载的 `SkillScope`。 |
| `WithOutputLanguage` | `WithOutputLanguage(AgentLanguages language)` | LLM 必须用哪种语言回复（独立于提示语言）。 |
| `WithAutoDiscovery` | `WithAutoDiscovery(AgentLanguages? language = null)` | 注册编译上下文树 `Customer/` 根下的每个类型条目 —— 组件（按四个组件接口分组）、枚举、接口与数据。**运行时不做任何扫描**；见 §3。 |
| `WithEnums` / `WithInterfaces` / `WithComponents` / `WithData` | `(Type[] …, AgentLanguages? language = null)` | 显式注册类型，而不是扫描。 |
| `WithMaxToolCalls` | `WithMaxToolCalls(int maxCalls)` | 累计工具调用上限。 |
| `WithMaxReadToolCalls` | `WithMaxReadToolCalls(int maxCalls)` | 只读（查询）调用的独立上限。 |
| `WithMaxWriteToolCalls` | `WithMaxWriteToolCalls(int maxCalls)` | 变更（非查询）调用的独立上限。 |

`AgentLanguages` 是一个 `byte` 枚举，共 33 个成员（`English = 0`、`ChineseSimplified = 1` 及其别名 `Chinese`、…、`Persian = 32`），另有 `AgentLanguagesExtensions`（`ToLanguageCode`、`TryParseLanguageCode`、`ParseLanguageCode`、`GetDisplayName`）。

## 3. 类型发现细节

上下文树由源码生成器**在编译期**遍历编译构建，因此 `WithAutoDiscovery` 只是若干目录列举，而不是运行时扫描：

| `Customer/` 下的目录 | 内容 |
|---|---|
| `Enums` | 生成器收录的枚举类型 |
| `Interfaces` | 被成员类型使用的接口 |
| `Data` | 数据类型 —— 带 `[AgentContext]` 的类与结构体，以及被已列类型成员以声明类型暴露的普通类 |
| `Components/{kind}` | 四个组件种类，按 `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` 分组 |

**注册的就是生成器收录的。** 没有任何标注、没有组件接口可达、也没有成员引用的类型不在树中，也不会在这里注册 —— 对它没有可渲染的上下文。框架类型位于 `Framework/`，这里只读 `Customer/`。

来源：`WorkflowAgentScope.cs`（`WithAutoDiscovery`）；数据扩宽的收录规则在 `AIContextModel.cs`。

**预期结果：** 调用 `WithAutoDiscovery()` 后，作用域持有编译树的客户类型注册；请求一个生成器从未收录的类型不会得到上下文块。

## 4. 提示提供器

| 成员 | 签名 | 作用 |
|---|---|---|
| `ProvideProgressiveContextPrompt` | `string ProvideProgressiveContextPrompt()` / `(AgentLanguages)` | 精简系统提示。 |
| `ProvideAllContexts` | `string ProvideAllContexts()` / `(AgentLanguages)` | 完整自包含提示。 |
| `ProvideFrameworkContext` | `string ProvideFrameworkContext(AgentLanguages language = English)` | 内置枚举/接口/组件的上下文块。 |
| `ProvideCustomerContext` | `string ProvideCustomerContext()` | 已注册客户类型的上下文块，各自使用注册时的语言。 |
| `ProvideFrameworkDataContext` | `string ProvideFrameworkDataContext(AgentLanguages language = English)` | `Framework/Data` 下内置数据类型（如 `Anchor`、`Offset`、`Size`）的数据块。 |
| `ProvideCustomerDataContext` | `string ProvideCustomerDataContext()` | 已注册客户数据类型的数据块，各自使用注册时的语言。 |

`ProvideProgressiveContextPrompt` 让初始提示保持精简：行为约束、失败处理协议、内置参考、带一行摘要的注册类型清单、自定义工具、权限策略、技能与输出语言指令。完整的属性/命令表**不会**预加载 —— 模型被告知在操作某类型前先用完整类型名调用 `GetComponentContext`。

```csharp
var skeleton = scope.ProvideProgressiveContextPrompt();   // 静态骨架 —— 冻结进 ChatOptions.Instructions
var providers = scope.CreateContextProviders();           // 每轮：能力包络 + 技能 + MCP + 子代理 + 框架
```

**预期结果：** `skeleton` 是非空 markdown 字符串，包含权限策略小节；`providers` 至少包含一个 `WorkflowAgentContextProvider`。

## 5. 工具产出

| 成员 | 签名 | 作用 |
|---|---|---|
| `CreateToolkit` | `WorkflowAgentToolkit CreateToolkit()` | 本作用域的工具包（每个作用域缓存一个实例）。 |
| `ProvideTools` | `IList<AITool> ProvideTools()` | 全部工具，遵守逐工具开关。 |
| `ProvideTools` | `IList<AITool> ProvideTools(WorkflowToolCategory categories)` | 限制到给定类别标志。 |

经 `WithTools` / `WithQueryTools` 注册的自定义工具始终包含，不受类别标志影响。工具被关闭后的行为见「工具预算与宿主策略」页。

**预期结果：** 对启用了节点执行、且两个交互处理器都已注册的作用域，`scope.ProvideTools().Count` 为 `71` —— 66 个无条件分类工具，加 `RequestSelection` / `RequestConfirmation` / `EnterPlanMode` / `ExitPlanMode`，加 `ResetToolCallLimit`（逐类别明细见第 06 页）。`Execution` 与 `Command` 闸门在每个工具体内检查，因此不会从计数中移除工具；没有处理器时数量只少掉这些条件工具。

## 运行声明

- ⚠️ 未实际运行 —— 仅静态核验（2026-10-18）。签名与上下文树发现行为读自 `WorkflowAgentScope.cs` 与 `AgentHelper.cs`；未从本页构造任何作用域。
