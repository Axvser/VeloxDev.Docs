# 工作流系统 — API 参考

`workflow-system` 功能的公开 API，按命名空间分组展开。页面中出现的每个类型、成员与签名均已对照真实源码核实，并标注源码路径；仅能由源码推断（而非 Demo/Test 证据）的行为标注 *推断所得*。

本功能 API 分为六个栏目：

- [命名空间：VeloxDev.WorkflowSystem](00_workflowsystem/index.md) —— 构建器属性（源生成器）、核心组件接口（Tree/Node/Slot/Link/Helper）、上下文契约（IContext 体系）、值类型与枚举、默认 ViewModel 与 Helper、选择器系统、空间系统与渲染就绪辅助。
- [命名空间：VeloxDev.WorkflowSystem.StandardEx](01_standardex/index.md) —— 生成命令调用的标准行为静态扩展（树 / 节点 / 槽 / 连接 / 命令生命周期）。
- [命名空间：VeloxDev.Core.WorkflowSystem.CompilerEx](02_compilerex/index.md) —— 编译入口 `CompilerViewModel.CompileAsync`（`CompileRole.Root/Terminal`）、编译模型（`ChainSegment` / `BranchSegment` / `ParallelSegment`）、编译期契约与运行时引擎 `RuntimeEngine`。
- [命名空间：VeloxDev.MVVM.Serialization](03_MVVM序列化/index.md) —— `ComponentModelEx` 工作流树 JSON 序列化。
- [关键成员契约](04_关键成员契约/index.md) —— 顶层 API 的条目模板形式（签名 / 参数 / 返回值 / 异常 / 示例）。
- [执行机制](05_执行机制/index.md) —— 唯一入口 `ReceiveAsync` 与两条执行路径（引擎驱动的编译运行 / 节点驱动的广播链）的数据流指南。

引擎类型命名空间一律为 `VeloxDev.Core.WorkflowSystem.CompilerEx`；核心接口（`IContext` 及其派生、各组件接口）位于 `VeloxDev.WorkflowSystem`。
