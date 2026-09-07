# 工作流代理 — 构建作用域

`WorkflowAgentScope` 是把一棵树变成代理可控表面的流式配置对象。代理能检查、触碰或运行的一切都在这里决定：语言、类型发现、预算、门禁、处理器与自定义工具。

## 1. 创建作用域

`tree.AsAgentScope()`（扩展方法声明于 `VeloxDev.AI.Workflow`，文件 `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`）返回一个全新的构建器。从语言与自动发现开始：

```csharp
var scope = tree.AsAgentScope()                  // tree: IWorkflowTreeViewModel
    .WithPromptLanguage(AgentLanguages.English)  // 提示词与文档的默认语言
    .WithOutputLanguage(AgentLanguages.Chinese)  // LLM 回复必须使用的语言
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib");
```

- `WithPromptLanguage(language)` 设置所有内置提示词/文档段使用的语言。它有全局默认值（`English`）；请把它放在最前，先于其它依赖它的注册。
- `WithOutputLanguage(language)` 发出模型回复时必须遵循的「输出语言」指令。它与提示词文档语言相互独立 —— 你可以用英文写文档、要求中文回复，正如演示所做。
- `WithAutoDiscovery(Assembly)` / `WithAutoDiscovery(assemblyName)` 对单个程序集做两遍扫描：先注册具体工作流组件类、带 `[AgentContext]` 的枚举与数据类；再深度扫描这些组件的属性/字段/方法，推断被引用的枚举、接口与数据（经 `[SlotSelectors]`、`[AgentCommandParameter]`、成员与泛型类型）。框架内建类型绝不会被重复加入。字符串重载在当前 `AppDomain` 中按简单名解析程序集。

若你更想要显式控制，可以按语言精确注册所需类型：`WithEnums(Type[], AgentLanguages?)`、`WithInterfaces(Type[], ...)`、`WithComponents(Type[], ...)` 与 `WithData(Type[], ...)` —— 自动发现只是这四者的语法糖。

**预期结果：** `scope` 无异常构建；其 `Tree` 属性等于 `tree`。

## 2. 生成系统提示词（自动读取双语文档）

作用域提供两个提示词提供器；两者都会内嵌随包分发在 `Src/Core/VeloxDev.Core.Extension/Resources/Workflow/{en,zh}` 下的提示词文档（`References/`、`Skills/`、`Safety/`），按当前提示词语言选取并以英文兜底：

```csharp
var progressive = scope.ProvideProgressiveContextPrompt();   // 精简、惰性
var allContexts = scope.ProvideAllContexts();                // 完整、自包含
```

- **渐进式**（`ProvideProgressiveContextPrompt()`）— 硬编码的行为约束、失败处理协议、全部 `References`，然后是一份紧凑的**类型注册表**（框架接口/基类/数据 + 每个已注册客户枚举/接口/组件/数据的全名）以及取自 `[AgentContext]` 的**一行摘要**。它指示模型按需用 `GetComponentContext` / `GetWorkflowSummary` / `ListComponentCommands` 获取完整属性/命令表。初始 token 成本低。
- **全部上下文**（`ProvideAllContexts()`）— 内容相同，但把整套框架与客户**表内联**进去（无需惰性获取）。自包含但 token 成本高。

无论选哪种，内嵌文档都会教会代理它必须遵守的规则 —— 例如 `Skills/CompilerUsage.md`（三种执行入口、Root 与 Terminal、绝不绕过路由器）、`Skills/OperationOrdering.md`（必须先 create → patch → connect → execute）、`References/CommandReference.md`（命令优先的变更规则）、`References/CoordinateSystem.md`（画布坐标），以及 `Safety/` 的分级策略。

**预期结果：** 两个调用都返回非空字符串；渐进式提示词的类型注册表段会列出你发现的类型全名及其 `[AgentContext]` 摘要。

## 3. 获取工具集

```csharp
var toolkit = scope.CreateToolkit();                         // WorkflowAgentToolkit
var allTools = scope.ProvideTools();                         // IList<AITool>，全部分类
var queryOnly = scope.ProvideTools(WorkflowToolCategory.Query); // 过滤后的表面
```

- `CreateToolkit()` 返回 `WorkflowAgentToolkit`（命名空间 `VeloxDev.AI.Workflow.Functions`），它持有树跟踪器与逐调用计数器。
- `ProvideTools()` 返回全部内置工具（默认 60 个；开启交互安全并注册处理器后最多 62 个）**外加**你用 `WithTools` / `WithQueryTools` 注册的自定义工具。
- `ProvideTools(WorkflowToolCategory)` 只返回指定分类 —— 例如 `Query` 只给你只读检查与编译计划工具，不含任何变更表面。

`WorkflowToolCategory` 与 `WorkflowAgentToolkit` 位于命名空间 `VeloxDev.AI.Workflow.Functions` —— 当你显式引用分类枚举或工具包类型时需要 `using VeloxDev.AI.Workflow.Functions;`（单独调用 `ProvideTools()` 不需要，因为它返回 `IList<AITool>`）。

**预期结果：** `ProvideTools()` 是非空的 `IList<AITool>`；`ProvideTools(WorkflowToolCategory.Query)` 中不包含变更、执行或命令工具。

## 运行声明

- ⚠️ 仅静态核验 —— 签名对照 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs` 与 `AgentEx.cs` 验证；示例未编译或运行。
