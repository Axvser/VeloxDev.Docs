# Workflow Agent — 设计模式 — 门面

`WorkflowAgentToolkit` 是工作流代理功能的门面。一次 `CreateTools()` 调用即可为一棵受限树注册全部约 60 个 `AITool`，把类型解析、基于反射的命令调用、JSON 序列化与完成等待全部隐藏在一个 LLM 眼中是扁平工具名的单一表面之后。

`CreateTools` 用局部 `T(...)` 帮助方法包装每个工具体，并按 `WorkflowToolCategory` 旗标分组注册，使宿主可以收缩暴露的表面：

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，第 39-164 行

```csharp
AITool T(Delegate method, string name)
    => new TrackedAIFunction(AIFunctionFactory.Create(method, name), this);

var tools = new List<AITool>();
void Add(WorkflowToolCategory category, params AITool[] items)
{
    if ((categories & category) == category)
        tools.AddRange(items);
}
```

每个类别块注册其工具，例如查询块以 `Add(WorkflowToolCategory.Query, T(ListNodes, nameof(ListNodes)), T(GetNodeDetail, nameof(GetNodeDetail)), ... )` 开头——完整列表从 `ListNodes` 一直到 `GetExecutionLog`。

门面是 agent 宿主使用的唯一公开入口：`scope.ProvideTools()` → `CreateToolkit().CreateTools()`。开发者注册的自定义工具（经 `WithTools` / `WithQueryTools`）在末尾并入；当它们是 `AIFunction` 时同样包上 `TrackedAIFunction` 装饰器，原始 MCP 客户端工具则原样追加（`WorkflowAgentToolkit.cs`，第 154-164 行）。
