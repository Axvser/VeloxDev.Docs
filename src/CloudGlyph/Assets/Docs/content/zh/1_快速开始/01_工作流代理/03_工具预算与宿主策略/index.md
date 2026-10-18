# 03 · 工具预算与宿主策略

作用域决定 agent 能花多少、以及危险工具是否存在。这些都是**宿主策略**，在代码中强制执行，而非写在提示里：被闸门关闭的工具要么从工具列表中被过滤掉，要么在函数体运行前返回结构化的 JSON 拒绝。

## 1. 工具调用预算

```csharp
scope.WithMaxToolCalls(200)          // 所有工具调用的总上限
    .WithMaxReadToolCalls(100)       // 只读/查询调用上限（ListNodes、GetFullTopology……）
    .WithMaxWriteToolCalls(50);      // 其余一切（变更、执行、命令）的上限
```

- 当调用的名字位于工具包的只读集合中时计为**读** —— Query 工具，加上 `TakeSnapshot` / `GetChangesSinceSnapshot`、`GetNodeStatistics`、五个 Graph 工具、`RequestSelection` / `RequestConfirmation`、`ResetToolCallLimit`、四个编译/计划读工具（`CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`、`GetExecutionLog`），以及**每一个技能与子代理工具名**（从 `SkillAgentToolkit.ToolNames` 与 `SubAgentAgentToolkit.ToolNames` 合并进来）。`EnterPlanMode` / `ExitPlanMode` 不在该名单中，因此尽管它们不触碰图，也计为**写**调用。
- 一个预检闸门（`CheckInvocation`）在编组块内、函数体之前运行。当某上限已达时返回拒绝；函数体从不运行，且该调用**不**计数。

拒绝措辞（来自 `LimitRefusal`）：

```text
Tool call limit (200) reached. No further tool calls are accepted until the budget is extended.
If the task is unfinished, call ResetToolCallLimit — it asks the user, and only their agreement
reopens the budget. Do not retry this call, and do not tell the user you can continue without it.
```

三种 `cause` 前缀为 `Tool call limit (N) reached.`、`Mutation tool call limit (N) reached.` 与 `Query tool call limit (N) reached.`；被派发的子代理还可能撞上 `The session's tool-call budget (N) is spent.`（根作用域的上限，最先被询问）。

**预期结果：** 触及某上限后，受影响的工具返回携带该消息的 `status:"error"`，而非执行。

## 2. `ResetToolCallLimit` —— 花光预算后的出路

每个工具包都会额外注册一个工具 `ResetToolCallLimit`（常量 `WorkflowAgentToolkit.ResetBudgetToolName`），**无论请求了哪些类别标志**。它是被拒绝后继续的唯一途径。

- 它从不消耗预算（若计数，就会重新增加刚被清零的计数器 —— 重置会自我撤销）。
- 它挺过它本就为之存在的闸门：即使预算已花光，预检闸门对它也返回 `null`。
- 它经作用域的确认处理器、以操作键 `extend-tool-call-budget` 把问题交给用户。询问本身就是全部安全属性 —— agent 只能问，永不能自行放宽自己的预算。**没有**注册处理器时答案是**拒绝**（一个无法回答的提示必须拒绝）。`AgentActionCategory.Interact` 从不交给模式策略，因此没有任何模式能压下这个问题。
- 用户同意后它调用 `ResetChain()`，清零本级**以及其上的每一级** —— 若根额度仍被花光，下一次调用就会立刻被拒绝。

**预期结果：** 在某上限已达时调用 `ResetToolCallLimit`，处理器答「允许」则返回 `Tool-call budget reset by the user. You may continue.`；无处理器则返回 `status:"denied"`。

## 3. 能力闸门

```csharp
scope.WithAllowNodeExecution(true)                 // 启用运行代码的工具
    .WithAllowedGenericCommands("ReceiveCommand"); // ExecuteCommandOnNode/ExecuteCommandById 的白名单
```

