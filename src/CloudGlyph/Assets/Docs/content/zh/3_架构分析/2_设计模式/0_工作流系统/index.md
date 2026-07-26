# 设计模式 — 工作流系统

## 1. 构建器模式（源生成器）

`[WorkflowBuilder.Tree<T>]`、`[WorkflowBuilder.Node<T>]`、`[WorkflowBuilder.Slot<T>]` 和 `[WorkflowBuilder.Link<T>]` 属性由 Roslyn 源生成器（`VeloxDev.Core.Generator`）处理，生成完整的 ViewModel 实现。

```csharp
// 用户编写：
[WorkflowBuilder.Tree<MyTreeHelper>]
public partial class MyTree { }

// 生成器生成：
//   - 实现 IWorkflowTreeViewModel
//   - InitializeWorkflow() 方法
//   - 所有必需属性（Nodes, Links, Layout...）
//   - 所有必需命令
//   - 序列化支持
//   - Agent 上下文元数据
```

**原因**: 大幅减少样板代码。用户只需编写特定于结构的逻辑（Helper）。重复的属性+命令模式由分析器一次性生成。

## 2. 策略模式（Helper 系统）

每个组件类型将其行为委托给 **Helper** 对象：

```
组件             Helper
─────────       ──────
TreeViewModel  → TreeHelper<T>      : CreateLink, CreateNode, ValidateConnection
NodeViewModel  → NodeHelper<T>      : WorkAsync, ValidateBroadcastAsync
SlotViewModel  → SlotHelper<T>      : ValidateConnection
LinkViewModel  → LinkHelper<T>      : （仅生命周期）
```

Helper 是一个可插拔的策略，可以在运行时通过 `SetHelper()` 替换。这将 ViewModel 的结构代码（位置、集合）与其行为代码（业务逻辑、验证）分离。

## 3. 中介者模式（基于命令的通信）

组件不直接调用彼此的方法。而是通过共享的命令接口（`IVeloxCommand`）进行通信：

```
Node.MoveCommand.Execute(offset)    → Helper 处理空间更新
Tree.SendConnectionCommand.Execute(slot) → Helper 管理连接协议
Slot.DeleteCommand.Execute(null)    → Helper 移除连接并通知 Tree
```

这解耦了发送者和接收者。命令可以通过 `SubmitCommand`/`UndoCommand` 机制被拦截、排队、记录或撤销。

## 4. 命令模式（撤销/重做）

每个变更操作都包装在 `IWorkflowActionPair` 中：

```
用户操作 → SubmitCommand(pair) → pair.Do()  → 记录到撤销栈
用户撤销 → UndoCommand(null)   → pair.Undo() → 移动到重做栈
用户重做 → RedoCommand(null)   → pair.Do()  → 移回撤销栈
```

**栈结构**: Tree 维护一个撤销栈和一个重做栈。操作可以批处理以实现复合操作的原子撤销/重做。

## 5. 观察者模式（事件驱动生命周期）

Helper 订阅组件事件：

```
TreeHelper.NodeAdded    → 空间管理器索引该节点
TreeHelper.LinkAdded    → 空间管理器索引连接线对
NodeHelper.WorkCommand  → Started / Completed / Failed / Exited 事件
```

`HttpHelper<T>` 示例订阅 `WorkCommand.Started`、`.Exited`、`.Enqueued`、`.Dequeued` 来跟踪运行时计数器并显示 UI 状态。

## 6. 虚拟代理模式（ViewPool + 虚拟化）

`ViewPool` 附加行为充当虚拟代理。仅当前 `Viewport` 内的项目被渲染：

```
IWorkflowTreeViewModelHelper.Viewport  → 定义可见区域
IWorkflowTreeViewModelHelper.VisibleItems → 计算的可见子集
ViewPool.ItemsSource = {Binding Helper.VisibleItems}  → 仅渲染这些
```

当用户平移/缩放时，视口变化 → `VisibleItems` 重新计算 → UI 回收离屏项目的视图。

## 7. 空间哈希模式（基于网格的索引）

`SpatialGridHashMap<T>` 使用基于网格的空间哈希实现 O(1) 的插入/移除和高效范围查询：

```
网格单元 [x, y] → 该单元中的项目哈希集
插入: 计算单元键 → 添加到哈希集 (O(1))
查询: 枚举视口中的单元 → 收集项目 (O(视口中单元数))
移除: 计算单元键 → 从哈希集移除 (O(1))
```

网格单元大小可配置。较大的单元大小减少内存但增加查询中的误报。

## 8. 层级/锚点模式（Z 索引管理）

每个节点都有一个带有 `Layer`（Z 索引）的 `Anchor`。当节点重叠时，层级决定哪个节点显示在前面。层级在创建时自动管理，并可在节点移动时调整。
