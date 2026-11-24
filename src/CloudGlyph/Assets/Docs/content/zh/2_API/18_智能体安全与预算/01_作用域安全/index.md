# 作用域安全

这些 `WorkflowAgentScope` 成员挂载权限策略，以及位于工具体内的一些选择性加入。每个都返回同一个作用域以便链式调用。

## 权限成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `PermissionPolicy` | `AgentPermissionPolicy PermissionPolicy { get; }` | 生效的策略。永不为 `null`。 |
| `PermissionMode` | `AgentPermissionMode PermissionMode { get; }` | 生效的模式。 |
| `WithPermissionMode` | `WorkflowAgentScope WithPermissionMode(AgentPermissionMode mode)` | 构造期间把会话移到另一个模式。 |
| `SetPermissionMode` | `bool SetPermissionMode(AgentPermissionMode mode)` | 供绑定驱动宿主的运行时对应物；返回模式是否移动。 |
| `WithPermissionRule` | `WorkflowAgentScope WithPermissionRule(PermissionDecision decision, params string[] patterns)` | 为每个模式在模式之下添加一条规则。规则在包括 `Bypass` 的每个模式中都成立。 |
| `WithoutPermissionRules` | `WorkflowAgentScope WithoutPermissionRules()` | 移除全部规则；模式不变。 |
| `WithPermissionJudge` | `WorkflowAgentScope WithPermissionJudge(Func<ToolInvocation, PermissionDecision>? judge)` | 提供 `Auto` 模式的 judge，或传 `null` 移除。 |
| `WithModePrompt` | `WorkflowAgentScope WithModePrompt(AgentPermissionMode mode, string? promptBody)` | 在库内置文本之后追加某个模式的宿主规则。内置文本不被替换；追加内容以优先呈现。`null` 移除追加。 |

策略每次调用读取，因此 `SetPermissionMode` 设置的模主管住下一次工具调用。提示文本在下一轮追上。

```csharp
using VeloxDev.AI.Safety;

scope.WithPermissionMode(AgentPermissionMode.AutoEdit)
     .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot", "DisconnectSlots");
```

## 执行选择性加入

两个独立控件位于**工具体内**而非共享包装器中。两者默认关闭。

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithAllowNodeExecution` | `WorkflowAgentScope WithAllowNodeExecution(bool enabled = false)` | 允许 `ExecuteNode`、`ExecuteNodes`、`BroadcastNode`、`ReverseBroadcastNode`、`RunCompiledWorkflow` 及相关执行工具。它们运行任意业务代码，因此来自不可信来源的图应保持关闭。 |
| `WithAllowedGenericCommands` | `WorkflowAgentScope WithAllowedGenericCommands(params string[] commandNames)` | 为 `ExecuteCommandOnNode` 与 `ExecuteCommandById` 列出允许的命令名。`Command` 后缀可选。从未调用时，通用命令执行完全禁用。 |

安全在代码中强制，不在提示文字里。模式仍会拦截调用；这些开关决定工具是否被注册为可执行。

## 交互处理器

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSelectionHandler` | `WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` | 注册 `RequestSelection` 的处理器。为 `null` 时工具根本不注册。 |
| `WithConfirmationHandler` | `WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` | 注册 `RequestConfirmation` 的处理器。为 `null` 时工具不注册。 |

处理器必须在完成前设置事件参数上的结果字段。交互工具从不会被模式阻止：询问是计划获得同意的方式。

## 嵌套类：WorkflowAgentScope.SelectionResult

承载选择交互的结果。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `SelectedOption` | `string?` | 单选：选中的选项，取消时为 `null`。 |
| `SelectedOptions` | `IReadOnlyList<string>` | 多选：选中的选项；未选时为空。 |
| `FreeTextResponse` | `string?` | 自由文本输入，或 `null`。 |
| `Single` | `static SelectionResult Single(string? option)` | 创建单选结果。 |
| `Multi` | `static SelectionResult Multi(IReadOnlyList<string> options, string? freeText = null)` | 创建多选结果。 |
| `FreeText` | `static SelectionResult FreeText(string text)` | 创建纯自由文本结果。 |

## 相关

- [权限模型](../00_权限模型/index.md) —— 这些成员配置的策略。
- [预算与脏标记](../02_预算/index.md) —— 同一作用域上的花费上限。
- [交互事件](../03_交互事件/index.md) —— 事件参数形状。
