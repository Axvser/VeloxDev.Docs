# 交互事件

这些 Core 类型承载宿主处理器接收、调用方观察的数据。它们位于 `VeloxDev.AI` 而非安全命名空间，因为它们描述的是面向智能体的契约，而不是策略引擎。

## 类：AgentToolCallEventArgs

为 `IAgentToolCallNotifier.ToolCalled` 提供数据，在每次**成功**的工具调用后触发。被拒绝或失败的调用改由作用域管线上的 `AgentToolCallCompleted` 承载。

| 成员 | 类型 | 说明 |
|---|---|---|
| `ToolName` | `string` | 被调用工具名。构造时为 null 抛 `ArgumentNullException`。 |
| `Result` | `string` | JSON 结果；无则为空。 |
| `CallCount` | `int` | 会话内累计调用数。`Bypass` 模式不记花费，因此在那里每次调用都报告 `0`。 |

## 接口：IAgentToolCallNotifier

触发 `ToolCalled` 的作用域或 toolkit 的契约。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>? ToolCalled` | 成功调用后触发。 |

## 类：AgentSelectionEventArgs

`RequestSelection` 工具的数据。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Prompt` | `string` | 选项列表上方显示的问题。 |
| `Options` | `IReadOnlyList<string>` | 有序候选字符串。 |
| `AllowMultiSelect` | `bool` | `true` 为复选框，`false`（默认）为单选按钮。 |
| `FreeTextPrompt` | `string` | 自由文本框上方的标签。默认 `"Custom input (optional)"`。 |
| `SelectedOption` | `string?` | 单选答案；由处理器在完成前设置。 |
| `SelectedOptions` | `IReadOnlyList<string>?` | 多选答案；由处理器设置。 |
| `FreeTextResponse` | `string?` | 自由文本答案；无则为 `null` 或空。 |

选项下方始终显示自由文本框。

## 类：AgentConfirmationEventArgs

`RequestConfirmation` 工具的数据。

| 成员 | 类型 | 说明 |
|---|---|---|
| `OperationKey` | `string` | 操作类型的稳定机器可读键，如 `"DeleteNode"`。持久化批准以它为键。 |
| `Description` | `string` | 作为对话框正文显示的人类可读说明。 |
| `Result` | `AgentConfirmationResult` | 用户决定；默认 `Deny`。由处理器在完成前设置。 |

## 枚举：AgentConfirmationResult

| 成员 | 含义 |
|---|---|
| `Deny` | 用户拒绝；智能体不得继续。 |
| `AllowOnce` | 仅允许此请求；相同请求会再次询问。 |
| `AllowAlways` | 在本会话剩余时间里允许该操作，后续相同 `OperationKey` 的请求静默批准。 |

## 说明

Core 中存在 `IAgentSelectionNotifier` 与 `IAgentConfirmationNotifier`，但已标记过时。库中没有任何类型实现或触发它们：宿主改由 `WithSelectionHandler` / `WithConfirmationHandler` 提供处理器，接口仅为让既有源码继续编译而保留。

## 相关

- [作用域安全](../01_作用域安全/index.md) —— 这些处理器的注册处。
- [智能体仪表盘与转录](../../22_智能体仪表盘与转录/index.md) —— 承载拒绝与失败调用的管线事件。
