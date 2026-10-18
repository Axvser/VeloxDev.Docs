# API 参考

每个 VeloxDev 功能的完整 API 目录，按功能与命名空间分组。每个成员条目记录精确签名、参数、返回值、异常、可追溯到真实源文件（Demo / Test / 源码）的示例以及备注。

| 功能 | 覆盖的命名空间 |
|---|---|
| [工作流系统](00_工作流系统) | `VeloxDev.WorkflowSystem`、`.StandardEx`、`VeloxDev.Core.WorkflowSystem.CompilerEx` |
| [工作流代理](01_工作流代理) | `VeloxDev.AI`、`VeloxDev.AI.Workflow`、`VeloxDev.AI.Workflow.Functions`、`VeloxDev.AI.MCP` |
| [MVVM](02_MVVM) | `VeloxDev.MVVM`、`VeloxDev.Generators` |
| [过渡动画](03_过渡动画) | `VeloxDev.TransitionSystem`、`.Abstractions`、`.NativeSamplers`、`VeloxDev.TimeLine` |
| [动态主题](04_动态主题) | `VeloxDev.DynamicTheme`、`VeloxDev.TransitionSystem` |
| [AOP](05_AOP) | `VeloxDev.AspectOriented` |
| [Tickable](06_Tickable) | `VeloxDev.TimeLine` |
| [弱引用类型](07_弱引用类型) | `VeloxDev.WeakTypes` |
| [平台适配器](08_平台适配器) | `VeloxDev.WorkflowSystem.AttachedBehaviors`、各适配器 `VeloxDev.*` |
| [序列化](09_序列化) | `VeloxDev.Serialization`（归档引擎在 `VeloxDev.Core`；`CompiledGraphEx` / `CheckpointEx` 在 `VeloxDev.Core.Extension`） |
