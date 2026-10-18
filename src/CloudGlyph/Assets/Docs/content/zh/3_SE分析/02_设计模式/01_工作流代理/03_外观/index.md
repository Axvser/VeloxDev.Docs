# 工作流代理 —— 设计模式 —— 外观

`WorkflowAgentToolkit` 是 workflow-agent 特性的外观。一次 `CreateTools()` 调用注册某个作用域树的全部内置 `AITool`（66 个无条件 + 至多四个条件交互/计划工具 + `ResetToolCallLimit`），把类型解析、基于反射的命令调用、JSON 序列化与完成等待隐藏在 LLM 看到的扁平工具名之后。

`CreateTools` 用本地 `T(...)` 辅助包装每个工具体，并按 `WorkflowToolCategory` 标志分组注册，让宿主可以收缩暴露表面：

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，`CreateAllTools`

```csharp
AITool T(Delegate method, string name, AgentActionCategory action)
    => new TrackedAIFunction(AIFunctionFactory.Create(method, name), Tools, _scope.Pipeline, action);

var tools = new List<AITool>();
void Add(WorkflowToolCategory category, params AITool[] items)
{
    if ((categories & category) == category)
        tools.AddRange(items);
}
```

每个类别块注册自己的工具，例如 Query 块以 `Add(WorkflowToolCategory.Query, T(ListNodes, nameof(ListNodes), AgentActionCategory.Read), ... )` 开始 —— 完整列表从 `ListNodes` 到 `GetExecutionLog`。

外观是 agent 宿主使用的唯一公开入口：`scope.ProvideTools()` → `CreateToolkit().CreateTools()`。开发者注册的自定义工具（经 `WithTools` / `WithQueryTools`）在最后并入；当它们是 `AIFunction` 时用同一 `TrackedAIFunction` 装饰器包装，原始 MCP 客户端工具按原样追加。
