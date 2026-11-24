# 智能体仪表盘与转录

让模型驱动工作流的宿主必须让人看见发生了什么。本模块提供两半：

- **`AgentTranscript`**——按顺序记录每一轮、它的回答、模型的思考与每次工具调用，由管线维护而不是宿主自己拼。
- **`AgentDashboardViewModel`**——一个 scope 的可绑定投影：工具、技能、MCP 服务器与子代理，每个成员带一个开关。

它还提供把图片、音频、视频、文档与文本附到用户消息的**媒体**通道。

## 你会构建什么

- 由管线填充、可导出为 Markdown 与 JSON 的 `AgentTranscript`；
- 覆盖一个 scope、汇报各子系统摘要的 `AgentDashboardViewModel`；
- 一条经过校验的媒体消息，交给支持它的模型。

## 页面

- [安装准备](00_安装准备/index.md) —— 前置条件、包、转录与仪表盘对象。
- [使用](01_使用/index.md) —— 转录 API、事件管线、仪表盘行、媒体、验证与完整程序。

## 证据说明

转录由 demo 聊天面板与 `TranscriptWiringTests` 覆盖。仪表盘层（`Agent/Dashboard/`）由 `AgentDashboardViewModelTests` 覆盖，但**没有任何 demo 绑定它**——demo 直接绑定 `McpScope.Status`。请把仪表盘当作经过测试的投影，而不是已发布的 UI。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 仪表盘投影的 scope。
- [MCP 集成](../20_MCP集成/index.md) —— demo 实际绑定的状态视图模型。
