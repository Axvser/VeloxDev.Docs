# 带媒体运行

`VeloxDev.AI.AgentMediaAgentExtensions` 把多模态内容附到用户消息并先校验再运行。这些重载的存在，是为了让宿主无需手工构建消息、忘记种类/媒体类型检查、大小限制或转码器。被拒的负载在发出任何请求前失败。

## 方法

| 方法 | 签名 | 说明 |
|---|---|---|
| `RunWithMediaAsync` | `Task<AgentResponse> RunWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<AgentMedia> media, AgentMediaOptions? options = null, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | 校验负载（需要时转换）并非流式运行。至少一个负载时可传空提示。 |
| `RunWithMediaAsync` | `Task<AgentResponse> RunWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<IAgentMediaContent> media, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | 用已校验负载或 URL 引用运行。 |
| `RunStreamingWithMediaAsync` | `IAsyncEnumerable<AgentResponseUpdate> RunStreamingWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<AgentMedia> media, AgentMediaOptions? options = null, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | 校验并流式返回回答。 |
| `RunStreamingWithMediaAsync` | `IAsyncEnumerable<AgentResponseUpdate> RunStreamingWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<IAgentMediaContent> media, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | 用已校验负载或引用流式运行。 |

## 参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `agent` | `AIAgent` | 要运行的智能体。 |
| `prompt` | `string` | 文本；至少一个负载时可空。 |
| `media` | `IEnumerable<AgentMedia>` 或 `IEnumerable<IAgentMediaContent>` | 按显示顺序的负载。 |
| `options` | `AgentMediaOptions?` | 限制与转码器；null 时用内置默认。 |
| `session` | `AgentSession?` | 要继续的会话，`null` 表示新运行。 |
| `runOptions` | `AgentRunOptions?` | 框架运行选项。 |
| `cancellationToken` | `CancellationToken` | 取消运行或转换。 |

## 异常

| 异常 | 条件 |
|---|---|
| `AgentMediaException` | 负载无法变得可接受；`Error` 指明原因。 |

## 示例

```csharp
using VeloxDev.AI;

var image = await AgentMedia.FromFileAsync("preview/frame.png");
var note = await AgentMedia.FromFileAsync("audio/note.mp3");
var options = AgentMediaOptions.CreateVisionDefault();

await foreach (var update in agent.RunStreamingWithMediaAsync(
    "Check the frame and the voice note.", new[] { image, note }, options, session))
{
    // each payload travels as its own image_url / input_audio / file block
}
```

不接受某媒体种类的模型会拒绝该部分，因此对这类端点保留纯文本回退。

## 相关

- [AgentMedia 与消息构建](../00_媒体负载/index.md) —— 手工构建消息。
- [限制与转码](../01_媒体限制/index.md) —— `options` 参数。
