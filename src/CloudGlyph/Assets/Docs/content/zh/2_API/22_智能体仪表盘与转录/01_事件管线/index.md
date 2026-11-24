# 事件管线

管线是库的事件词汇与阶段链：它观察一次运行做了什么并转成转录条目，而不改变运行。它位于 Agent Framework 官方中间件槽中，因此宿主仍可原样调用 `RunAsync` / `RunStreamingAsync`。

## 作用域成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `Pipeline` | `AgentPipeline Pipeline { get; }` | 作用域的事件链，首次使用时组合并共享。 |

用 `scope.WithTranscript(...)`（组合记账与转录阶段）或 `agent.AsBuilder().UseAgentPipeline(scope.Pipeline).Build()` 挂载管线。

## 基类：AgentEvent

| 成员 | 类型 | 说明 |
|---|---|---|
| `Timestamp` | `DateTimeOffset` | 管线观察到事件的时间。 |

事件是观察而非控制流：阶段可以丢弃或改写它们，但运行由智能体驱动。

### 事件类型

| 类型 | 携带 |
|---|---|
| `AgentTurnStarted` | `Kind`、`Prompt`、`Attachments`。构造函数为 `(AgentRunKind, string?)` 或 `(AgentRunKind, string?, IReadOnlyList<AgentAttachment>?)`。 |
| `AgentTurnCompleted` | `Kind`、`Text`（流式时为 null）、`Elapsed`、`Usage`。构造函数 `(AgentRunKind, string?, TimeSpan, UsageDetails?)`。 |
| `AgentUsageReported` | `Usage`——流式运行期间上报的 token 数。 |
| `AgentTurnFaulted` | `Kind`、`Error`（取消时为 null）、`Cancelled`。 |
| `AgentTextDelta` | `Text`——回答的原始片段。 |
| `AgentReasoningDelta` | `Text`——模型思考的原始片段。 |
| `AgentToolCallStarted` | `ToolName`。 |
| `AgentToolCallCompleted` | `ToolName`、`Result`、`Outcome`、`Elapsed`。 |
| `AgentMediaReceived` | `Attachment`、`Content`——模型产生了非文本媒体。 |

思考从 `TextReasoningContent` 恢复。`AgentResponseUpdate.Text` 只拼接回答，因此单独读它会丢失思考。

## 枚举

| `AgentRunKind` | 含义 |
|---|---|
| `Complete` | 由 `RunAsync` 产生；一个完整响应。 |
| `Streaming` | 由 `RunStreamingAsync` 产生；片段。 |

| `AgentToolOutcome` | 含义 |
|---|---|
| `Succeeded` | 工具运行并返回。 |
| `Refused` | 阶段在运行前拒绝调用；`Result` 携带拒绝内容。 |
| `Failed` | 工具抛出；包装器把它转成错误结果，运行继续。 |

## 接口：IAgentPipelineStage

| 成员 | 签名 | 说明 |
|---|---|---|
| `OnEventAsync` | `ValueTask OnEventAsync(AgentEvent agentEvent, Func<AgentEvent, ValueTask> next, CancellationToken cancellationToken)` | 看到每个事件并决定下一阶段看到什么：传下去、丢弃、替换或发出多个。 |

`DelegateAgentPipelineStage(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` 是委托适配器。

## 类：AgentPipeline

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Stages` | `IReadOnlyList<IAgentPipelineStage>` | 阶段，按顺序。 |
| `Use(IAgentPipelineStage stage)` | `AgentPipeline Use(IAgentPipelineStage stage)` | 追加阶段；返回自身。 |
| `Use(Func<...> handler)` | `AgentPipeline Use(Func<AgentEvent, Func<AgentEvent, ValueTask>, CancellationToken, ValueTask> handler)` | 追加委托阶段。 |
| `StageFailed` | `event EventHandler<AgentStageFailedEventArgs>?` | 阶段抛出时触发。发布照常继续。 |
| `PublishAsync(AgentEvent agentEvent, CancellationToken cancellationToken = default)` | `ValueTask PublishAsync(...)` | 按顺序把事件送过每个阶段。 |

损坏的阶段不会破坏运行：每个阶段被隔离，失败跳过链的其余部分并在 `StageFailed` 上浮现。只负责绘制的阶段绝不能把成功的工具调用变成错误结果。

`AgentStageFailedEventArgs` 携带 `Stage`、`Event` 与 `Error`。

## 类：AgentPipelineAgent

`AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline) : DelegatingAIAgent` 位于 MAF 中间件槽并发布运行事件。它原样、无缓冲地产出更新，保留流时序。

| 成员 | 签名 |
|---|---|
| 构造函数 | `AgentPipelineAgent(AIAgent innerAgent, AgentPipeline pipeline)` |
| RunCoreAsync | `protected override Task<AgentResponse> RunCoreAsync(IEnumerable<ChatMessage> messages, AgentSession? session = null, AgentRunOptions? options = null, CancellationToken cancellationToken = default)` |
| RunCoreStreamingAsync | `protected override IAsyncEnumerable<AgentResponseUpdate> RunCoreStreamingAsync(IEnumerable<ChatMessage> messages, AgentSession? session = null, AgentRunOptions? options = null, CancellationToken cancellationToken = default)` |

### 类：AgentPipelineExtensions

| 方法 | 签名 | 说明 |
|---|---|---|
| `UseAgentPipeline` | `static AIAgentBuilder UseAgentPipeline(this AIAgentBuilder builder, AgentPipeline pipeline)` | 把构建出的智能体包进中间件槽。 |
| `WithPipeline` | `static AIAgent WithPipeline(this AIAgent agent, AgentPipeline pipeline)` | 直接包装已有智能体。 |

## 类：TextPipeline

`TextPipeline(Func<AgentTranscript?> transcript, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` 把流式输出转成回答与思考条目。它在写入前合并片段，使长回答的成本线性而非二次。事件本身不受影响，只有转录写入被批处理。

## 类：ToolPipeline

`ToolPipeline(Func<AgentTranscript?>? transcript = null, Func<SynchronizationContext?>? marshalTo = null) : IAgentPipelineStage` 持有一个调用前查询的闸门，以及调用后写入的条目。

| 成员 | 类型 | 说明 |
|---|---|---|
| `MarshalTo` | `Func<SynchronizationContext?>?` | 调用编组到的线程，每次调用读取一次。 |
| `Refuse` | `Func<ToolInvocation, string?>?` | 调用前查询；返回消息即拒绝。预算与权限在此决定。 |
| `Confirm` | `Func<ToolInvocation, CancellationToken, ValueTask<string?>>?` | 在 `Refuse` 之后、调用之前查询；返回消息即拒绝。在编组块内运行，因此对话框在正确线程上。 |
| `MaxResultChars` | `Func<int?>?` | 逐调用结果大小上限；null 或 0 表示无上限。 |
| `MutationGate` | `Func<SemaphoreSlim?>?` | 在同一棵树上串行化图变更调用；查询不获取它。 |

## 相关

- [转录](../00_转录/index.md) —— 内置阶段写入的地方。
- [仪表盘](../02_仪表盘/index.md) —— 同一作用域上的面板。
