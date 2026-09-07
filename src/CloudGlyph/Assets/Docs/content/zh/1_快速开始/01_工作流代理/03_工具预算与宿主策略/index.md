# 工作流代理 — 工具预算与宿主策略

作用域决定代理每轮可以花多少工具调用、以及哪些危险工具到底存不存在。这些都是**宿主策略**决定：当一个工具被门禁关掉时，它要么不出现在 `ProvideTools()` 里，要么在调用时返回 `status:"error"` 的 JSON 说明它被禁用 —— 强制执行在代码里，不在提示词里。

## 1. 交互安全与人在回路处理器

交互安全是单个 0–3 整数（默认 **1**），用 `WithInteractionSafety(level)` 设置：

| 级别 | 名称 | 行为 |
|---|---|---|
| 0 | 静默 | 完全自主。两个交互工具被整体跳过，且不发出任何安全策略。 |
| 1 | 谨慎（默认） | 仅当意图确实有歧义或动作是批量/破坏性时才询问。 |
| 2 | 平衡 | 当存在多个可行路径、或动作触碰 ≥ 2 个节点/连接时询问。 |
| 3 | 严格 | 在每一个非纯单节点创建的变更前询问；无条件门禁一切破坏性动作。 |

1–3 级只在存在对应处理器时才注册工具，且各等级（1–3）的整段策略正文可用 `WithInteractionSafetyPrompt(level, body)` 替换 —— 第 0 级的静默规则不可覆盖。

```csharp
scope.WithInteractionSafety(3);
scope.WithInteractionSafetyPrompt(2, "在触碰超过一个节点的任何结构性变更前必须询问。");

scope.WithSelectionHandler(async args =>           // 支撑 RequestSelection 工具
{
    args.SelectedOption = args.Options.FirstOrDefault();   // 单选结果
    // 多选/自由文本：args.SelectedOptions = [...]; args.FreeTextResponse = "...";
    await Task.CompletedTask;
});
scope.WithConfirmationHandler(async args =>         // 支撑 RequestConfirmation 工具
{
    args.Result = AgentConfirmationResult.AllowOnce;      // 或 AllowAlways | Deny
    await Task.CompletedTask;
});
```

- 仅当 `WithInteractionSafety(level)` 的 level > 0 **且**调用了 `WithSelectionHandler(...)` 时才注册 `RequestSelection`；在处理器内设置 `args.SelectedOption`（单选）或 `args.SelectedOptions` / `args.FreeTextResponse`（多选/自由文本）。作用域还提供一个小 `SelectionResult` 帮手，含 `Single(...)` / `Multi(...)` / `FreeText(...)` 工厂。
- 仅当 level > 0 且调用了 `WithConfirmationHandler(...)` 时才注册 `RequestConfirmation`；在处理器内设置 `args.Result = AgentConfirmationResult.AllowOnce | AllowAlways | Deny`。`AllowAlways` 会在本次会话剩余时间内记住该批准。

**预期结果：** level 0 时不存在 `RequestSelection` / `RequestConfirmation` 工具；level 3 时每个已注册处理器恰好对应出现一个对应工具。

## 2. 工具调用预算

三个预算旋钮限制模型每轮最多调用多少次工具：

```csharp
scope.WithMaxToolCalls(200)            // 全部工具调用的总上限
    .WithMaxReadToolCalls(100)         // 只读/查询调用上限（ListNodes、GetFullTopology、...）
    .WithMaxWriteToolCalls(50);        // 其余一切的上限（变更、执行、命令）
```

- 当工具名位于工具包的只读集合中时计入**读** —— `Query` 工具加上只读的 graph/analytics/state/interaction 工具（`GetChangesSinceSnapshot`、`TakeSnapshot`、`GetNodeStatistics`、`SearchForward`/`SearchReverse`/`SearchAllRelative`、`IsConnected`、`FindPath`、`RequestSelection`、`RequestConfirmation`）。其余一切计入**写**（全部 Mutation 工具、`MarkDirty`、六个 Execution 工具、两个 Command 工具）。
- 超过预算会在工具运行前返回错误 JSON，例如 `Tool call limit (200) exceeded...` / `Mutation tool call limit (50) exceeded...` / `Query tool call limit (100) exceeded...`。
- 在调用对应 `With*` 之前预算是未设置（`null`）。设置独立上限后，token 密集的读查询就不会悄悄吃光变更预算。

**预期结果：** 超限后对应工具返回 `status:"error"` JSON 并附上限信息，而不是继续执行。

## 3. 节点执行、通用命令、UI 线程与脏标记

```csharp
scope.WithAllowNodeExecution(true)                        // 启用 ExecuteNode/ExecuteNodes/BroadcastNode/
                                                          // ReverseBroadcastNode/RunCompiledWorkflow/GetNodeResult
    .WithAllowedGenericCommands("ReceiveCommand")          // 为 ExecuteCommandOnNode/ExecuteCommandById 加白名单
    .WithSynchronizationContext(SynchronizationContext.Current) // 把每个工具调用编组到 UI 线程
    .WithAutoMarkDirty(false)                              // 默认：代理必须自己调用 MarkDirty
    .WithToolCallCallback(args =>                          // 在每个工具调用之后
    {
        Console.WriteLine($"tool {args.ToolName} called (count {args.CallCount})");
        return Task.CompletedTask;
    });
```

- `WithAllowNodeExecution(enabled)` 门禁那六个会运行任意节点业务代码的工具（`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow`、`GetNodeResult`）。默认关闭。仅编译工具（`CompileWorkflow`、`CompileNodeResult`）从不运行节点代码，因此**不受门禁**。被拦截的运行工具会返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`
- `WithAllowedGenericCommands(params string[])` 为通用命令工具（`ExecuteCommandOnNode` / `ExecuteCommandById`）加白名单。名字会被归一化为 `"Command"` 后缀。从未调用 ⇒ 通用命令执行整体禁用（安全默认）。未列入的命令会返回错误，要求宿主用 `WithAllowedGenericCommands` 加白名单。
- `WithSynchronizationContext(context)` 注册 UI 上下文，让每个工具调用都编组到它上面 —— 当工作流组件绑定 UI 时必需（演示在 UI 线程调用 `SynchronizationContext.Current`）。
- `WithAutoMarkDirty(enabled)` — 为 `false`（默认）时框架不自动置脏，注入的 `CommandReference.md` 提示词会告诉代理在变更任务结束时调用一次 `MarkDirty`；为 `true` 时每个非查询的变更工具调用都会自动把树置脏。查询工具从不自动置脏。
- `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` 在每个工具调用之后触发，带工具名、结果与累计次数 —— 适合用它触发 UI 虚拟化刷新（演示从中抛出 `ToolCalled` 事件）。

**预期结果：** 不设置 `WithAllowNodeExecution` 时，`ExecuteNode` 返回 `status:"error"` JSON 并引用宿主策略；设置它并加白名单命令后，对应工具出现在 `ProvideTools()` 中并可以运行。

## 运行声明

- ⚠️ 仅静态核验。行为、默认值与错误消息措辞取自 `WorkflowAgentScope.cs` 与 `WorkflowAgentToolkit.cs`（门禁代码行与 `TrackedAIFunction`）；本页内容未编译或执行。
