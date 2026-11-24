# 使用

## 转录 API

```csharp
transcript.AddUser("导出这张图。");
transcript.AppendAnswer("我来把它序列化。");
transcript.AppendReasoning("用 SerializeWorkflow 的 summary 模式。");
transcript.AddToolCall("SerializeWorkflow", """{"status":"ok"}""", AgentToolOutcome.Succeeded);
transcript.AddError("导出失败。");
```

| 成员 | 结果 |
|---|---|
| `Entries` | 有序的 `AgentTranscriptEntry` 列表 |
| `AddUser(text, attachments?)` | 一个 `User` 条目，关闭打开的答案 |
| `AppendAnswer(fragment)` | 延续或新建 `Assistant` 条目 |
| `AppendReasoning(fragment)` | 延续或新建 `Reasoning` 条目 |
| `AddToolCall(name, result, outcome)` | 一个 `ToolCall` 条目 |
| `AddError(text)` | 一个 `Error` 条目 |
| `ToMarkdown(options?)` | 可渲染文档 |
| `ToJson()` / `Restore(json)` | 持久化**显示记录** |
| `ToPlainTextLines()` | 每条一行，带角色前缀 |

`ToMarkdown` 接受 `AgentMarkdownOptions`（`ReasoningFence`、`ReasoningHeading`、`ChatFences`、`ToolDetailLimit`）。开启 `ChatFences` 时每次工具调用单独成可折叠面板；不开时是紧凑的项目符号列表。

**预期结果：** `transcript.ToMarkdown()` 按顺序显示用户轮、思考块、工具行与答案。`Restore(ToJson())` 复现同样的条目。

## 事件管线

管线在运行期间填充转录。`scope.Pipeline` 已带记账与转录阶段；你可以在前后追加自己的阶段。

```csharp
using VeloxDev.AI.Pipelines;

scope.Pipeline.Use((agentEvent, next, ct) =>
{
    if (agentEvent is AgentToolCallCompleted tool)
        Console.WriteLine($"{tool.ToolName}: {tool.Outcome} in {tool.Elapsed.TotalMilliseconds:F0} ms");
    return next(agentEvent);
});
```

| 事件 | 携带 |
|---|---|
| `AgentTurnStarted` | 运行类型、提示词、附件 |
| `AgentTextDelta` / `AgentReasoningDelta` | 一个流式片段 |
| `AgentToolCallStarted` / `AgentToolCallCompleted` | 工具名、结果、结局、耗时 |
| `AgentTurnCompleted` | 答案、耗时、token 用量 |
| `AgentTurnFaulted` | 错误或取消 |
| `AgentUsageReported` | 流式回合的 token 用量 |
| `AgentMediaReceived` | 一个附件及其内容 |

抛异常的阶段通过 `AgentPipeline.StageFailed` 上报，运行继续。`WithPipeline` 把链装进框架的中间件槽，因此 `RunAsync` 与 `RunStreamingAsync` 都会被观察到。

**预期结果：** 一次运行每完成一个工具调用打印一行，转录自动获得对应条目，宿主无需手动追加。

## 仪表盘

`AgentDashboardViewModel` 把一个 scope 分成五个集合：

| 集合 | 行 |
|---|---|
| `SystemTools` | 工作流内置工具加宿主注册的工具 |
| `SkillTools` | `ListSkills`、`load_skill`、`UnloadSkill`、`read_skill_resource` |
| `McpServers` | 每个已配置服务器一行，可展开到它的工具 |
| `Skills` | 每个被发现的技能 |
| `SubAgents` | 本会话派发的子代理 |

每一行都是**投影**，不是第二个真相源。翻转 `IsEnabled` 会调用 `ApplyToScope`；scope 里的变化经 `SetFromScope` 回灌且不回响。这就是面板不能直写 `SkillStatusViewModel.IsEnabled` 的原因：那样会绕过 scope 的 `Version` 自增，按版本缓存的提示词会继续送出宿主以为已经关掉的文字。

`IsReachable` 是 `IsEnabled && Note.Length == 0`——「开着但被宿主策略挡住」是真实状态，`Note` 会写明。`ActivityText` 报告调用次数。

**预期结果：** 翻转 `dashboard.Skills[0].IsEnabled` 会在下一轮改变 `scope.Skills`；直接改过 scope 后用 `dashboard.Rebuild()` 重读全部。

## 媒体输入

媒体属于**用户消息**，不属于工具结果。在 OpenAI 兼容的 chat completions 里，工具消息只有文本通道，工具返回的 `DataContent` 到达模型时是一段 base64 JSON 字符串，而不是像素或声音。

```csharp
var image = await AgentMedia.FromFileAsync("preview/frame.png");
var note  = await AgentMedia.FromFileAsync("audio/note.mp3");
var pdf   = await AgentMedia.FromFileAsync("docs/spec.pdf");

var options = AgentMediaOptions.CreateVisionDefault();
options.Transcoder = myHostTranscoder; // 可选

await foreach (var update in agent.RunStreamingWithMediaAsync(
    "Check the frame, the voice note and the spec.", new[] { image, note, pdf }, options, session))
{
    // 每个负载各走自己的 image_url / input_audio / file 块
}
```

想自己驱动 `RunAsync` 时用 `AgentMessage.CreateUserAsync(prompt, media, options)` 构造消息。`AgentMediaReference.FromUrl` 只发送 URL，不抓取。`AgentAttachment` 出现在 `AgentTurnStarted` 里，只有名称、媒体类型与大小——没有字节。

**预期结果：** 接受图片的模型能回答关于这一帧的问题；不接受的模型会拒绝该部分，因此要保留纯文本兜底。

## 验证

1. 运行完整程序。它打印 Markdown 转录、JSON 往返前后的条目数，以及四项仪表盘摘要。
2. 确认恢复后的转录条目数相同。
3. 确认 `SystemToolSummary` 非零，另外三项子系统摘要为 `0/0`——没有挂载技能、MCP 服务器或子代理。

## 完整代码

```csharp
using VeloxDev.AI.Dashboard;
using VeloxDev.AI.Pipelines;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var transcript = new AgentTranscript();
transcript.AddUser("添加一个节点并接上它的输出。");
transcript.AppendReasoning("编辑前先检查图。");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("目前还没有节点，我来创建一个。");
transcript.AddToolCall("CreateNode", """{"status":"ok","nodeIndex":0}""", AgentToolOutcome.Succeeded);

Console.WriteLine(transcript.ToMarkdown());
Console.WriteLine($"entries: {transcript.Entries.Count}");

var json = transcript.ToJson();
var restored = new AgentTranscript();
restored.Restore(json);
Console.WriteLine($"restored entries: {restored.Entries.Count}");

var scope = new TreeDefaultViewModel().AsAgentScope();
using var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine($"system tools: {dashboard.SystemToolSummary}");
Console.WriteLine($"skills:       {dashboard.SkillSummary}");
Console.WriteLine($"mcp:          {dashboard.McpSummary}");
Console.WriteLine($"sub-agents:   {dashboard.SubAgentSummary}");
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentTranscript.cs`、`AgentEvent.cs`、`AgentPipeline.cs`、`AgentPipelineAgent.cs`、`Agent/Dashboard/AgentDashboardViewModel.cs`、`Agent/Dashboard/AgentMemberViewModel.cs`、`Agent/Media/AgentMedia.cs` 与 `Agent/Media/AgentMediaAgentExtensions.cs` 做了静态核对。仪表盘只有测试覆盖，没有 demo 绑定。没有记录运行输出。
