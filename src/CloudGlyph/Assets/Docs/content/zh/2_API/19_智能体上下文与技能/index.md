# 智能体上下文与技能

编辑工作流的智能体需要两类知识：框架是什么，以及怎样完成一件多步骤的活。VeloxDev 把第一类作为**上下文块**从编译的智能体上下文树渲染，把第二类作为**技能**——随包嵌入或从磁盘发现的开关文档。

上下文分层渲染，让提示保持稳定。技能只在模型需要时加载，要么完整注入（嵌入型），要么按名通告、按需取正文（文件型）。

## 命名空间

| 命名空间 | 类型 |
|---|---|
| `VeloxDev.AI` | `AgentContextAttribute`、`AgentLanguages`、`AgentLanguagesExtensions`、`AgentEmbeddedResources` |
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope` 的上下文成员、`AgentContextCollector` |
| `VeloxDev.AI.Skills` | `SkillScope`、`SkillStatusViewModel`、`SkillsViewModel`、`SkillSummary`、`SkillDescriptor`、`SkillState`、`SkillSourceKind`、`ISkillSource`、`EmbeddedSkillSource`、`FileSkillSource`、`SkillAgentToolkit`、`SkillAgentContextProvider` |

## 页面

- [上下文作用域](00_上下文作用域/index.md) —— 提示语言、类型注册、提示形状与上下文收集器。
- [技能作用域](01_技能作用域/index.md) —— 发现、开关、渲染与挂载。
- [技能状态](02_技能状态/index.md) —— 可绑定技能行与线程安全摘要。
- [技能来源](03_技能来源/index.md) —— 嵌入与磁盘来源、`SKILL.md` frontmatter。
- [技能工具](04_技能工具/index.md) —— 四个面向模型的技能工具、其 provider 与嵌入资源读取。

## 提示分层

| 来源 | 携带 | 何时变化 |
|---|---|---|
| 静态骨架 | 行为约束、参考文档、类型目录 | 构造后从不 |
| 能力包络 | 闸门、被关掉的工具、预算、漂移 | 每次配置变更 |
| 技能 | 每篇文档一个流程，外加随附资源 | 每次开关技能 |
| MCP | 服务器清单与工具 | 每次装载服务器 |

骨架只渲染一次；另外三者每轮贡献。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 上下文所描述的工具。
- [MCP 集成](../20_MCP集成/index.md) —— 每轮的第四个来源。
