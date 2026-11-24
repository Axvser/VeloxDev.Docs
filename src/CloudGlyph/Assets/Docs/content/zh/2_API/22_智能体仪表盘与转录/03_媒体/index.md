# 媒体

多模态输入属于**用户消息**，不属于工具结果。在 OpenAI 兼容的 chat completions 中，工具消息只有文本通道，因此工具返回的媒体会变成 base64 JSON 字符串，而不是像素或声音。本层按实际字节校验媒体，然后构建用户消息。

## 页面

- [AgentMedia 与消息构建](00_媒体负载/index.md) —— 经校验的负载、附件记录、URL 引用与消息构建器。
- [限制与转码](01_媒体限制/index.md) —— 接受的种类与类型、大小与尺寸限制，以及宿主编解码接缝。
- [带媒体运行](02_媒体运行/index.md) —— 经校验的 `RunWithMediaAsync` / `RunStreamingWithMediaAsync` 扩展。

## 类型地图

| 类型 | 角色 |
|---|---|
| `AgentMedia` | 由字节校验的负载。 |
| `AgentAttachment` | 转录携带的显示记录（名称、类型、大小）。 |
| `AgentMediaReference` | provider 可获取的远程 HTTP(S) 负载。 |
| `AgentMessage` | 构建用户 `ChatMessage`。 |
| `AgentMediaOptions` | 限制与转码策略。 |
| `IAgentMediaTranscoder` / `DelegateAgentMediaTranscoder` | 宿主编解码接缝。 |
| `AgentMediaAgentExtensions` | 先校验再运行的辅助方法。 |

## 相关

- [转录](../00_转录/index.md) —— 附件显示处。
- [事件管线](../01_事件管线/index.md) —— `AgentTurnStarted` 与 `AgentMediaReceived` 携带它们。
