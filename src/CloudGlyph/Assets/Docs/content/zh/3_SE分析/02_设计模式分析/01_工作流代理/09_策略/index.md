# Workflow Agent — 设计模式 — 策略

`WorkflowToolCategory` 旗标让宿主缩小工具表面（更低的 token 成本、更高的工具选择准确率）。`WithSelectionHandler` / `WithConfirmationHandler` 提供宿主的交互策略 —— 工具包仅在存在处理器且安全级别 > 0 时注册 `RequestSelection`/`RequestConfirmation`。

> 源码：`WorkflowToolCategory.cs`；`WorkflowAgentToolkit.cs` 第 142-149 行。