- `WithAllowNodeExecution(enabled)` 闸控运行任意节点业务代码的工具：`ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow`、`GetNodeResult`、`StartCompiledWorkflow` 与 `ContinueCompiledWorkflow`。默认关闭。被拦的运行工具返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` 只编译的计划工具（`CompileWorkflow`、`CompileNodeResult`、`GetCompileStatus`）从不运行节点代码，**不**受闸控；句柄操作 `GetCompiledRunStatus` / `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun` 也不受闸控。
- `WithAllowedGenericCommands(params string[])` 为 `ExecuteCommandOnNode` / `ExecuteCommandById` 列出命令白名单；`"Command"` 后缀可省。从不调用 ⇒ 通用命令执行被完全禁用（安全默认）。该闸门由 `CommandInvoker` 逐次调用检查。

## 4. 逐工具开关

```csharp
scope.WithToolEnabled("ClearHistory", false);   // 流式：下一轮起关闭
bool moved = scope.SetToolEnabled("Undo", true);// 运行时：返回开关是否真的移动
bool on = scope.IsToolEnabled("Undo");          // 读取当前状态
```

- `CreateTools(categories)` 用 `IsToolEnabled` 过滤最终列表；`CreateAllTools()` 返回**未过滤**的表面（宿主 UI 枚举它来展示可切换的工具）。
- 被关闭的工具也会被预检闸门**拒绝**，而不仅是过滤：闸门的钩子与该作用域组合的每个切片共享（MCP 与技能提供器拿到的是同一策略），因此一个开关也能触达 MCP 或技能来源的工具。拒绝文本为 `'{toolName}' is disabled by host policy. Do not try to work around it — use another tool or report it to the user.`
- 开关可在**会话中途**翻转：工具集每轮重新渲染（见「运行一轮对话」页），因此无需重建 agent，也不会留下过期的缓存渲染。
- `DisabledToolNames`（只读）列出被关闭的；作用域版本移动时触发 `Changed` 事件。

**预期结果：** `SetToolEnabled("Undo", false)` 后，下一次调用不再提供 `Undo`，直接调用它会被宿主策略消息拒绝。

## 5. 权限模式 —— 代码闸门

会话的权限策略取代了旧的交互安全档位和独立的工具审批开关。它由一个 `AgentPermissionMode` 加可选规则组成，**逐次调用**在函数体运行前评估。`PermissionDecision` 为 `Allow` | `Ask` | `Deny`；模式是用户可以切换的**具名状态**，每次拒绝都会点名该模式以及该切到哪一档。

| 模式 | 值 | 允许什么 |
|---|---|---|
| `Plan` | 0 | 只读与交互；编辑、执行与可达性变更一律拒绝。 |
| `Manual` | 1 | 每个非读动作都交给用户。 |
| `AutoEdit` | 2 | 读与图编辑直接运行；执行与可达性变更询问。 |
| `Auto` | 3 | 读、编辑与执行直接运行；只有可达性变更（`Curate`）询问。**默认。** |
| `Bypass` | 4 | 什么都不问；显式 `Deny` 规则仍然生效。 |

```csharp
scope.WithPermissionMode(AgentPermissionMode.AutoEdit)
     .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot")
     .WithPermissionRule(PermissionDecision.Deny, "category:Curate");
