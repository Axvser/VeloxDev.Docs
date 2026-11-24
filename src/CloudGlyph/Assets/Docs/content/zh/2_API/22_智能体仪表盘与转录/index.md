# 智能体仪表盘与转录

让模型驱动工作流的宿主必须让人看见发生了什么。本模块提供两半：

- **`AgentTranscript`**——按顺序记录每一轮、它的回答、模型的思考与每次工具调用，由管线维护而不是宿主自己拼。
- **`AgentDashboardViewModel`**——一个 scope 的可绑定投影：工具、技能、MCP 服务器与子代理，每个成员带一个开关。

它还提供把图片、音频、视频、文档与文本附到用户消息的**媒体**通道。

## 命名空间

| 命名空间 | 类型 |
|---|---|
| `VeloxDev.AI.Pipelines` | `AgentTranscript`、`AgentTranscriptEntry`、`AgentTranscriptRole`、`AgentMarkdownOptions`、`AgentEvent` 家族、`AgentPipeline`、`AgentPipelineAgent`、`IAgentPipelineStage`、`DelegateAgentPipelineStage`、`TextPipeline`、`ToolPipeline` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`、`AgentMemberViewModel`、`ToolMemberViewModel`、`SkillMemberViewModel`、`McpServerMemberViewModel`、`McpToolMemberViewModel` |
| `VeloxDev.AI` | `AgentMedia`、`AgentAttachment`、`AgentMediaReference`、`AgentMessage`、`AgentMediaOptions`、`IAgentMediaContent`、`IAgentMediaTranscoder`、`AgentMediaAgentExtensions` |

## 页面

- [转录](00_转录/index.md) —— 对话记录及其 Markdown 与 JSON 形式。
- [事件管线](01_事件管线/index.md) —— 事件词汇、阶段链与内置阶段。
- [仪表盘](02_仪表盘/index.md) —— 逐 scope 的面板及其成员行。
- [媒体](03_媒体/index.md) —— 经校验的多模态输入与宿主转码接缝。

## 证据说明

转录由 demo 聊天面板与 `TranscriptWiringTests` 覆盖。仪表盘层（`Agent/Dashboard/`）由 `AgentDashboardViewModelTests` 覆盖，但**没有任何 demo 绑定它**——demo 直接绑定 `McpScope.Status`。请把仪表盘当作经过测试的投影，而不是已发布的 UI。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 仪表盘投影的 scope。
- [MCP 集成](../20_MCP集成/index.md) —— demo 实际绑定的状态视图模型。
