# 10 · 技能与管线

两个与 MCP、子代理并列的子系统：

- **技能**（`VeloxDev.AI.Skills`）—— 一个 Agent Skills 库，模型可以发现、加载、关闭并从其中读取资源。`scope.WithSkills(...)` 挂载它；四个技能工具与技能语料每轮到达。
- **管线**（`VeloxDev.AI.Pipelines`）—— 每次 agent 运行都会经过的可观测链。`scope.Pipeline` 已替你组合好并输入 `AgentTranscript`；`scope.WithTranscript(...)` 挂载对话。

## 子页面

- [技能](00_技能/index.md) —— `SkillScope`、`SkillAgentToolkit`、内嵌 vs 文件技能、描述符/状态模型、四个工具。
- [管线](01_管线/index.md) —— `AgentPipeline`、`AgentEvent` 层级、`ToolPipeline`、`AgentTranscript` 以及连接它们的重载。

**预期结果：** 两者都挂载后，当轮工具列表携带四个技能工具，每次调用都以 `ToolCall` 条目落进对话记录。
