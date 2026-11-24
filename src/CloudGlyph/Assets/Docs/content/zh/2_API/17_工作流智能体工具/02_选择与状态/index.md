# 选择与状态

两个小型服务在不增加工具的前提下支持智能体：选择扩展把每轮提示收窄到用户选中的节点，`WorkflowStateTracker` 让模型读取差异而不是重新读取整张图。

## 类：WorkflowAgentSelectionExtensions

`VeloxDev.AI.Workflow.WorkflowAgentSelectionExtensions` 是扩展方法的静态类。选择是提示上下文，不是工具：它只改变每轮说明中列出选中节点的部分，从不改变工具集或树。

选择是身份快照（稳定运行时 id 加类型名）。几何、槽与属性刻意不捕获；模型通过普通查询工具读取它们，因此提示不会携带过期位置。被删除、被重挂或从树中移除的节点会立即从选择中消失。

| 方法 | 返回 | 说明 |
|---|---|---|
| `SelectForAgent(this INodeComponent node)` | `bool` | 把一个节点加入其树的选择。新加入时为 `true`。 |
| `SelectForAgent(this IReadOnlyCollection<INodeComponent> nodes)` | `int` | 把多个节点并入各自树的选择。返回新加入数量，无变化为 `0`，内部错误为 `-1`。 |
| `DeselectForAgent(this INodeComponent node)` | `bool` | 从一个节点的选择中移除它。 |
| `DeselectForAgent(this IReadOnlyCollection<INodeComponent> nodes)` | `int` | 移除多个节点；返回实际移除数量。 |
| `ClearAgentSelection(this ITreeComponent tree)` | `int` | 清空树的选择并返回释放数量。 |
| `GetAgentSelection(this ITreeComponent tree)` | `IReadOnlyList<INodeComponent>` | 当前选择的副本，按选择顺序。 |

操作是集合式的：重复选择已选节点是无操作，集合调用只报告真正改变的部分。要替换整个选择，先调用 `ClearAgentSelection` 再加入新集合。没有异常逃逸；为空、未挂载或缺少 id 的节点被跳过。

提示最多列出 64 个身份；报告的数量始终是完整选择量。这避免一次全选把每轮提示撑大，同时仍告诉模型工作集有多大。

```csharp
using VeloxDev.AI.Workflow;

node.SelectForAgent();                 // 加入一个节点
selectedNodes.SelectForAgent();        // 并集；返回新加入数量
tree.ClearAgentSelection();            // 释放全部
var current = tree.GetAgentSelection();
```

## 类：WorkflowStateTracker

`VeloxDev.AI.Workflow.WorkflowStateTracker` 捕获轻量快照并计算差异，使智能体以最小上下文跟踪变化。工作流 toolkit 为每个作用域持有一个实例，位于 `TakeSnapshot` 与 `GetChangesSinceSnapshot` 之后。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `WorkflowStateTracker(ITreeComponent tree)` | 把跟踪器绑定到一棵树。 |
| `Version` | `long` | 单调递增的快照版本号。 |
| `TakeSnapshot` | `string TakeSnapshot()` | 记录当前树状态并以 JSON 返回。 |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | 返回新增、移除、修改的节点与连线的 JSON 差异。没有上一快照时返回完整当前状态。 |

跟踪器是普通类，不触发变更通知。`State` 工具分类把它以 `TakeSnapshot` 与 `GetChangesSinceSnapshot` 暴露给模型。

## 相关

- [WorkflowAgentToolkit](../01_工作流工具集/index.md) —— 由这些服务支撑的工具。
- [WorkflowAgentScope](../00_工作流作用域/index.md) —— `CreateToolkit` 持有作用域的跟踪器。
