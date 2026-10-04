# 10 · 技能与管线

两个位于 MCP 与子代理之旁的子系统：

- **技能**（`VeloxDev.AI.Skills`）—— 一个模型可发现、加载、关闭并读取其资源的 Agent Skills 库。`scope.WithSkills(...)` 挂载它；四个技能工具与技能语料每轮到达。
- **管线**（`VeloxDev.AI.Pipelines`）—— 每次 agent 运行都会流经的可观测链。`scope.Pipeline` 由作用域替你组合并喂给 `AgentTranscript`；`scope.WithTranscript(...)` 挂载对话记录。

## 子页面

- [技能](00_技能/index.md) —— `SkillScope`、`SkillAgentToolkit`、内嵌 vs 文件技能、描述符/状态模型、四个工具。
- [管线](01_管线/index.md) —— `AgentPipeline`、`AgentEvent` 层级、`ToolPipeline`、`AgentTranscript` 及其接线重载。

**预期结果：** 两者都挂载后，该轮的工具列表携带四个技能工具，且每次调用都以 `ToolCall` 条目落入对话记录。
