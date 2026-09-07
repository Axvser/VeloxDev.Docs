# 设计模式 — 工作流系统

对 workflow-system 功能（编辑器 VM 层 + CompilerEx 编译/运行引擎）所作的设计模式分析。每页用 Mermaid `classDiagram` 或表格说明模式，并给出带源码路径与行范围的代码摘录。编译产物（`CompiledGraph`）是不可变描述，真正的执行由 `RuntimeEngine` 在运行期驱动——见[数据流分析](../../03_数据流分析/00_工作流系统/index.md)。

| 页面 | 内容 |
|---|---|
| [类图](00_class-diagram/index.md) | Mermaid 类图——核心/执行模型（CompilerEx）与组件 VM 模型 |
| [模式总览](01_patterns-overview/index.md) | 模式 → 位置对照表 |
| [模板方法](02_模板方法/index.md) | Helper 生命周期骨架（`Install`/`Uninstall`/`CloseAsync`）+ 可覆写钩子 |
| [命令模式](03_命令模式/index.md) | `WorkflowActionPair` 撤销/重做命令栈 |
| [观察者模式](04_观察者模式/index.md) | Helper 集合事件 + `PropertyChanged` 观察 |
| [策略模式](05_策略模式/index.md) | `ICompileTimeRouter` 的 Static/Dynamic 分支选择 |
| [代理 / 装饰器](06_代理-装饰器/index.md) | 源生成的 partial VM 转发给 Helper |
| [门面](07_门面/index.md) | `WorkflowBuilder` 属性类型 |
| [组合](08_组合/index.md) | 节点拥有槽位；连接以节点对形式派生 |
| [虚拟代理](09_虚拟代理/index.md) | `VisibleItems` 的空间虚拟化 |
| [策略（运行期）](10_策略-运行期/index.md) | `IRedirectable` 朝向更早编译状态整图重跑 |
