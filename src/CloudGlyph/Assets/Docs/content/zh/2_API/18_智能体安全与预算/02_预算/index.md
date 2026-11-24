# 预算与脏标记

决定一次调用*能否*运行的作用域，也决定会话*能花多少*。有五种上限；每个都在调用前强制，并在拒绝中指名。

## 调用与 token 上限

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithMaxToolCalls` | `WorkflowAgentScope WithMaxToolCalls(int maxCalls)` | 作用域生命周期内总工具调用上限，直到 `ResetToolCallLimit` 清空账本。在 `Bypass` 下不计数也不强制。 |
| `WithMaxReadToolCalls` | `WorkflowAgentScope WithMaxReadToolCalls(int maxCalls)` | 只读（查询）调用上限。用于阻止高 token 查询消耗变更预算。 |
| `WithMaxWriteToolCalls` | `WorkflowAgentScope WithMaxWriteToolCalls(int maxCalls)` | 变更（非查询）调用上限。 |
| `WithMaxToolResultChars` | `WorkflowAgentScope WithMaxToolResultChars(int maxChars)` | 单次工具结果文本上限。超过时用截断信封替换。`0` 关闭。默认 64 KiB。 |
| `WithMaxTokens` | `WorkflowAgentScope WithMaxTokens(int maxTokens)` | 总 token 上限。上报总数达到后拒绝工具调用；模型仍可作答。与调用上限不同，此项在 `Bypass` 下仍强制。 |

## 花费属性

| 成员 | 类型 | 说明 |
|---|---|---|
| `MaxToolCalls` | `int?` | 总调用上限，`null` 表示无。 |
| `MaxToolResultChars` | `int` | 结果大小上限。 |
| `MaxTokens` | `int?` | token 上限，或 `null`。 |
| `InputTokens` / `OutputTokens` / `TotalTokens` | `long` | provider 为此作用域运行上报的花费。 |
| `ResetTokenUsage()` | `void` | 清空上报的 token 计数，使之后的切换可再次花预算。 |

## 决定结果的行为

- **`Bypass` 跳过三种调用数上限且不记花费。** 它不跳过 `MaxTokens` 或 `Deny` 规则。提示文本由同一模式生成，因此模型不会围绕一个不会强制的上限规划。
- **`ResetToolCallLimit` 始终注册、始终允许。** 它是宿主退出调用预算的唯一方式，因此不能被关闭或过滤掉。调用它会询问用户；只有用户同意才重开预算。
- **子智能体消耗同一账本。** 子级额度是父级的子限额，不是第二口锅；根上限就是整棵树的上限。见[子智能体](../../21_子智能体/index.md)。

预算拒绝会指名上限与 `ResetToolCallLimit`，而不是含糊地说宿主设置。

## 脏标记

| 成员 | 签名 | 说明 |
|---|---|---|
| `AutoMarkDirty` | `bool AutoMarkDirty { get; }` | 变更工具调用是否自动把树标记为脏。 |
| `WithAutoMarkDirty` | `WorkflowAgentScope WithAutoMarkDirty(bool enabled = false)` | 为 `true` 时，每个变更工具调用都标记树为脏，智能体无需调用 `MarkDirty`。为 `false`（默认）时，注入的提示指示智能体在变更任务结束时调用一次 `MarkDirty`。查询工具从不自动标记。 |

## 示例

```csharp
scope.WithMaxToolCalls(200)
     .WithMaxReadToolCalls(150)
     .WithMaxWriteToolCalls(50)
     .WithMaxToolResultChars(48 * 1024)
     .WithMaxTokens(200_000);
```

在 `WithMaxToolCalls(2)` 下，第三次成功调用会被拒绝，拒绝会指名上限与 `ResetToolCallLimit`。

## 相关

- [权限模型](../00_权限模型/index.md) —— 与预算协同的「拒绝优先」求值顺序。
- [作用域安全](../01_作用域安全/index.md) —— 执行与命令选择性加入。
- [子智能体](../../21_子智能体/index.md) —— 子级如何消耗根账本。
