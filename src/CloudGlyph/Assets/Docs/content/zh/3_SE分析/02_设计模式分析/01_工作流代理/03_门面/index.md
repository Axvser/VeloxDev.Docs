# Workflow Agent — 设计模式 — 门面

`CreateTools()` 用局部 `T(...)` 帮助方法构建每个工具，把 `AIFunctionFactory.Create(method, name)` 包装进 `TrackedAIFunction`。分组注册由 `WorkflowToolCategory` 旗标驱动。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，第 39-161 行

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