bool moved = scope.SetPermissionMode(AgentPermissionMode.Manual);  // 运行时切换
```

- **规则是细粒度层。** 模式按工具名（`DeleteNode`、`Get*`）、按类别（`category:Edit`）或按来源（`source:mcp:*`、`source:skill`）选择。`Deny` 规则在所有模式下生效，包括 `Bypass`。
- **闸门在代码里。** `ToolPipeline.Confirm` 调用 `PermissionPolicy.Evaluate(invocation)`；`Ask` 以工具名交给确认处理器（因此「本会话允许」即批准该工具），`Deny` 返回 `DescribePermissionRefusal`。模型无法靠不调用 `RequestConfirmation` 绕过它。
- **MCP 管理工具是 `Curate`**（它们改变会话可达范围），因此 `Auto` 仍会询问 `AddMcpServer`、`SetMcpServerArguments`、`LoadMcpServers` 与 `UnloadMcpServer`。已连接服务器*导出的*工具是第三方代码，归类为 `Execute`；`Auto` 让它们运行，`AutoEdit`/`Manual` 会询问，宿主也可用 `Ask("source:mcp:*")` 这样的规则闸控它们。`WithPermissionJudge` 为 `Auto` 中无规则裁决的调用提供决定；judge 抛异常即拒绝。
- **Agent 自己只有两个模式转换**，且都先询问：`EnterPlanMode` 与 `ExitPlanMode`（仅在配置了确认处理器时注册）。刻意没有能把模式放宽的工具。

**预期结果：** 在 `Plan` 下，`CreateNode` 返回点名 `Plan` 的拒绝；在 `AutoEdit` 下它直接运行，而 `ExecuteNode` 会询问。`DeleteNode` 上的 `Deny` 规则在任何模式下都拒绝它。

## 6. 交互处理器

两个可选工具直接询问用户；注册只取决于处理器，与任何安全级别无关：

```csharp
scope.WithSelectionHandler(async args =>        // 支撑 RequestSelection
{
    args.SelectedOption = args.Options.FirstOrDefault();
    await Task.CompletedTask;
});
scope.WithConfirmationHandler(async args =>      // 支撑 RequestConfirmation / Ask 决定 / ResetToolCallLimit
{
    args.Result = AgentConfirmationResult.AllowOnce;   // 或 AllowAlways | Deny
    await Task.CompletedTask;
});
```

- 调用了 `WithSelectionHandler` 时才注册 `RequestSelection`；在处理内设置 `args.SelectedOption`（单选）或 `args.SelectedOptions` / `args.FreeTextResponse`。嵌套的 `WorkflowAgentScope.SelectionResult` 提供 `Single` / `Multi` / `FreeText` 工厂供底层使用。
- 调用了 `WithConfirmationHandler` 时才注册 `RequestConfirmation`；设置 `args.Result = AllowOnce | AllowAlways | Deny`。`AllowAlways` 按 `operationKey` 本会话内记住（`ResolveConfirmationAsync`）。
- 没有确认处理器时，每个 `Ask` 决定都按拒绝作答，`ResetToolCallLimit` 也拒绝。

**预期结果：** 两个处理器都注册时，`RequestSelection` 与 `RequestConfirmation` 在 `ProvideTools()` 中各出现一次；都未注册时两者缺席，工具计数再少掉 `EnterPlanMode` / `ExitPlanMode`。

## 7. UI 线程、回调与脏标记

```csharp
scope.WithSynchronizationContext(SynchronizationContext.Current)  // 把每次工具调用编组到 UI 线程
    .WithAutoMarkDirty(false)                                     // 默认：agent 自己调用 MarkDirty
    .WithToolCallCallback(args =>                                 // 每次完成的调用之后
    {
        Console.WriteLine($"tool {args.ToolName} (count {args.CallCount})");
        return Task.CompletedTask;
    });
```

- `WithSynchronizationContext(context)` 把每次工具调用编组到该上下文 —— 组件与 UI 绑定时必需（demo 传 `SynchronizationContext.Current`）。
- `WithAutoMarkDirty(enabled)` —— `true` 时在每次**成功且非查询**的调用后把树标记为脏（`AccountingStage` → `AccountAsync`）；默认 `false`，由注入的 `CommandReference.md` 提示让 agent 在变更任务末尾调用一次 `MarkDirty`。
- `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` 在每次完成的调用后被调用；`ToolCalled`（`IAgentToolCallNotifier` 事件）也会触发。

**预期结果：** 每次工具调用都在注册的上下文上运行；自动脏标记关闭时，树的脏标志只在 agent 调用 `MarkDirty` 时改变。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。曾有一次 2026-10-01 的确定性测试记录（`失败: 0，通过: 387`），但它早于权限模式 / 上下文树重构，不能作为本页所述闸门今天行为的证据。
