# 设计模式 — 工作流系统

工作流系统特性（编辑器 ViewModel 层 + CompilerEx 编译/运行引擎）的设计模式分析。以下页面逐一分析该特性采用的模式，配 Mermaid 类图与来自当前仓库的代码摘录。

| 页面 | 内容 |
|---|---|
| [类图](00_类图/index.md) | Mermaid 类图（由三页组成的总览） |
| [模式总览](01_模式总览/index.md) | 模式 → 位置对照表 |
| [模板方法](02_模板方法/index.md) | Helper 生命周期骨架（`Install`/`Uninstall`/`CloseAsync`）+ 可重写钩子 |
| [命令模式](03_命令模式/index.md) | `WorkflowActionPair` 撤销/重做命令栈 |
| [观察者模式](04_观察者模式/index.md) | Helper 集合事件、`PropertyChanged` 观察与 `IExecutionObserver` |
| [策略模式](05_策略模式/index.md) | `ICompileTimeRouter` 的 Static/Dynamic 分支选择 |
| [代理 / 装饰器](06_代理与装饰器/index.md) | 源生成 partial VM 转发给 Helper |
| [外观模式](07_外观模式/index.md) | `WorkflowBuilder` 特性类型 |
| [组合](08_组合/index.md) | 节点拥有槽；连线派生为节点对 |
| [虚拟代理](09_虚拟代理/index.md) | `VisibleItems` 的空间虚拟化 |
| [策略（运行时）](10_运行时策略/index.md) | `IRedirectable` 向前驱 Order 重跑整图 |
| [策略族（宿主能力）](11_宿主能力/index.md) | 作为策略族的宿主接缝，每项默认都是空对象 |
| [备忘录（检查点）](12_检查点备忘录/index.md) | `ExecutionCheckpoint` 作为备忘录：快照边界、`Rekey` 守卫、恢复拒绝 |
| [连接预览](13_连接预览/index.md) | 拖拽预览作为规则链 + 一个宿主策略钩子：与完成共用同一套检查，只收紧不放松 |

`00_类图` 内的三张图分别位于[类图：核心 / 执行模型](00_类图/00_核心模型/index.md)、[组件模型](00_类图/01_组件模型/index.md)与[运行时能力层的类图](00_类图/02_运行时能力/index.md)。
