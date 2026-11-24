# 转录

`VeloxDev.AI.Pipelines.AgentTranscript` 是宿主绑定的对话：用户说了什么、模型想了什么、它答了什么、用了哪些工具——都在一个有序集合里。它承担 demo 宿主过去自己实现且会出错的两条规则：片段只延续同角色的开放条目，工具调用是条目而非分隔符。

## 挂载到工作流作用域

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithTranscript` | `WorkflowAgentScope WithTranscript(AgentTranscript transcript)` | 挂载对话并接好维护它的阶段。一次调用取代宿主本应自己写的运行循环。 |
| `Transcript` | `AgentTranscript? Transcript { get; }` | `WithTranscript` 之后的对话。 |

在构建智能体**之前**挂载：智能体被该阶段链包装，宿主无需自己循环流。

## 枚举：AgentTranscriptRole

| 成员 | 含义 |
|---|---|
| `User` | 来自用户的消息。 |
| `Assistant` | 模型的回答。 |
| `Reasoning` | 模型的思考。 |
| `ToolCall` | 一次完成的工具调用。 |
| `Error` | 呈现给用户的失败。 |

## 类：AgentTranscriptEntry

一个条目。单一类型携带角色，而非每个角色一个类，因此模板绑定并挑选自己的呈现。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Text` | `string` | 条目累积的文本（生成的 MVVM 属性）。 |
| `Role` | `AgentTranscriptRole` | 此条目是什么。 |
| `Timestamp` | `DateTimeOffset` | 首次创建时间。仅由恢复操作设置。 |
| `ToolName` | `string` | 工具名，用于 `ToolCall`。 |
| `Outcome` | `AgentToolOutcome?` | 工具如何结束，用于 `ToolCall`。 |
| `Detail` | `string` | 工具的原始结果负载。 |
| `Attachments` | `IReadOnlyList<AgentAttachment>` | 用户回合除文本外附带的内容；是显示记录，不是字节。 |
| `IsStreaming` | `bool` | 是否还可追加片段。回答与思考条目保持开放；其他种类创建即完成。 |
| `Summary` | `string` | 折叠后的一行。 |
| `HasDetail` | `bool` | 是否有值得展开的负载。 |
| `User(string text)` | `static AgentTranscriptEntry` | 一条文本消息。 |
| `User(string text, IReadOnlyList<AgentAttachment>? attachments)` | `static AgentTranscriptEntry` | 一条带附件的消息。 |
| `Assistant()` | `static AgentTranscriptEntry` | 一条新的空回答。 |
| `Reasoning()` | `static AgentTranscriptEntry` | 一个新的空思考块。 |
| `Error(string text)` | `static AgentTranscriptEntry` | 一个错误。 |
| `ToolCall(string toolName, string result, AgentToolOutcome outcome)` | `static AgentTranscriptEntry` | 一次完成的工具调用。 |

## 类：AgentTranscript

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry>` | 对话，最旧在前（生成的 MVVM 属性）。 |
| `Open` | `AgentTranscriptEntry?` | 当前追加片段的条目，或 `null`。 |
| `CloseOpen()` | `void CloseOpen()` | 关闭开放条目不开始新条目；回合结束时调用。 |
| `Clear()` | `void Clear()` | 丢弃整个对话。 |
| `AddUser(string text)` | `AgentTranscriptEntry AddUser(string text)` | 记录用户消息，关闭任何开放回答。 |
| `AddUser(string text, IReadOnlyList<AgentAttachment>? attachments)` | `AgentTranscriptEntry AddUser(string text, IReadOnlyList<AgentAttachment>? attachments)` | 同上，带附件。 |
| `AddError(string text)` | `AgentTranscriptEntry AddError(string text)` | 记录失败，关闭任何开放回答。 |
| `AppendAnswer(string fragment)` | `AgentTranscriptEntry AppendAnswer(string fragment)` | 延续开放回答；工具调用、思考块或用户消息会关闭它，回答在新条目中继续。 |
| `AppendReasoning(string fragment)` | `AgentTranscriptEntry AppendReasoning(string fragment)` | 延续开放思考块，规则相同。 |
| `AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | 记录完成的工具调用，先关闭任何开放回答。 |
| `ToMarkdown(AgentMarkdownOptions? options = null)` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | 渲染为 Markdown。连续工具调用合成一块；`ChatFences` 打开时每个成折叠面板。 |
| `ToPlainTextLines()` | `IReadOnlyList<string> ToPlainTextLines()` | 每条目一行，带角色前缀。工具调用也在此出现。 |
| `ToJson()` | `string ToJson()` | 显示记录作为 JSON 数组。 |
| `Restore(string json)` | `void Restore(string json)` | 用 `ToJson` 产出的文档替换所有条目。不是 JSON 数组时抛异常。 |

`ToJson` 持久化的是**显示**记录，不是模型的对话侧。要恢复对话，还需用框架持久化智能体会话。

该类型按设计非线程安全：由一个管线阶段喂入，在它被编组到的线程上。

## 类：AgentMarkdownOptions

| 成员 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `ReasoningFence` | `string` | `"thinking"` | 包裹思考的栅栏信息串。空则去掉栅栏。 |
| `ReasoningHeading` | `string?` | `"**思考：**"` | 栅栏上方标签，`null` 表示无。 |
| `ChatFences` | `bool` | `false` | 把思考与工具调用渲染为可折叠聊天面板，而非代码栅栏与项目符号列表。 |
| `ToolDetailLimit` | `int` | `4000` | 面板携带的工具负载最长字符数；`0` 表示全部。 |

## 示例

```csharp
using VeloxDev.AI.Pipelines;

var transcript = new AgentTranscript();
transcript.AddUser("List the nodes.");
transcript.AppendReasoning("I should call ListNodes first.");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("The graph has no nodes.");

Console.WriteLine(transcript.ToMarkdown());
```

## 相关

- [事件管线](../01_事件管线/index.md) —— 填充转录的阶段。
- [仪表盘](../02_仪表盘/index.md) —— 对话旁的面板。
